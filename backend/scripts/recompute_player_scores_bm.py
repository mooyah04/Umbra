"""Recompute PlayerScore rows for Beast Mastery hunters from existing
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
    python -m scripts.recompute_player_scores_bm              # dry-run
    python -m scripts.recompute_player_scores_bm --commit
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore, Role
from app.scoring.engine import score_player_runs


def _zone_pct_or_none(old, key: str) -> float | None:
    """Treat the engine's excluded-category placeholder (0.0) as None
    so the recompute doesn't double-penalize players whose damage_output
    was excluded at last ingest. See impact_report.py for full discussion."""
    if not old:
        return None
    v = (old.category_scores or {}).get(key)
    if v is None or v == 0.0:
        return None
    return v


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist changes. Default dry-run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        bm_player_ids = list(session.execute(
            select(DungeonRun.player_id)
            .where(DungeonRun.spec_name == "Beast Mastery")
            .distinct()
        ).scalars())

        print(f"Found {len(bm_player_ids)} players with Beast Mastery runs")

        updated = 0
        unchanged = 0
        for pid in bm_player_ids:
            player = session.get(Player, pid)
            if not player:
                continue

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

            existing_scores = {
                ps.role: ps for ps in session.execute(
                    select(PlayerScore).where(PlayerScore.player_id == pid)
                ).scalars()
            }

            role = Role.dps
            role_runs = runs_by_role.get(role) or []
            if len(role_runs) < settings.min_runs_for_grade:
                continue

            old = existing_scores.get(role)
            # 0.0 in category_scores can mean "excluded at last ingest"
            # rather than "real 0th percentile" — see impact_report.py.
            zone_dps = _zone_pct_or_none(old, "damage_output")
            zone_dps_ilvl = _zone_pct_or_none(old, "damage_output_ilvl")

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
