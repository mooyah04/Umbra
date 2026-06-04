"""Propose new GRADE_THRESHOLDS for the damage_output bracketed swap.

The swap (zone_dps_percentile -> _score_damage_output) deflates composites
sitewide. Left alone, everyone slides to B/C. This re-fits the composite->
letter cutoffs so the *share* of players in each grade stays close to
today's distribution — same grade rarity, but now earned via same-key-level
performance instead of the inflated global ranking.

Method (distribution-preserving / quantile-matched):
  1. Read every stored PlayerScore — its current letter grade defines the
     "today" distribution we want to roughly preserve.
  2. Recompute each player's composite under the swap (zone_dps=None).
  3. For each grade boundary, find the new-composite quantile that keeps
     the same cumulative share of players at-or-above that grade.

Read-only. Prints proposed thresholds + a before/after grade histogram.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore


# Best -> worst. Mirrors engine.GRADE_THRESHOLDS order.
GRADE_ORDER = [
    "S+", "S", "A+", "A", "A-", "B+", "B", "B-",
    "C+", "C", "C-", "D+", "D", "D-", "F", "F-",
]


def _zone_pct_or_none(ps, key: str) -> float | None:
    if not ps:
        return None
    v = ps.category_scores.get(key)
    if v is None or v == 0.0:
        return None
    return v


def _quantile(sorted_vals: list[float], q: float) -> float:
    """Value at quantile q in [0,1] of an ascending list."""
    if not sorted_vals:
        return 0.0
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    frac = idx - lo
    if lo + 1 >= len(sorted_vals):
        return sorted_vals[lo]
    return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--floor-spread", type=int, default=1,
                        help="Minimum composite gap between adjacent thresholds")
    args = parser.parse_args()

    from app.scoring.engine import score_player_runs

    new_composites: list[float] = []
    current_grades: list[str] = []
    per_role: dict[str, list[float]] = {"dps": [], "healer": [], "tank": []}
    simulated = 0

    with SessionLocal() as session:
        scores = list(session.execute(select(PlayerScore)).scalars())
        print(f"Stored PlayerScore rows: {len(scores)}")

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
                continue
            zone_ilvl = _zone_pct_or_none(ps, "damage_output_ilvl")
            try:
                prop = score_player_runs(
                    role_runs, ps.role,
                    zone_dps_percentile=None,
                    zone_dps_ilvl_percentile=zone_ilvl,
                    class_id=player.class_id,
                )
            except Exception as e:
                print(f"  err {player.name}: {e}", file=sys.stderr)
                continue
            new_composites.append(prop.composite_score)
            current_grades.append(ps.overall_grade)
            per_role.setdefault(ps.role.value, []).append(prop.composite_score)
            simulated += 1

    print(f"Simulated: {simulated}\n")
    if not new_composites:
        return 1

    new_sorted = sorted(new_composites)
    n = len(new_sorted)

    # --- New composite distribution (sanity check) ---
    print("New composite percentiles:")
    for p in [99, 97, 95, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5]:
        print(f"  p{p:<2} = {_quantile(new_sorted, p/100):5.1f}")

    # --- Per-role new composite distribution (fairness check) ---
    print("\nPer-role new composite (count / p90 / p50 / p10):")
    for role, vals in per_role.items():
        if not vals:
            continue
        sv = sorted(vals)
        print(f"  {role:<7} n={len(sv):4d}  p90={_quantile(sv,0.9):5.1f}  "
              f"p50={_quantile(sv,0.5):5.1f}  p10={_quantile(sv,0.1):5.1f}")

    # --- Today's grade distribution -> cumulative share at-or-above ---
    cur = Counter(current_grades)
    print("\nCurrent grade distribution:")
    for g in GRADE_ORDER:
        if cur.get(g):
            print(f"  {g:<3} {cur[g]:4d}  ({100*cur[g]/simulated:4.1f}%)")

    # Cumulative share strictly ABOVE each grade boundary, walking best->worst.
    # threshold for grade g = quantile keeping that cumulative share at-or-above.
    print("\nProposed GRADE_THRESHOLDS (distribution-preserving):")
    proposed: list[tuple[int, str]] = []
    cum_above = 0  # players in grades strictly better than current g
    prev_thr = 101
    for g in GRADE_ORDER[:-1]:  # F- is the 0 floor
        share_at_or_above = (cum_above + cur.get(g, 0)) / simulated
        q = 1.0 - share_at_or_above
        thr = _quantile(new_sorted, q)
        thr_i = int(round(thr))
        # enforce strictly decreasing with a floor spread
        if thr_i >= prev_thr:
            thr_i = prev_thr - args.floor_spread
        thr_i = max(0, thr_i)
        proposed.append((thr_i, g))
        prev_thr = thr_i
        cum_above += cur.get(g, 0)
    proposed.append((0, "F-"))

    print("GRADE_THRESHOLDS = [")
    line = "    "
    for i, (thr, g) in enumerate(proposed):
        line += f"({thr}, {g!r}), "
        if (i + 1) % 4 == 0:
            print(line.rstrip()); line = "    "
    if line.strip():
        print(line.rstrip())
    print("]")

    # --- Resulting distribution under proposed thresholds ---
    def grade_for(score: float) -> str:
        for thr, g in proposed:
            if score >= thr:
                return g
        return "F-"

    after = Counter(grade_for(c) for c in new_composites)
    print("\nGrade distribution AFTER swap + proposed thresholds:")
    print(f"  {'grade':<5}{'now':>6}{'after':>7}")
    for g in GRADE_ORDER:
        if cur.get(g) or after.get(g):
            print(f"  {g:<5}{cur.get(g,0):>6}{after.get(g,0):>7}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
