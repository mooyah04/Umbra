"""Background player-refresh scheduler.

Runs in a daemon thread started from the FastAPI lifespan. Every
`scheduler_interval_seconds`, wakes up, picks the N stalest players
(by `last_ingested_at`), and re-ingests each via `ingest_player`.

Ingests are dispatched to a thread pool so the wall-clock time per
sweep is roughly max(per-player-ingest-duration) instead of the sum.
Each worker opens its own Session — SQLAlchemy Sessions aren't
thread-safe, so sharing would be a bug. Exceptions are logged and
swallowed so one bad player can't kill the sweep.
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    last_ingested_at is older than the cutoff.

    Order:
      1. `discovered_keystone_level` DESC, nulls last — prefer high-tier
         leaderboard stubs over the long tail when WCL budget is tight.
      2. `last_ingested_at` ASC, nulls first — among peers at the same
         tier, serve never-ingested stubs before re-sweeps, and the
         stalest re-sweeps before fresher ones.

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
            .order_by(
                Player.discovered_keystone_level.desc().nullslast(),
                Player.last_ingested_at.asc().nullsfirst(),
            )
            .limit(limit)
        )
        if region_whitelist:
            stmt = stmt.where(Player.region.in_(region_whitelist))
        return [(n, r, rg) for n, r, rg in session.execute(stmt)]


def _ingest_one(name: str, realm: str, region: str) -> None:
    """Re-ingest a single player in a fresh Session. Runs inside a worker
    thread so multiple players ingest concurrently during a sweep."""
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


def _sweep_once() -> None:
    players = _pick_stale_players(
        limit=settings.scheduler_batch_size,
        stale_after_seconds=settings.scheduler_stale_after_seconds,
    )
    if not players:
        logger.debug("scheduler: nothing stale to refresh")
        return
    workers = max(1, settings.scheduler_workers)
    start = time.monotonic()
    logger.info(
        "scheduler: refreshing %d stale player(s) across %d workers",
        len(players), workers,
    )
    with ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="umbra-ingest"
    ) as pool:
        futures = [
            pool.submit(_ingest_one, name, realm, region)
            for name, realm, region in players
        ]
        # Drain futures so the sweep doesn't return before all ingests
        # complete — the next tick should see the new last_ingested_at
        # timestamps and pick different stale rows.
        for f in as_completed(futures):
            # Exceptions are swallowed inside _ingest_one, but pool can
            # still raise on thread-pool-level errors. Log + continue.
            try:
                f.result()
            except Exception as e:
                logger.exception("scheduler: worker raised: %s", e)
    elapsed = time.monotonic() - start
    logger.info(
        "scheduler: sweep complete — %d players in %.1fs (%.1fs/player avg)",
        len(players), elapsed, elapsed / max(1, len(players)),
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
