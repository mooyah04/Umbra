"""Delete DungeonRun rows that look like disconnects or phantom
participation (very low cast counts).

Background: WCL's playerDetails lists anyone who was in the raid group
for a fight, including players who disconnected seconds into the run.
These show up in our DB as real DungeonRun rows but with tiny cast
counts (observed as low as 1). Because they flow through the scoring
engine with the rest of a player's runs, they zero out CPM and
cooldown-usage and can demote a plausibly B-grade player into D.

The ingest pipeline now filters these at write time, but prior ingests
left some in the DB. This script cleans them up.

Idempotent — subsequent runs are no-ops once the DB is clean.

Usage (from backend/ or `railway ssh`):
    python -m scripts.purge_phantom_runs            # dry-run
    python -m scripts.purge_phantom_runs --commit   # apply
"""
from __future__ import annotations

import argparse

from sqlalchemy import delete, select, func

from app.db import SessionLocal
from app.models import DungeonRun, PlayerScore
from app.pipeline.ingest import MIN_CASTS_FOR_VALID_RUN


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist the deletions. Default is dry-run.")
    args = parser.parse_args()

    print(f"Phantom threshold: casts_total < {MIN_CASTS_FOR_VALID_RUN}")

    with SessionLocal() as session:
        # Summarize what we would delete, grouped by cast count so we
        # can eyeball the distribution (are most of these 0-cast or
        # smeared across 1-19?).
        stmt = (
            select(DungeonRun.casts_total, func.count().label("n"))
            .where(DungeonRun.casts_total < MIN_CASTS_FOR_VALID_RUN)
            .group_by(DungeonRun.casts_total)
            .order_by(DungeonRun.casts_total)
        )
        rows = list(session.execute(stmt).all())
        if not rows:
            print("No phantom runs found. Nothing to do.")
            return 0

        total = sum(n for _, n in rows)
        print(f"\n{total} phantom DungeonRun rows across "
              f"{len(rows)} distinct cast-count buckets:")
        for casts, n in rows:
            print(f"  casts_total={casts:>3}  runs={n}")

        affected_stmt = (
            select(DungeonRun.player_id)
            .where(DungeonRun.casts_total < MIN_CASTS_FOR_VALID_RUN)
            .distinct()
        )
        affected_players = [r[0] for r in session.execute(affected_stmt).all()]
        print(f"\n{len(affected_players)} players have at least one "
              "phantom run.")

        if not args.commit:
            print("\nDry-run. Re-run with --commit to apply.")
            return 0

        del_stmt = delete(DungeonRun).where(
            DungeonRun.casts_total < MIN_CASTS_FOR_VALID_RUN
        )
        res = session.execute(del_stmt)
        print(f"\nDeleted {res.rowcount} DungeonRun rows.")

        # Invalidate PlayerScore for affected players — their grade was
        # computed including phantom runs. Next refresh will re-score
        # from the cleaned-up run set. Same pattern as the out-of-season
        # purge.
        score_del = delete(PlayerScore).where(
            PlayerScore.player_id.in_(affected_players)
        )
        res2 = session.execute(score_del)
        print(f"Invalidated {res2.rowcount} PlayerScore rows — affected "
              "players will re-grade on their next refresh.")

        session.commit()
        print("\nCommitted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
