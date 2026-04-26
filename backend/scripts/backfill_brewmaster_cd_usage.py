"""Refetch BuffsTable per Brewmaster run and recompute
`cooldown_usage_pct` using the talent-aware scorer.

Old ingests stored cd_usage at ~67% for every BRM running the no-Keg
build (Black Ox Brew talent path) because the scorer treated the
missing Exploding Keg aura as 0 uses. The new _get_cooldown_usage
skips talent-gated CDs that aren't in the player's BuffsTable; this
script applies that to existing DungeonRun rows so users see the
corrected grade without waiting for a manual refresh.

Cost: 1-2 WCL queries per run (masterData lookup is cached per
report_code so reports with multiple BRM runs only pay it once).
~750 BRM runs in production → ~1500 calls, well under the 54k/hr
multi-client budget.

Usage:
    python -m scripts.backfill_brewmaster_cd_usage              # dry-run
    python -m scripts.backfill_brewmaster_cd_usage --commit
    python -m scripts.backfill_brewmaster_cd_usage --commit --limit 50
"""
from __future__ import annotations

import argparse

from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import DungeonRun, Player
from app.pipeline.ingest import _get_cooldown_usage
from app.scoring.cooldowns import get_cooldowns_for_spec
from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist changes. Default dry-run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap rows processed this run.")
    args = parser.parse_args()

    spec_cds = get_cooldowns_for_spec(10, "Brewmaster")
    if not spec_cds:
        print("No Brewmaster cooldowns configured; aborting.")
        return 1

    with SessionLocal() as session:
        runs = list(
            session.execute(
                select(DungeonRun).where(DungeonRun.spec_name == "Brewmaster")
                .order_by(DungeonRun.id)
            ).scalars()
        )
        if args.limit:
            runs = runs[: args.limit]
        print(f"Recomputing cd_usage for {len(runs)} Brewmaster runs...")

        # Cache: report_code -> { player_name_lower: actor_id }
        actor_cache: dict[str, dict[str, int]] = {}

        updated = 0
        unchanged = 0
        skipped = 0
        rate_limited = False

        for i, run in enumerate(runs):
            if i and i % 50 == 0:
                print(f"  ... {i} processed (updated={updated} unchanged={unchanged} skipped={skipped})")
            try:
                # Resolve actor_id once per report
                if run.wcl_report_id not in actor_cache:
                    md = wcl_client.query("""
                    query($c: String!) {
                      reportData { report(code: $c) { masterData { actors(type: "Player") { id name } } } }
                    }
                    """, {"c": run.wcl_report_id})
                    actors = md["reportData"]["report"]["masterData"]["actors"]
                    actor_cache[run.wcl_report_id] = {
                        a["name"].lower(): a["id"] for a in actors
                    }

                player = session.get(Player, run.player_id)
                pname = (player.name if player else "").lower()
                actor_id = actor_cache[run.wcl_report_id].get(pname)
                if not actor_id:
                    skipped += 1
                    continue

                buffs = wcl_client.query("""
                query($c: String!, $f: [Int!]!, $s: Int!) {
                  reportData { report(code: $c) { buffsTable: table(fightIDs: $f, dataType: Buffs, sourceID: $s) } }
                }
                """, {"c": run.wcl_report_id, "f": [run.fight_id], "s": actor_id})
                buffs_table = buffs["reportData"]["report"]["buffsTable"]

                new_pct = _get_cooldown_usage(buffs_table, spec_cds, run.duration)
                old_pct = run.cooldown_usage_pct

                # Round to 1dp for the no-op check so floating-point noise
                # in the source data doesn't show up as a "change".
                if abs((old_pct or 0) - new_pct) < 0.05:
                    unchanged += 1
                    continue

                if args.commit:
                    session.execute(
                        text("UPDATE dungeon_runs SET cooldown_usage_pct = :p WHERE id = :id"),
                        {"p": new_pct, "id": run.id},
                    )
                updated += 1
            except WCLRateLimitedError as e:
                print(f"  WCL rate limited; stopping. retry_after={e.retry_after}s")
                rate_limited = True
                break
            except WCLQueryError as e:
                print(f"  run id={run.id} {run.wcl_report_id}/{run.fight_id}: WCL error: {e}")
                skipped += 1
                continue

        if args.commit and not rate_limited:
            session.commit()
            print(f"committed: {updated} rows updated, {unchanged} unchanged, {skipped} skipped")
        else:
            print(f"dry-run: would update {updated}, unchanged={unchanged}, skipped={skipped}")
            if not args.commit:
                print("re-run with --commit to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
