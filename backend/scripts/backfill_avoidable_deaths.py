"""Recompute avoidable_deaths from stored pulls JSON.

Why: _count_avoidable_deaths reads the WCL Deaths table's
`killingAbility.guid`, which sometimes disagrees with the events API's
`killingAbilityGameID` (wrapper spell vs. final damaging tick). The
pulls builder uses the events API and is authoritative, so for any run
that has pulls stored we can recompute avoidable_deaths from the death
events inside pulls without touching WCL.

Usage (from backend/):
    python -m scripts.backfill_avoidable_deaths            # dry-run
    python -m scripts.backfill_avoidable_deaths --commit   # write changes
"""
from __future__ import annotations

import argparse

from sqlalchemy import select

from app.db import SessionLocal
from app.models import DungeonRun
from app.scoring.avoidable import get_avoidable_abilities


def _avoidable_from_pulls(pulls: list[dict] | None, avoidable_ids: set[int]) -> int:
    if not pulls or not avoidable_ids:
        return 0
    return sum(
        1
        for p in pulls
        for e in p.get("events", [])
        if e.get("type") == "death" and e.get("ability_id") in avoidable_ids
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist updates. Default is dry-run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process the first N candidate runs.")
    args = parser.parse_args()

    updates: list[tuple[int, int, int]] = []  # (run_id, old, new)
    with SessionLocal() as session:
        stmt = select(DungeonRun).where(DungeonRun.pulls.is_not(None))
        if args.limit:
            stmt = stmt.limit(args.limit)
        runs = list(session.execute(stmt).scalars())
        print(f"scanning {len(runs)} runs with pulls")

        for run in runs:
            avoidable_ids = get_avoidable_abilities(run.encounter_id)
            if not avoidable_ids:
                continue
            new_count = _avoidable_from_pulls(run.pulls, avoidable_ids)
            old_count = run.avoidable_deaths or 0
            if new_count > old_count:
                updates.append((run.id, old_count, new_count))
                if args.commit:
                    run.avoidable_deaths = new_count

        print(f"runs needing update: {len(updates)}")
        for run_id, old, new in updates[:20]:
            print(f"  run {run_id}: {old} -> {new}")
        if len(updates) > 20:
            print(f"  ... and {len(updates) - 20} more")

        if args.commit:
            session.commit()
            print(f"committed {len(updates)} updates")
        else:
            print("dry-run (use --commit to write)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
