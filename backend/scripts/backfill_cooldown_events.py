"""Backfill cooldown events into existing runs' pulls JSON.

Why: CD tracking in the pull breakdown landed after many runs were already
ingested. Those runs' pulls[].events arrays have deaths / avoidable damage /
interrupts but no "cooldown" entries. This script fetches Buffs events for
each affected run, filters to the spec's tracked major-CD buff IDs, and
appends a "cooldown" event to the matching pull — without touching other
fields on the run.

Per-run cost: one playerDetails fetch to resolve the actor_id, plus one
paginated Buffs events fetch. Roughly 2 WCL queries per run. Not cheap at
scale, so default --limit is 50 and --sleep is 0.3s between runs.

Usage (from backend/):
    python -m scripts.backfill_cooldown_events                  # dry-run
    python -m scripts.backfill_cooldown_events --commit
    python -m scripts.backfill_cooldown_events --commit --limit 200
    python -m scripts.backfill_cooldown_events --run-id 1234    # single run
"""
from __future__ import annotations

import argparse
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.db import SessionLocal
from app.models import DungeonRun, Player
from app.scoring.cooldowns import get_cooldowns_for_spec
from app.wcl.client import wcl_client
from app.pipeline.ingest import _find_player_in_details, _iter_player_details

logger = logging.getLogger(__name__)


def _class_id_from_name(class_name: str) -> int | None:
    """Map WCL class name (e.g. 'DemonHunter') to our internal class_id.
    Kept local to avoid importing the full pipeline layer."""
    from app.scoring.roles import class_id_from_name
    return class_id_from_name(class_name)


def _resolve_actor_id(
    report_code: str, fight_id: int, player_name: str
) -> tuple[int | None, str | None]:
    """Return (actor_id, class_name) for the player in this fight.

    Fallback path: if playerDetails for the specific fight doesn't list
    the player, fall back to masterData.actors for the whole report. The
    WCL playerDetails query occasionally returns a sparse roster for a
    specific fight (the scoping semantics aren't strict about who was
    present vs who was merely in the raid group), so a name miss there
    isn't authoritative. masterData.actors is the report-wide actor list
    and is stable."""
    rd = wcl_client.get_report_player_data(report_code, [fight_id])
    pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {})
    info = _find_player_in_details(pd, player_name)
    if info:
        actor_id = info.get("id")
        class_name = info.get("type")
        return (int(actor_id) if isinstance(actor_id, int) else None), class_name

    # Fallback: report masterData.actors
    names_seen = sorted({
        p.get("name", "")
        for _g, p in _iter_player_details(pd)
    })
    logger.debug(
        "playerDetails miss for %r in %s/%d — names present: %s",
        player_name, report_code, fight_id, names_seen,
    )

    md = wcl_client.get_report_master_data(report_code) or {}
    for actor in (md.get("actors") or []):
        if (actor.get("type") or "").lower() != "player":
            continue
        if (actor.get("name") or "").lower() == player_name.lower():
            actor_id = actor.get("id")
            # masterData doesn't carry a canonical spec/class in the same
            # shape as playerDetails — subType is usually the class name.
            class_name = actor.get("subType") or ""
            logger.debug(
                "resolved %r via masterData.actors -> id=%s class=%s",
                player_name, actor_id, class_name,
            )
            return (int(actor_id) if isinstance(actor_id, int) else None), class_name

    return None, None


def _has_cooldown_events(pulls: list[dict]) -> bool:
    for p in pulls:
        for e in p.get("events", []):
            if e.get("type") == "cooldown":
                return True
    return False


