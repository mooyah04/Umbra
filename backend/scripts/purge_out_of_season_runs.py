"""Delete DungeonRun rows whose encounter_id is not in the active-season
dungeon pool.

Background: before the ingest-time season filter landed (2026-04-18),
ingest blindly stored every M+ fight WCL returned for a character. When
a user's recent WCL reports included last season's logs (October/November
2025 runs from TWW S2 for example), those fights got persisted with
encounter_ids outside our registry. They show up on the profile under
blank dungeon names and skew aggregate counts.

This script removes them. Idempotent — runs can be re-run safely and
will be no-ops once the DB is clean.

Usage (from backend/ or `railway ssh`):
    python -m scripts.purge_out_of_season_runs            # dry-run
    python -m scripts.purge_out_of_season_runs --commit   # apply
"""
from __future__ import annotations

import argparse

from sqlalchemy import delete, select, func

from app.db import SessionLocal
from app.models import DungeonRun, PlayerScore
from app.scoring.dungeons.registry import active_encounter_ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist the deletions. Default is dry-run.")
    args = parser.parse_args()

    active = active_encounter_ids()
    print(f"Active-season encounter IDs ({len(active)}): {sorted(active)}")

    with SessionLocal() as session:
        # How many would we delete? Group by encounter_id so the output
        # shows which legacy dungeons are polluting the DB.
        stmt = (
            select(DungeonRun.encounter_id, func.count().label("n"))
            .where(DungeonRun.encounter_id.notin_(active))
            .group_by(DungeonRun.encounter_id)
            .order_by(func.count().desc())
        )
        rows = list(session.execute(stmt).all())
        if not rows:
            print("No out-of-season runs found. Nothing to do.")
            return 0

        total = sum(n for _, n in rows)
        print(f"\n{total} out-of-season DungeonRun rows across "
              f"{len(rows)} distinct legacy encounters:")
        for enc_id, n in rows:
            print(f"  encounter_id={enc_id:>6}  runs={n}")

        # Which players are affected? Useful for deciding whether to
        # also recompute their PlayerScore rows after purge.
        affected_stmt = (
            select(DungeonRun.player_id)
            .where(DungeonRun.encounter_id.notin_(active))
            .distinct()
        )
        affected_players = [r[0] for r in session.execute(affected_stmt).all()]
        print(f"\n{len(affected_players)} players have at least one "
              "out-of-season run.")

        if not args.commit:
            print("\nDry-run. Re-run with --commit to apply.")
            return 0

        # Delete
        del_stmt = delete(DungeonRun).where(
            DungeonRun.encounter_id.notin_(active)
        )
        res = session.execute(del_stmt)
        print(f"\nDeleted {res.rowcount} DungeonRun rows.")

        # Invalidate PlayerScore rows for affected players so the next
        # scheduled/user refresh recomputes their grade from only the
        # current-season runs. Simpler and safer than recomputing inline
        # (scoring engine needs WCL data we don't keep locally).
        score_del = delete(PlayerScore).where(
            PlayerScore.player_id.in_(affected_players)
        )
        res2 = session.execute(score_del)
        print(f"Invalidated {res2.rowcount} PlayerScore rows — affected "
              "players will re-grade next time they're refreshed.")

        session.commit()
        print("\nCommitted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
