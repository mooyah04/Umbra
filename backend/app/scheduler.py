"""Background player-refresh scheduler.

Runs in a daemon thread started from the FastAPI lifespan. Every
`scheduler_interval_seconds`, wakes up, picks the N stalest players
(by `last_ingested_at`), and re-ingests each via `ingest_player`.

Threaded (not asyncio) to match the app's sync SQLAlchemy Session model.
Each sweep uses its own Session scope — we never hold a session across
iterations. Exceptions are logged and swallowed so one bad player can't
kill the scheduler loop.
"""
import logging
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import or_, select

from app.config import settings
from app.db import SessionLocal
from app.models import Player
from app.pipeline.ingest import ingest_player

logger = logging.getLogger(__name__)


_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _region_filter_list() -> list[str]:
    """Parse SCHEDULER_REGION_FILTER into an uppercase list. Empty = no filter."""
    raw = settings.scheduler_region_filter or ""
    return [r.strip().upper() for r in raw.split(",") if r.strip()]


def _pick_stale_players(limit: int, stale_after_seconds: int) -> list[tuple[str, str, str]]:
    """Return up to `limit` (name, realm, region) tuples for players whose
    last_ingested_at is older than the cutoff, oldest first. NULL counts
    as 'never ingested' and sorts to the top.

    If `SCHEDULER_REGION_FILTER` is set, only players in those regions are
    eligible — useful for prioritizing a single region (EU for internal
    testing) while leaving non-matching stubs in the queue for later.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=stale_after_seconds)
    region_whitelist = _region_filter_list()
    with SessionLocal() as session:
        stmt = (
            select(Player.name, Player.realm, Player.region)
            .where(
                or_(
                    Player.last_ingested_at.is_(None),
                    Player.last_ingested_at < cutoff,
                )
            )
            .order_by(Player.last_ingested_at.asc().nullsfirst())
            .limit(limit)
        )
        if region_whitelist:
            stmt = stmt.where(Player.region.in_(region_whitelist))
        return [(n, r, rg) for n, r, rg in session.execute(stmt)]


def _sweep_once() -> None:
    players = _pick_stale_players(
        limit=settings.scheduler_batch_size,
        stale_after_seconds=settings.scheduler_stale_after_seconds,
    )
    if not players:
        logger.debug("scheduler: nothing stale to refresh")
        return
    logger.info("scheduler: refreshing %d stale player(s)", len(players))
    for name, realm, region in players:
        try:
            with SessionLocal() as session:
                result = ingest_player(session, name, realm, region)
                logger.info(
                    "scheduler: refreshed %s-%s-%s (runs=%d, reason=%s)",
                    name, realm, region,
                    len(result.player.runs) if result.player else 0,
                    result.reason,
                )
        except Exception as e:
            logger.warning(
                "scheduler: ingest failed for %s-%s-%s: %s",
                name, realm, region, e,
            )


def _loop() -> None:
    interval = max(60, settings.scheduler_interval_seconds)
    logger.info(
        "scheduler: started (interval=%ds batch=%d stale_after=%ds)",
        interval, settings.scheduler_batch_size,
        settings.scheduler_stale_after_seconds,
    )
    while not _stop_event.is_set():
        try:
            _sweep_once()
        except Exception as e:
            logger.exception("scheduler: sweep crashed: %s", e)
        # Wait with early-wake so shutdown is responsive.
        _stop_event.wait(interval)
    logger.info("scheduler: stopped")


def start() -> None:
    global _thread
    if not settings.scheduler_enabled:
        logger.info("scheduler: disabled via settings")
        return
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_loop, name="umbra-scheduler", daemon=True)
    _thread.start()


def stop() -> None:
    _stop_event.set()