def _build_cooldown_events(
    *,
    report_code: str,
    fight_id: int,
    fight_start_ms: int,
    actor_id: int,
    spec_cooldowns: list[tuple[int, str, float, str]],
    pulls: list[dict],
) -> int:
    """Fetch Buffs events and append cooldown entries to the matching
    pulls' events lists. Mutates `pulls` in place. Returns the number of
    cooldown events appended."""
    if not spec_cooldowns:
        return 0

    cd_name_by_id = {buff_id: name for buff_id, name, _u, _k in spec_cooldowns}
    cd_kind_by_id = {buff_id: kind for buff_id, _n, _u, kind in spec_cooldowns}
    cd_buff_ids = set(cd_name_by_id.keys())

    try:
        raw = wcl_client.get_player_events(
            report_code, [fight_id],
            data_type="Buffs",
            source_id=actor_id,
        )
    except Exception as e:
        logger.debug("buffs events failed for %s/%d: %s", report_code, fight_id, e)
        return 0

    def _assign_to_pull(t_sec: float) -> dict | None:
        for p in pulls:
            if p["start_t"] <= t_sec <= p["end_t"]:
                return p
        return None

    appended = 0
    for ev in raw:
        if ev.get("type") != "applybuff":
            continue
        aid = ev.get("abilityGameID")
        if not isinstance(aid, int) or aid not in cd_buff_ids:
            continue
        ts = ev.get("timestamp")
        if not isinstance(ts, (int, float)):
            continue
        t_sec = (ts - fight_start_ms) / 1000.0
        pull = _assign_to_pull(t_sec)
        if pull is None:
            continue
        pull.setdefault("events", []).append({
            "t": round(t_sec, 1),
            "type": "cooldown",
            "ability_id": aid,
            "ability_name": cd_name_by_id.get(aid, "Unknown"),
            "amount": None,
            "kind": cd_kind_by_id.get(aid, "offensive"),
        })
        appended += 1

    if appended:
        for p in pulls:
            p["events"].sort(key=lambda e: e["t"])

    return appended


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist updates. Default is dry-run.")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max runs to process this invocation (default 50).")
    parser.add_argument("--run-id", type=int, default=None,
                        help="Only process the specified run id.")
    parser.add_argument("--sleep", type=float, default=0.3,
                        help="Seconds to sleep between runs (default 0.3).")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    touched: list[tuple[int, int]] = []  # (run_id, events_appended)
    skipped_already = 0
    skipped_no_spec_cds = 0
    skipped_no_actor = 0

    with SessionLocal() as session:
        stmt = (
            select(DungeonRun, Player)
            .join(Player, Player.id == DungeonRun.player_id)
            .where(DungeonRun.pulls.is_not(None))
        )
        if args.run_id is not None:
            stmt = stmt.where(DungeonRun.id == args.run_id)
        stmt = stmt.order_by(DungeonRun.id.asc())
        rows = list(session.execute(stmt).all())
        logger.info("candidates: %d runs with pulls", len(rows))

        processed = 0
        for run, player in rows:
            if processed >= args.limit:
                break
            pulls = run.pulls or []
            if not pulls:
                continue
            if _has_cooldown_events(pulls):
                skipped_already += 1
                continue

            class_id = player.class_id
            spec_cds = get_cooldowns_for_spec(class_id, run.spec_name)
            if not spec_cds:
                skipped_no_spec_cds += 1
                continue

            # Resolve actor_id and confirm class. Some characters rename
            # or switch mains; the playerDetails class wins if they disagree.
            actor_id, class_name = _resolve_actor_id(
                run.wcl_report_id, run.fight_id, player.name
            )
            if actor_id is None:
                skipped_no_actor += 1
                logger.debug(
                    "run %d: player %r not found in report %s fight %d",
                    run.id, player.name, run.wcl_report_id, run.fight_id,
                )
                time.sleep(args.sleep)
                continue
            # If WCL says they played a different class, re-resolve CDs.
            if class_name:
                resolved_class_id = _class_id_from_name(class_name) or class_id
                if resolved_class_id != class_id:
                    spec_cds = get_cooldowns_for_spec(resolved_class_id, run.spec_name)
                    if not spec_cds:
                        skipped_no_spec_cds += 1
                        time.sleep(args.sleep)
                        continue

            # fight_start_ms: pulls[0].start_t is seconds into fight, and
            # we stored pulls with start_t == 0 for the first pull when
            # the fight starts. But the ingest builder uses
            # fight.get("startTime") (absolute log ms) as fight_start_ms.
            # Here we only have seconds-relative timestamps in pulls, so
            # we need absolute fight startTime from WCL.
            fights_info = wcl_client.get_report_fights(run.wcl_report_id) or []
            fight_abs_start_ms: int | None = None
            for f in fights_info:
                if f.get("id") == run.fight_id:
                    fight_abs_start_ms = f.get("startTime")
                    break
            if not isinstance(fight_abs_start_ms, (int, float)):
                logger.debug("run %d: could not resolve fight start ms", run.id)
                time.sleep(args.sleep)
                continue

            appended = _build_cooldown_events(
                report_code=run.wcl_report_id,
                fight_id=run.fight_id,
                fight_start_ms=int(fight_abs_start_ms),
                actor_id=actor_id,
                spec_cooldowns=spec_cds,
                pulls=pulls,
            )
            if appended:
                touched.append((run.id, appended))
                if args.commit:
                    # JSON column needs explicit flag_modified for SQLAlchemy
                    # to detect the in-place mutation.
                    run.pulls = pulls
                    flag_modified(run, "pulls")

            processed += 1
            time.sleep(args.sleep)

        logger.info("touched: %d runs", len(touched))
        for run_id, count in touched[:20]:
            logger.info("  run %d: +%d cooldown events", run_id, count)
        if len(touched) > 20:
            logger.info("  ... and %d more", len(touched) - 20)
        logger.info(
            "skipped: already=%d, no-spec-cds=%d, no-actor=%d",
            skipped_already, skipped_no_spec_cds, skipped_no_actor,
        )

        if args.commit:
            session.commit()
            logger.info("committed %d updates", len(touched))
        else:
            logger.info("dry-run (use --commit to write)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
