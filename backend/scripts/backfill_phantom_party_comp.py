"""Re-fetch playerDetails per affected fight and rewrite `party_comp`
on rows where WCL's old data leaked phantom players (e.g. a healer who
DC'd at the pull but still appeared in playerDetails alongside the real
party). The forward fix is in `_extract_party_comp` — see ingest.py.
This script repairs already-stored rows.

Targets only rows with `jsonb_array_length(party_comp) > 5`, so it's
idempotent and cheap to re-run after future ingests if the issue
recurs.

Usage (from backend/):
    python -m scripts.backfill_phantom_party_comp              # dry-run
    python -m scripts.backfill_phantom_party_comp --commit     # apply
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

from sqlalchemy import text

from app.db import SessionLocal
from app.pipeline.ingest import _extract_party_comp
from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client
from app.wcl.queries import REPORT_PLAYER_DATA


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist changes. Default dry-run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap distinct fights processed this run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        # Pull all rows with oversized party_comp. Bucket by (report, fight)
        # so we make one WCL call per fight regardless of how many of its
        # 5 participants are stored in our DB.
        rows = session.execute(text("""
            SELECT id, wcl_report_id, fight_id, jsonb_array_length(to_jsonb(party_comp)) AS pc_len
            FROM dungeon_runs
            WHERE party_comp IS NOT NULL
              AND jsonb_array_length(to_jsonb(party_comp)) > 5
            ORDER BY wcl_report_id, fight_id
        """)).all()

        by_fight: dict[tuple[str, int], list[int]] = defaultdict(list)
        for r in rows:
            by_fight[(r.wcl_report_id, r.fight_id)].append(r.id)

        fights = list(by_fight.items())
        if args.limit:
            fights = fights[: args.limit]

        print(
            f"backfill: {len(rows)} rows across {len(by_fight)} distinct fights; "
            f"processing {len(fights)} fights"
        )

        fixed_rows = 0
        unchanged_fights = 0
        empty_fights = 0
        rate_limited = False

        for (report_code, fight_id), run_ids in fights:
            try:
                resp = wcl_client.query(
                    REPORT_PLAYER_DATA,
                    {"code": report_code, "fightIDs": [fight_id]},
                )
            except WCLRateLimitedError as e:
                print(f"  WCL rate limited; stopping. retry_after={e.retry_after}s")
                rate_limited = True
                break
            except WCLQueryError as e:
                print(f"  {report_code}/{fight_id}: WCL query error: {e}; skipping")
                continue

            report_payload = resp.get("reportData", {}).get("report", {}) or {}
            player_details = report_payload.get("playerDetails") or {}
            new_pc = _extract_party_comp(
                player_details,
                damage_table=report_payload.get("damageTable"),
                healing_table=report_payload.get("healingTable"),
                damage_taken_table=report_payload.get("damageTakenTable"),
            ) or None
            new_len = len(new_pc) if new_pc else 0

            if new_len != 5:
                # Conservative — only rewrite rows where the filter
                # produced exactly 5 entries (the canonical M+ comp).
                # Anything else (still oversized OR under-filtered to 4
                # because the fight had genuinely sparse perf data)
                # might make the row worse, so leave it alone.
                if new_len == 0:
                    empty_fights += 1
                else:
                    unchanged_fights += 1
                print(
                    f"  {report_code}/{fight_id}: filter produced {new_len}; "
                    f"skipping ({len(run_ids)} rows untouched)"
                )
                continue

            print(
                f"  {report_code}/{fight_id}: party {len(run_ids)} rows -> "
                f"party_comp {new_len} entries"
            )
            if args.commit:
                session.execute(
                    text(
                        "UPDATE dungeon_runs SET party_comp = CAST(:pc AS json) "
                        "WHERE id = ANY(:ids)"
                    ),
                    {"pc": json.dumps(new_pc), "ids": run_ids},
                )
            fixed_rows += len(run_ids)

        if args.commit and not rate_limited:
            session.commit()
            print(f"committed: {fixed_rows} rows updated")
        else:
            print(
                f"dry-run: would update {fixed_rows} rows "
                f"(unchanged_fights={unchanged_fights}, empty_fights={empty_fights})"
            )
            if not args.commit:
                print("re-run with --commit to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
