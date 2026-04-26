"""Recompute PlayerScore rows for Brewmaster tanks from their existing
DungeonRun data, without re-fetching from WCL.

The cd_usage backfill updated `cooldown_usage_pct` on existing runs,
but the cached `PlayerScore` (composite, category_scores, grade) is
only refreshed during ingest. This script picks up the corrected
cd_usage by re-running the scoring engine on the stored runs and
replacing the matching PlayerScore row in place.

zone_dps_percentile and zone_dps_ilvl_percentile come from WCL during
ingest — we reuse them from the existing PlayerScore.category_scores
so we don't have to re-query WCL just to recompute. Other categories
re-derive from the (now-corrected) DungeonRun data.

Usage:
    python -m scripts.recompute_player_scores_brm              # dry-run
    python -m scripts.recompute_player_scores_brm --commit
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
                        help="Persist changes. Default dry-run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        # Find every player who has a Brewmaster run. PlayerScore is per-
        # role, so we'll recompute the tank role for these players.
        brm_player_ids = list(session.execute(
            select(DungeonRun.player_id)
            .where(DungeonRun.spec_name == "Brewmaster")
            .distinct()
        ).scalars())

        print(f"Found {len(brm_player_ids)} players with Brewmaster runs")

        updated = 0
        unchanged = 0
        for pid in brm_player_ids:
            player = session.get(Player, pid)
            if not player:
                continue

            # Load all of this player's runs, newest first.
            all_runs = list(session.execute(
                select(DungeonRun)
                .where(DungeonRun.player_id == pid)
                .order_by(DungeonRun.logged_at.desc())
            ).scalars())
            recent_runs = all_runs[: settings.max_runs_to_analyze]

            runs_by_role: dict[Role, list[DungeonRun]] = defaultdict(list)
            for r in recent_runs:
                runs_by_role[r.role].append(r)

            primary_role = (
                max(runs_by_role, key=lambda r: len(runs_by_role[r]))
                if runs_by_role else Role.dps
            )

            # Existing PlayerScore rows — keep zone_dps percentiles (fetched
            # from WCL at last ingest) by reading them off the cached score.
            existing_scores = {
                ps.role: ps for ps in session.execute(
                    select(PlayerScore).where(PlayerScore.player_id == pid)
                ).scalars()
            }

            # Only recompute the tank role for BRM cleanup.
            role = Role.tank
            role_runs = runs_by_role.get(role) or []
            if len(role_runs) < settings.min_runs_for_grade:
                continue

            old = existing_scores.get(role)
            zone_dps = (old.category_scores.get("damage_output") if old else None)
            zone_dps_ilvl = (old.category_scores.get("damage_output_ilvl") if old else None)

            result = score_player_runs(
                role_runs, role,
                zone_dps_percentile=zone_dps,
                zone_dps_ilvl_percentile=zone_dps_ilvl,
                class_id=player.class_id,
            )

            old_grade = old.overall_grade if old else None
            old_cd = old.category_scores.get("cooldown_usage") if old else None
            new_cd = result.category_scores.get("cooldown_usage")

            if old and abs((old_cd or 0) - (new_cd or 0)) < 0.05 and old_grade == result.overall_grade:
                unchanged += 1
                continue

            print(
                f"  {player.name}-{player.realm} {player.region}: "
                f"grade {old_grade} -> {result.overall_grade}, "
                f"cd_usage {old_cd} -> {new_cd}"
            )

            if args.commit:
                if old:
                    old.overall_grade = result.overall_grade
                    old.composite_score = result.composite_score
                    old.category_scores = result.category_scores
                    old.runs_analyzed = max(len(all_runs), old.runs_analyzed or 0)
                    old.primary_role = (role == primary_role)
                else:
                    session.add(PlayerScore(
                        player_id=pid,
                        role=role,
                        overall_grade=result.overall_grade,
                        composite_score=result.composite_score,
                        category_scores=result.category_scores,
                        runs_analyzed=len(all_runs),
                        primary_role=(role == primary_role),
                    ))
            updated += 1

        if args.commit:
            session.commit()
            print(f"committed: {updated} PlayerScore rows updated, {unchanged} unchanged")
        else:
            print(f"dry-run: would update {updated}, unchanged={unchanged}")
            print("re-run with --commit to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
