"""Compute Augmentation Evoker group-uplift damage for a single run.

Aug's value to a group is buffing 2-4 teammates with Ebon Might (damage
amp) and Prescience (crit chance) — contribution that WCL attributes
to the teammates' damage bars, not the Aug's. Without explicit credit
the scoring engine under-grades Augs who maintain excellent buff
uptime because their personal DPS ceiling is lower by design.

Algorithm:
  1. Fetch applybuff / refreshbuff / removebuff events sourced by the
     Aug for Ebon Might (395152) and Prescience (409311).
  2. Reconstruct per-(target, buff) active windows.
  3. For each buffed teammate, fetch their DamageDone events and sum
     damage whose timestamp falls inside any window on that teammate.
  4. Multiply each matched damage chunk by the buff's uplift factor
     (see UPLIFT_FACTORS). Sum across all teammates and both buffs.

Returns raw total uplift damage — caller converts to DPS by dividing
by fight duration, and applies scoring curves calibrated against the
observed distribution across real top-Aug logs.

Uplift factor estimates:
  - Ebon Might:  0.15 (~15% damage amp in Midnight S1)
  - Prescience:  0.08 (+20% crit ≈ 8% effective DPS for most specs)

These are approximations. A follow-up calibration pass against the
validate_aug_uplift.py sampler can refine them if the observed
uplift distribution differs meaningfully from expected.
"""
from __future__ import annotations

import logging

from app.wcl.client import wcl_client

logger = logging.getLogger(__name__)


# Ebon Might on teammates uses 395152; 395296 is the Aug's self-aura
# and does NOT fire on teammates. Prescience on teammates uses 410089
# in Midnight (409311 was the TWW ID — still present in masterData but
# never fires in live reports). Sourced 2026-04-21 from WCL report
# kz2ZJgMXFrQ7vh6L/10 (top Aug log, all target distributions verified).
EBON_MIGHT_ID = 395152
PRESCIENCE_ID = 410089

UPLIFT_FACTORS: dict[int, float] = {
    EBON_MIGHT_ID: 0.15,
    PRESCIENCE_ID: 0.08,
}

AUG_BUFF_IDS: frozenset[int] = frozenset(UPLIFT_FACTORS.keys())


def _reconstruct_windows(
    buff_events: list[dict], fight_end_ms: int
) -> dict[tuple[int, int], list[tuple[int, int]]]:
    """Given apply/refresh/remove events sourced by the Aug, return a
    map of (target_id, buff_id) -> list of [start_ms, end_ms] intervals.

    Multiple applications during the fight get separate intervals.
    Refresh events are ignored (they extend an already-active window,
    which is captured by the subsequent removebuff). A missing removebuff
    (fight ended with buff still up) is closed at fight_end_ms so we
    don't silently drop credit at fight end.
    """
    active: dict[tuple[int, int], int] = {}
    windows: dict[tuple[int, int], list[tuple[int, int]]] = {}

    # Process chronologically so apply/remove pairing is deterministic
    # even if WCL returns pages in a non-monotonic order.
    for ev in sorted(buff_events, key=lambda e: e.get("timestamp", 0)):
        buff_id = ev.get("abilityGameID")
        target = ev.get("targetID")
        t = ev.get("timestamp")
        etype = ev.get("type")
        if buff_id not in AUG_BUFF_IDS:
            continue
        if not isinstance(target, int) or not isinstance(t, (int, float)):
            continue
        key = (target, buff_id)
        if etype in ("applybuff",):
            # Only open a new window if none is active — refreshes inside
            # an open window don't split intervals.
            if key not in active:
                active[key] = int(t)
        elif etype in ("removebuff",):
            start = active.pop(key, None)
            if start is not None:
                windows.setdefault(key, []).append((start, int(t)))

    # Close any still-active windows at fight end.
    for key, start in active.items():
        windows.setdefault(key, []).append((start, fight_end_ms))

    return windows


def _in_any_window(t: int, intervals: list[tuple[int, int]]) -> bool:
    """Linear scan — intervals per (target, buff) are typically ≤10 per
    fight. A sorted-binary-search is over-engineered for this shape."""
    for start, end in intervals:
        if start <= t <= end:
            return True
    return False


