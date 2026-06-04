"""Full prod rescore for the damage_output bracketed swap + threshold
recalibration (2026-06-04).

Recomputes every PlayerScore in place under the new engine:
  - damage_output is now the same-key-bracketed per-run average
    (_score_damage_output), not WCL's "overall" zoneRankings percentile.
  - GRADE_THRESHOLDS were re-fit to keep the distribution stable.

No WCL calls — uses runs already in the DB (r.dps holds the bracketed
percentile) plus the WCL overall/ilvl percentiles already stored on the
existing PlayerScore (carried forward as display-only context).

Idempotent: reads the overall percentile from `damage_output_overall`
when present (set by a prior run of this script), else from the legacy
`damage_output` field (pre-swap, where it lived). Safe to re-run.

Usage (from backend/ with DATABASE_URL pointed at prod):
    python -m scripts.rescore_all_damage_output_swap            # dry-run
    python -m scripts.rescore_all_damage_output_swap --commit   # apply
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore
from app.scoring.engine import score_player_runs


def _ctx_pct(cat: dict, *keys: str) -> float | None:
    """First non-zero, non-null value among keys (0.0 is the engine's
    excluded-category placeholder, treated as missing)."""
    for k in keys:
        v = cat.get(k)
        if v is not None and v != 0.0:
            return v
    return None


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist the new scores. Default is dry-run.")
    args = parser.parse_args()

    grade_moves: Counter = Counter()
    moved = 0
    rescored = 0
    cactue_line = None

    with SessionLocal() as session:
        scores = list(session.execute(select(PlayerScore)).scalars())
        print(f"PlayerScore rows: {len(scores)}\n")

        for ps in scores:
            player = session.get(Player, ps.player_id)
            if not player:
                continue

            all_runs = list(session.execute(
                select(DungeonRun)
                .where(DungeonRun.player_id == ps.player_id)
                .order_by(DungeonRun.logged_at.desc())
            ).scalars())
            recent = all_runs[: settings.max_runs_to_analyze]
            role_runs = [r for r in recent if r.role == ps.role]
            if len(role_runs) < settings.min_runs_for_grade:
                # Falls below the grade floor under current data — leave the
                # stored row untouched rather than silently zeroing it.
                continue

            cat = ps.category_scores or {}
            zone_overall = _ctx_pct(cat, "damage_output_overall", "damage_output")
            zone_ilvl = _ctx_pct(cat, "damage_output_ilvl")

            result = score_player_runs(
                role_runs, ps.role,
                zone_dps_percentile=zone_overall,
                zone_dps_ilvl_percentile=zone_ilvl,
                class_id=player.class_id,
            )

            old_grade = ps.overall_grade
            if old_grade != result.overall_grade:
                moved += 1
                grade_moves[(old_grade, result.overall_grade)] += 1

            if player.name.lower() == "cactue" and player.realm.lower() == "archimonde":
                cactue_line = (
                    f"cactue-Archimonde [{ps.role.value}]: "
                    f"{old_grade} ({ps.composite_score:.1f}) -> "
                    f"{result.overall_grade} ({result.composite_score:.1f})  "
                    f"DO same-key={result.category_scores.get('damage_output')}, "
                    f"overall={result.category_scores.get('damage_output_overall')}"
                )

            if args.commit:
                ps.overall_grade = result.overall_grade
                ps.composite_score = result.composite_score
                ps.category_scores = result.category_scores
                ps.runs_analyzed = len(all_runs)
            rescored += 1

        print(f"Rescored: {rescored} (grade moved: {moved})")
        print("Top grade transitions:")
        for (o, n), c in grade_moves.most_common(15):
            print(f"  {o} -> {n}: {c}")
        if cactue_line:
            print(f"\n{cactue_line}")
        else:
            print("\n(cactue-Archimonde not found / below grade floor)")

        if not args.commit:
            print("\nDry-run. Re-run with --commit to apply.")
            return 0

        session.commit()
        print("\nCommitted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
