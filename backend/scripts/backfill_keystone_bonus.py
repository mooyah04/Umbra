"""Re-query WCL per report and correct `timed` / `keystone_bonus` on
existing DungeonRun rows.

The prior ingest heuristic compared log duration to `keystoneTime`
(which is actually the run's official Blizzard completion time, not
the par timer). Razor-thin finishes like +3 chests with a little bit
of release/run-back overhead got flagged depleted. This script re-
queries `REPORT_FIGHTS` per unique report_code (one cheap WCL call per
report, not per fight) and flips `timed` + writes `keystone_bonus`
where WCL says otherwise.

Runs only where `keystone_bonus IS NULL` (so it's idempotent + cheap
to re-run after new ingests).

Usage (from backend/ or via railway ssh):
    python -m scripts.backfill_keystone_bonus            # dry-run
    python -m scripts.backfill_keystone_bonus --commit   # apply
    python -m scripts.backfill_keystone_bonus --commit --limit 200
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from app.db import SessionLocal
from app.models import DungeonRun
from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client
from app.wcl.queries import REPORT_FIGHTS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist changes. Default dry-run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap distinct reports processed this run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        # Bucket runs by report_code so we make one WCL call per report
        # regardless of how many fights we need to backfill in it.
        stmt = select(DungeonRun).where(DungeonRun.keystone_bonus.is_(None))
        runs = list(session.execute(stmt).scalars())
        by_report: dict[str, list[DungeonRun]] = defaultdict(list)
        for r in runs:
            by_report[r.wcl_report_id].append(r)

        reports = list(by_report.items())
        if args.limit:
            reports = reports[: args.limit]
        print(f"backfill: {len(runs)} runs across {len(by_report)} reports; "
              f"processing {len(reports)} reports")

        flipped_to_timed = 0
        flipped_to_depleted = 0
        keystone_bonus_set = 0
        skipped_reports = 0

        for report_code, report_runs in reports:
            try:
                d = wcl_client.query(REPORT_FIGHTS, {"code": report_code})
            except WCLRateLimitedError as e:
                print(f"rate-limited with {e.retry_after}s; stopping early.")
                break
            except WCLQueryError as e:
                print(f"skip {report_code}: WCL error {e}")
                skipped_reports += 1
                continue

            fights_by_id = {
                f["id"]: f
                for f in d.get("reportData", {}).get("report", {}).get("fights", [])
            }

            for run in report_runs:
                fight = fights_by_id.get(run.fight_id)
                if fight is None:
                    continue
                bonus = fight.get("keystoneBonus") or 0
                kill = fight.get("kill", False)
                correct_timed = bool(kill and bonus > 0)

                if run.keystone_bonus != bonus:
                    if args.commit:
                        run.keystone_bonus = bonus
                    keystone_bonus_set += 1
                if run.timed != correct_timed:
                    if correct_timed:
                        flipped_to_timed += 1
                    else:
                        flipped_to_depleted += 1
                    if args.commit:
                        run.timed = correct_timed

            if args.commit:
                session.commit()

        print(f"keystone_bonus set: {keystone_bonus_set}")
        print(f"timed flipped depleted→timed: {flipped_to_timed}")
        print(f"timed flipped timed→depleted: {flipped_to_depleted}")
        print(f"reports skipped (errors): {skipped_reports}")
        if not args.commit:
            print("dry-run (use --commit to write)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
