"""Regenerate PlayerScore rows for players whose scores were invalidated
but whose DungeonRun data is still locally usable.

Context: purge scripts (out-of-season, phantom runs) delete PlayerScore
rows so grades recompute against the cleaned-up run set. Without a
backfill, the next profile view shows "Not rated" until the user clicks
Refresh — which triggers a full WCL re-ingest and burns API budget even
though we already have all the runs locally.

This script closes that gap: for every player with DungeonRun rows but
no PlayerScore, recompute grades from the in-DB runs. No WCL calls.

Scoring matches ingest's behavior with two caveats:
  - zone_dps_percentile is None (we didn't persist it). The engine
    falls back to averaging per-run WCL percentiles (r.dps / r.hps on
    each DungeonRun), which are already stored. Grades will match a
    full re-ingest within a percentile point or two.
  - class_id is trusted as-is on Player (last ingest resolved it).

Usage (from /app or backend/ locally):
    python -m scripts.rescore_invalidated_players            # dry-run
    python -m scripts.rescore_invalidated_players --commit   # apply
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore, Role
from app.scoring.engine import score_player_runs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist the new scores. Default is dry-run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        # Players that have at least one DungeonRun but zero PlayerScore.
        # NOT IN subquery is cheap on this table at current size.
        scored_player_ids = select(PlayerScore.player_id).distinct().subquery()
        candidates_stmt = (
            select(Player)
            .join(DungeonRun, DungeonRun.player_id == Player.id)
            .where(Player.id.notin_(select(scored_player_ids)))
            .distinct()
        )
        candidates = list(session.execute(candidates_stmt).scalars())

        if not candidates:
            print("No invalidated players found. Nothing to do.")
            return 0

        print(f"Found {len(candidates)} players with runs but no scores.\n")

        rescored = 0
        skipped = 0
        new_score_rows = 0

        for player in candidates:
            runs_stmt = (
                select(DungeonRun)
                .where(DungeonRun.player_id == player.id)
                .order_by(DungeonRun.logged_at.desc())
            )
            all_runs = list(session.execute(runs_stmt).scalars())
            recent_runs = all_runs[:settings.max_runs_to_analyze]

            runs_by_role: dict[Role, list[DungeonRun]] = defaultdict(list)
            for run in recent_runs:
                runs_by_role[run.role].append(run)

            if not runs_by_role:
                skipped += 1
                continue

            primary_role = max(
                runs_by_role, key=lambda r: len(runs_by_role[r])
            )

            scored_any = False
            for role, role_runs in runs_by_role.items():
                if len(role_runs) < settings.min_runs_for_grade:
                    continue

                result = score_player_runs(
                    role_runs,
                    role,
                    zone_dps_percentile=None,
                    zone_dps_ilvl_percentile=None,
                    class_id=player.class_id,
                )

                if args.commit:
                    session.add(PlayerScore(
                        player_id=player.id,
                        role=role,
                        overall_grade=result.overall_grade,
                        composite_score=result.composite_score,
                        category_scores=result.category_scores,
                        runs_analyzed=len(all_runs),
                        primary_role=(role == primary_role),
                    ))
                new_score_rows += 1
                scored_any = True

            if scored_any:
                rescored += 1
            else:
                # Not enough runs in any single role to meet the floor.
                # Leave these as-is — "Not rated" is the correct state.
                skipped += 1

        print(f"Would rescore {rescored} players "
              f"({new_score_rows} PlayerScore rows).")
        print(f"Skipped {skipped} players "
              "(fewer than min_runs_for_grade in every role).")

        if not args.commit:
            print("\nDry-run. Re-run with --commit to apply.")
            return 0

        session.commit()
        print("\nCommitted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
