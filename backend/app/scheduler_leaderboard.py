"""Leaderboard-discovery scheduler — round-robins through regions and
connected-realm chunks, upserting stub Player rows for anyone we
haven't seen yet.

Runs in its own daemon thread (separate from the WCL re-sweep in
`app/scheduler.py`) so Blizzard API calls and DB writes can't block
the WCL pipeline. Exceptions are logged and swallowed so one bad tick
can't kill the loop.

State is purely in-memory: region cursor + per-region realm cursor.
On restart we just start over — connected-realm lists are deterministic
and one full pass is only ~23 hours with defaults, so losing state
amounts to at most one extra day of overlap.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from app.bnet.client import bnet_client
from app.config import settings
from app.db import SessionLocal
from app.discovery import (
    discover_from_realm,
    match_active_dungeons,
    upsert_stub_players,
)

logger = logging.getLogger(__name__)


_thread: threading.Thread | None = None
_stop_event = threading.Event()

# In-memory cursor state. Per-region realm index + last-tick metadata so
# the /leaderboard-status endpoint can show progress.
_state: dict = {
    "region_cursor": 0,
    "realm_cursors": {},  # region -> realm index into full realm list
    "last_tick_at": None,
    "last_region_scanned": None,
    "last_realms_scanned": [],
    "last_new_players": 0,
    "last_unknown_specs": [],
    "total_ticks": 0,
    "total_new_players": 0,
}


def _regions() -> list[str]:
    return [r.strip().upper() for r in settings.leaderboard_regions.split(",") if r.strip()]


def _next_region() -> str:
    regions = _regions()
    if not regions:
        return "EU"
    region = regions[_state["region_cursor"] % len(regions)]
    _state["region_cursor"] = (_state["region_cursor"] + 1) % len(regions)
    return region


def _next_realm_chunk(region: str, all_realms: list[int]) -> list[int]:
    """Return the next N realms for this region, wrapping around when
    we hit the end of the list. N defaults to leaderboard_realms_per_tick."""
    n = max(1, settings.leaderboard_realms_per_tick)
    start = _state["realm_cursors"].get(region, 0) % max(1, len(all_realms))
    if len(all_realms) <= n:
        _state["realm_cursors"][region] = 0
        return list(all_realms)
    end = start + n
    if end <= len(all_realms):
        chunk = all_realms[start:end]
        _state["realm_cursors"][region] = end % len(all_realms)
    else:
        # Wrap around
        chunk = all_realms[start:] + all_realms[: end - len(all_realms)]
        _state["realm_cursors"][region] = end - len(all_realms)
    return chunk


def _tick_once() -> None:
    region = _next_region()
    _state["last_region_scanned"] = region

    dungeons = match_active_dungeons(region)
    if not dungeons:
        logger.warning("leaderboard: no dungeon matches for region=%s", region)
        _state["last_tick_at"] = datetime.utcnow()
        return

    period_id = bnet_client.get_current_mythic_period(region)
    if not period_id:
        logger.warning("leaderboard: no mythic period for region=%s", region)
        _state["last_tick_at"] = datetime.utcnow()
        return

    all_realms = bnet_client.get_connected_realms_index(region)
    if not all_realms:
        logger.warning("leaderboard: no connected realms for region=%s", region)
        _state["last_tick_at"] = datetime.utcnow()
        return

    chunk = _next_realm_chunk(region, all_realms)
    _state["last_realms_scanned"] = chunk

    tick_new = 0
    tick_unknown: set[int] = set()
    for realm_id in chunk:
        try:
            players, unknowns = discover_from_realm(region, realm_id, period_id, dungeons)
            tick_unknown |= unknowns
        except Exception as e:
            logger.warning("leaderboard: discovery failed region=%s realm=%d: %s",
                           region, realm_id, e)
            continue
        if not players:
            continue
        try:
            with SessionLocal() as session:
                new_count = upsert_stub_players(session, players)
        except Exception as e:
            logger.warning("leaderboard: upsert failed region=%s realm=%d: %s",
                           region, realm_id, e)
            continue
        tick_new += new_count

    _state["last_tick_at"] = datetime.utcnow()
    _state["last_new_players"] = tick_new
    _state["last_unknown_specs"] = sorted(tick_unknown)
    _state["total_ticks"] += 1
    _state["total_new_players"] += tick_new
    logger.info(
        "leaderboard tick: region=%s realms=%d new_players=%d unknown_specs=%s",
        region, len(chunk), tick_new, sorted(tick_unknown),
    )


def _loop() -> None:
    interval = max(300, settings.leaderboard_interval_seconds)
    logger.info(
        "leaderboard scheduler: started (interval=%ds realms_per_tick=%d regions=%s)",
        interval, settings.leaderboard_realms_per_tick,
        settings.leaderboard_regions,
    )
    while not _stop_event.is_set():
        try:
            _tick_once()
        except Exception as e:
            logger.exception("leaderboard scheduler: tick crashed: %s", e)
        _stop_event.wait(interval)
    logger.info("leaderboard scheduler: stopped")


def start() -> None:
    global _thread
    if not settings.leaderboard_enabled:
        logger.info("leaderboard scheduler: disabled via settings")
        return
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_loop, name="umbra-leaderboard", daemon=True)
    _thread.start()


def stop() -> None:
    _stop_event.set()


def status() -> dict:
    """Snapshot of the current poller state for /admin/leaderboard-status."""
    return {
        "enabled": settings.leaderboard_enabled,
        "interval_seconds": settings.leaderboard_interval_seconds,
        "realms_per_tick": settings.leaderboard_realms_per_tick,
        "regions": _regions(),
        "thread_alive": bool(_thread and _thread.is_alive()),
        "region_cursor": _state["region_cursor"],
        "realm_cursors": dict(_state["realm_cursors"]),
        "last_tick_at": _state["last_tick_at"].isoformat() if _state["last_tick_at"] else None,
        "last_region_scanned": _state["last_region_scanned"],
        "last_realms_scanned": list(_state["last_realms_scanned"]),
        "last_new_players": _state["last_new_players"],
        "last_unknown_specs": list(_state["last_unknown_specs"]),
        "total_ticks": _state["total_ticks"],
        "total_new_players": _state["total_new_players"],
    }