def compute_uplift(
    report_code: str,
    fight_id: int,
    aug_source_id: int,
    fight_end_ms: int,
    teammate_source_ids: list[int],
) -> dict:
    """Fetch buff + damage events and return the uplift breakdown.

    Returns:
      {
        "total_uplift_damage": float  # weighted sum, all teammates
        "per_buff": {buff_id: float}
        "per_teammate": {teammate_id: float}
        "buff_uptime_ms": {buff_id: int}  # sum across all buffed teammates
      }

    teammate_source_ids is informational — the actual set of buffed
    targets comes from the buff events themselves, which also includes
    pets / guardians / temporary summons that received Ebon Might or
    Prescience. WCL attributes pet damage to the pet's own sourceID, so
    we have to credit their damage too to get the full uplift picture.
    """
    # 1. Fetch ALL buff events in the fight — unfiltered. WCL's
    # sourceID and targetID filters on Buffs dataType have non-obvious
    # semantics (they require source==target, silently dropping
    # cross-actor buffs). Filtering client-side for aug-sourced Aug
    # buffs is slower per-byte but correct. Pagination up to 5 pages
    # covers ~50k events — sufficient for an M+ fight.
    try:
        all_buff_events = wcl_client.get_player_events(
            report_code, [fight_id], data_type="Buffs"
        )
    except Exception as e:
        logger.warning(
            "aug_uplift: buff fetch failed for %s/%d: %s",
            report_code, fight_id, e,
        )
        return {"total_uplift_damage": 0.0, "per_buff": {}, "per_teammate": {}, "buff_uptime_ms": {}}

    buff_events = [
        ev for ev in all_buff_events
        if ev.get("sourceID") == aug_source_id
        and ev.get("abilityGameID") in AUG_BUFF_IDS
    ]

    windows = _reconstruct_windows(buff_events, fight_end_ms)
    if not windows:
        return {"total_uplift_damage": 0.0, "per_buff": {}, "per_teammate": {}, "buff_uptime_ms": {}}

    # Per-teammate aggregation of intervals per buff, for quick lookup.
    # intervals_by_teammate[target][buff_id] = [(start, end), ...]
    intervals_by_teammate: dict[int, dict[int, list[tuple[int, int]]]] = {}
    for (target, buff_id), ivals in windows.items():
        intervals_by_teammate.setdefault(target, {})[buff_id] = ivals

    # 2. For each buffed target (players + pets), fetch their damage
    # and intersect with the buff windows.
    per_buff: dict[int, float] = {}
    per_teammate: dict[int, float] = {}
    uptime_ms: dict[int, int] = {}

    # Pre-compute uptime totals (shared across both loops).
    for (target, buff_id), ivals in windows.items():
        dur = sum(max(0, end - start) for start, end in ivals)
        uptime_ms[buff_id] = uptime_ms.get(buff_id, 0) + dur

    # Use the full set of buffed targets from the buff events themselves
    # — captures pets and temporary summons, not just friendlyPlayers.
    buffed_teammates = list(intervals_by_teammate.keys())
    for teammate_id in buffed_teammates:
        try:
            dmg_events = wcl_client.get_player_events(
                report_code,
                [fight_id],
                data_type="DamageDone",
                source_id=teammate_id,
            )
        except Exception as e:
            logger.warning(
                "aug_uplift: damage fetch failed for %s/%d teammate=%d: %s",
                report_code, fight_id, teammate_id, e,
            )
            continue

        per_buff_intervals = intervals_by_teammate[teammate_id]
        teammate_total = 0.0
        for ev in dmg_events:
            # WCL damage events: 'damage' or 'calculateddamage' types.
            # Skip absorbs / heals / anything else. Amount is in 'amount'.
            if ev.get("type") not in ("damage", "calculateddamage"):
                continue
            t = ev.get("timestamp")
            if not isinstance(t, (int, float)):
                continue
            amount = ev.get("amount")
            if not isinstance(amount, (int, float)):
                continue
            t_int = int(t)
            # Check each active buff on this teammate and credit the
            # largest-uplift overlap. We don't double-credit if both
            # Ebon Might AND Prescience are up on the same teammate —
            # that would double-count the teammate's damage. Picking
            # the higher factor is conservative and avoids gaming the
            # metric by stacking buffs.
            best_factor = 0.0
            best_buff = None
            for buff_id, ivals in per_buff_intervals.items():
                if _in_any_window(t_int, ivals):
                    factor = UPLIFT_FACTORS.get(buff_id, 0.0)
                    if factor > best_factor:
                        best_factor = factor
                        best_buff = buff_id
            if best_buff is None:
                continue
            credited = amount * best_factor
            teammate_total += credited
            per_buff[best_buff] = per_buff.get(best_buff, 0.0) + credited

        per_teammate[teammate_id] = teammate_total

    total_uplift_damage = sum(per_teammate.values())
    return {
        "total_uplift_damage": total_uplift_damage,
        "per_buff": per_buff,
        "per_teammate": per_teammate,
        "buff_uptime_ms": uptime_ms,
    }
