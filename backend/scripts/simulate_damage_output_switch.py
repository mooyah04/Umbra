"""Sitewide impact sim: switch damage_output from WCL zoneRankings
"overall" (un-bracketed, best-parse-per-dungeon) to the key-bracketed
per-run weighted average the engine already computes (_score_damage_output).

Both sides run through the CURRENT engine and differ in exactly one input:
  baseline  — zone_dps_percentile passed (today's live behavior; the
              engine.py:782 override uses it for damage_output)
  proposed  — zone_dps_percentile=None, so the engine falls through to
              _score_damage_output, a key-level-weighted average of each
              run's bracketed rankPercent (stored on DungeonRun.dps).

That isolates the grade movement attributable to the switch alone — no
WCL calls, no cooldown/weight changes mixed in. Read-only; never writes.

Run against PROD data (local DB is the dev stub):
  railway run python -m scripts.simulate_damage_output_switch
or point DATABASE_URL at prod and:
  python -m scripts.simulate_damage_output_switch [--role dps|healer|tank] [--limit N]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore, Role


GRADE_ORDER = [
    "S+", "S", "S-", "A+", "A", "A-", "B+", "B", "B-",
    "C+", "C", "C-", "D+", "D", "D-", "F+", "F", "F-",
]
GRADE_RANK = {g: i for i, g in enumerate(GRADE_ORDER)}


def _zone_pct_or_none(existing, key: str) -> float | None:
    """Stored zone percentile, treating the engine's 0.0 excluded-category
    placeholder as None (mirrors scripts/impact_report.py)."""
    if not existing:
        return None
    v = existing.category_scores.get(key)
    if v is None or v == 0.0:
        return None
    return v


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["dps", "healer", "tank"], default=None,
                        help="Limit to one role (default: all)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap players processed (debug)")
    args = parser.parse_args()

    # Import here so a bad DATABASE_URL surfaces clearly above the import.
    from app.scoring.engine import score_player_runs

    role_filter = Role(args.role) if args.role else None

    rows: list[dict] = []
    with SessionLocal() as session:
        scores = list(session.execute(select(PlayerScore)).scalars())
        print(f"Graded PlayerScore rows in DB: {len(scores)}")

        for ps in scores:
            if role_filter and ps.role != role_filter:
                continue
            if args.limit and len(rows) >= args.limit:
                break

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

            zone_dps = _zone_pct_or_none(ps, "damage_output")
            zone_ilvl = _zone_pct_or_none(ps, "damage_output_ilvl")
            class_id = player.class_id

            try:
                base = score_player_runs(
                    role_runs, ps.role,
                    zone_dps_percentile=zone_dps,
                    zone_dps_ilvl_percentile=zone_ilvl,
                    class_id=class_id,
                )
                prop = score_player_runs(
                    role_runs, ps.role,
                    zone_dps_percentile=None,
                    zone_dps_ilvl_percentile=zone_ilvl,
                    class_id=class_id,
                )
            except Exception as e:
                print(f"  scoring error {player.name}-{player.realm}: {e}",
                      file=sys.stderr)
                continue

            rows.append({
                "name": player.name, "realm": player.realm,
                "region": player.region, "role": ps.role.value,
                "do_before": base.category_scores.get("damage_output", 0.0),
                "do_after": prop.category_scores.get("damage_output", 0.0),
                "comp_before": base.composite_score,
                "comp_after": prop.composite_score,
                "grade_before": base.overall_grade,
                "grade_after": prop.overall_grade,
            })

    _report(rows, role_filter)
    return 0


def _report(rows: list[dict], role_filter) -> None:
    label = role_filter.value if role_filter else "ALL ROLES"
    print(f"\n==== Damage Output switch impact — {label} ====")
    print(f"Players simulated: {len(rows)}")
    if not rows:
        return

    do_d = [r["do_after"] - r["do_before"] for r in rows]
    comp_d = [r["comp_after"] - r["comp_before"] for r in rows]

    print(f"\ndamage_output category delta: avg {sum(do_d)/len(do_d):+.1f}, "
          f"max {max(do_d):+.1f} / min {min(do_d):+.1f}")
    print(f"composite delta: avg {sum(comp_d)/len(comp_d):+.1f}, "
          f"max {max(comp_d):+.1f} / min {min(comp_d):+.1f}")

    moved = [r for r in rows if r["grade_before"] != r["grade_after"]]
    up = sum(1 for r in moved
             if GRADE_RANK.get(r["grade_after"], 99) < GRADE_RANK.get(r["grade_before"], 99))
    down = len(moved) - up
    print(f"\nGrade-tier moves: {len(moved)}/{len(rows)} "
          f"({100*len(moved)/len(rows):.0f}%)  — up {up}, down {down}")

    # How far grades move (tiers), e.g. S -> B is 6 tiers.
    tier_jumps = Counter()
    for r in moved:
        jump = GRADE_RANK.get(r["grade_after"], 0) - GRADE_RANK.get(r["grade_before"], 0)
        tier_jumps[jump] += 1
    print("Tier-jump distribution (− = downgrade):")
    for jump in sorted(tier_jumps):
        print(f"  {jump:+d} tiers: {tier_jumps[jump]}")

    # Most common letter transitions.
    trans = Counter((r["grade_before"], r["grade_after"]) for r in moved)
    print("Top grade transitions:")
    for (o, n), c in trans.most_common(12):
        print(f"  {o} -> {n}: {c}")

    # Worst drops (the cactue-style high-key DPS).
    biggest = sorted(rows, key=lambda r: r["comp_after"] - r["comp_before"])[:12]
    print("\nBiggest composite drops:")
    for r in biggest:
        print(f"  {r['name']}-{r['realm']} {r['region']} [{r['role']}]: "
              f"{r['grade_before']} ({r['comp_before']:.1f}) -> "
              f"{r['grade_after']} ({r['comp_after']:.1f})  "
              f"DO {r['do_before']:.0f}->{r['do_after']:.0f}")


if __name__ == "__main__":
    raise SystemExit(main())
