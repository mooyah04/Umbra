"""Analyze scoring distribution for high keystone runs (+20 and above).

Pulls real run data from the DB, scores each run individually, and
reports per-category distributions by key-level bracket so we can see
where the scoring engine breaks down at high keys.

Read-only — never writes to the DB.

Usage:
  cd backend
  python -m scripts.analyze_high_keys
  python -m scripts.analyze_high_keys --min-key 23
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore, Role
from app.scoring.engine import score_player_runs


def percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * pct / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def print_distribution(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label}: no data")
        return
    values.sort()
    n = len(values)
    print(
        f"  {label:>22s}  n={n:>5}  "
        f"min={values[0]:5.1f}  p10={percentile(values, 10):5.1f}  "
        f"p25={percentile(values, 25):5.1f}  p50={percentile(values, 50):5.1f}  "
        f"p75={percentile(values, 75):5.1f}  p90={percentile(values, 90):5.1f}  "
        f"max={values[-1]:5.1f}"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-key", type=int, default=20, help="Minimum keystone level to analyze")
    parser.add_argument("--limit", type=int, default=None, help="Limit total runs analyzed")
    args = parser.parse_args()

    with SessionLocal() as session:
        # Overview: key level distribution
        key_dist = list(session.execute(
            select(
                DungeonRun.keystone_level,
                func.count(DungeonRun.id),
            )
            .where(DungeonRun.keystone_level >= args.min_key)
            .group_by(DungeonRun.keystone_level)
            .order_by(DungeonRun.keystone_level)
        ))
        total_high = sum(cnt for _, cnt in key_dist)
        print(f"\n=== Key Level Distribution (>= +{args.min_key}) ===")
        print(f"Total runs: {total_high}")
        for level, cnt in key_dist:
            bar = "#" * min(60, cnt // max(1, total_high // 60))
            print(f"  +{level:>2}: {cnt:>5} {bar}")

        # Overall DB stats for context
        total_runs = session.scalar(select(func.count(DungeonRun.id)))
        total_players = session.scalar(select(func.count(Player.id)))
        total_scores = session.scalar(select(func.count(PlayerScore.id)))
        max_key = session.scalar(select(func.max(DungeonRun.keystone_level)))
        print(f"\nDB totals: {total_runs} runs, {total_players} players, {total_scores} scores, max key: +{max_key}")

        # Pull high-key runs
        q = (
            select(DungeonRun)
            .where(DungeonRun.keystone_level >= args.min_key)
            .order_by(DungeonRun.keystone_level.desc())
        )
        if args.limit:
            q = q.limit(args.limit)
        runs = list(session.execute(q).scalars())

        if not runs:
            print("No runs found at that key level.")
            return 0

        # Score each run individually and collect per-category scores
        brackets = defaultdict(lambda: defaultdict(list))  # bracket -> category -> [scores]
        role_brackets = defaultdict(lambda: defaultdict(list))  # (bracket, role) -> category -> [scores]
        composite_by_bracket = defaultdict(list)
        grade_by_bracket = defaultdict(list)

        for run in runs:
            player = session.get(Player, run.player_id)
            class_id = player.class_id if player else None

            try:
                result = score_player_runs(
                    [run], run.role, class_id=class_id, select_runs=False,
                )
            except Exception:
                continue

            # Bucket into brackets: 20-22, 23-25, 26-28, 29+
            if run.keystone_level >= 29:
                bracket = "29+"
            elif run.keystone_level >= 26:
                bracket = "26-28"
            elif run.keystone_level >= 23:
                bracket = "23-25"
            else:
                bracket = "20-22"

            composite_by_bracket[bracket].append(result.composite_score)
            grade_by_bracket[bracket].append(result.overall_grade)

            for cat, score in result.category_scores.items():
                if cat in ("timing_modifier", "damage_output_ilvl", "aug_uplift_score"):
                    continue
                brackets[bracket][cat].append(score)
                role_brackets[(bracket, run.role.value)][cat].append(score)

        # Report
        for bracket in ["20-22", "23-25", "26-28", "29+"]:
            if bracket not in composite_by_bracket:
                continue

            composites = composite_by_bracket[bracket]
            grades = grade_by_bracket[bracket]

            print(f"\n{'='*70}")
            print(f"  BRACKET: +{bracket}  ({len(composites)} runs)")
            print(f"{'='*70}")

            print_distribution("COMPOSITE", composites)

            # Grade distribution
            from collections import Counter
            gc = Counter(grades)
            grade_order = ["S+", "S", "A+", "A", "A-", "B+", "B", "B-",
                          "C+", "C", "C-", "D+", "D", "D-", "F", "F-"]
            grade_str = "  Grades: " + ", ".join(
                f"{g}={gc[g]}" for g in grade_order if gc[g] > 0
            )
            print(grade_str)

            for cat in ["damage_output", "utility", "survivability",
                       "cooldown_usage", "casts_per_minute", "healing_throughput"]:
                if cat in brackets[bracket]:
                    print_distribution(cat, brackets[bracket][cat])

            # Per-role breakdown
            for role_name in ["dps", "tank", "healer"]:
                key = (bracket, role_name)
                if key not in role_brackets:
                    continue
                role_data = role_brackets[key]
                n_role = len(role_data.get("damage_output", role_data.get("healing_throughput", [])))
                if n_role == 0:
                    continue
                print(f"\n  --- {role_name.upper()} ({n_role} runs) ---")
                for cat in ["damage_output", "utility", "survivability",
                           "cooldown_usage", "casts_per_minute", "healing_throughput"]:
                    if cat in role_data:
                        print_distribution(cat, role_data[cat])

        # Also show raw metric distributions for high-key runs
        print(f"\n{'='*70}")
        print(f"  RAW METRICS (all runs >= +{args.min_key})")
        print(f"{'='*70}")

        deaths = sorted([r.deaths for r in runs])
        dps_pcts = sorted([r.dps for r in runs if 0 <= r.dps <= 100])
        cpm_vals = sorted([
            r.casts_total / max(1, r.duration / 60000)
            for r in runs if r.casts_total > 0 and r.duration > 0
        ])
        cd_pcts = sorted([r.cooldown_usage_pct for r in runs])
        interrupts = sorted([r.interrupts for r in runs])
        avoidable_ratios = sorted([
            r.avoidable_damage_taken / r.damage_taken_total * 100
            for r in runs
            if r.damage_taken_total > 0 and r.avoidable_damage_taken > 0
        ])

        print_distribution("deaths", [float(d) for d in deaths])
        print_distribution("dps_percentile (WCL)", dps_pcts)
        print_distribution("casts_per_minute", cpm_vals)
        print_distribution("cooldown_usage_pct", cd_pcts)
        print_distribution("interrupts", [float(i) for i in interrupts])
        if avoidable_ratios:
            print_distribution("avoidable_dmg_ratio %", avoidable_ratios)

        # Timed rate by bracket
        print(f"\n  Timing rate by bracket:")
        for bracket in ["20-22", "23-25", "26-28", "29+"]:
            bracket_runs = [
                r for r in runs
                if (r.keystone_level >= 29 and bracket == "29+")
                or (26 <= r.keystone_level <= 28 and bracket == "26-28")
                or (23 <= r.keystone_level <= 25 and bracket == "23-25")
                or (20 <= r.keystone_level <= 22 and bracket == "20-22")
            ]
            if not bracket_runs:
                continue
            timed = sum(1 for r in bracket_runs if r.timed)
            print(f"    +{bracket}: {timed}/{len(bracket_runs)} timed ({timed*100/len(bracket_runs):.1f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
