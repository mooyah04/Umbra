"""Sample top WCL logs to see what high-key performance actually looks like.

Pulls top-ranked M+ logs from WCL for each active-season dungeon,
fetches per-fight details (deaths, damage taken, avoidable damage,
casts, interrupts, etc.) and reports distributions so we can calibrate
scoring thresholds against real data.

Usage:
  cd backend
  python -m scripts.sample_high_key_logs
  python -m scripts.sample_high_key_logs --logs-per-dungeon 10
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass

from app.scoring.dungeons.registry import (
    _DUNGEONS,
    get_avoidable_abilities,
    UNIVERSAL_AVOIDABLE,
)
from app.wcl.client import WCLClient, WCLQueryError


@dataclass
class RunSample:
    dungeon: str
    keystone_level: int | None
    report_code: str
    fight_id: int
    duration_ms: int
    deaths: int
    total_damage_taken: float
    avoidable_damage_taken: float
    avoidable_ratio: float
    healing_received: float
    casts_total: int
    interrupts: int
    role: str
    spec: str
    player_name: str


def percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * pct / 100)
    return sorted_vals[min(idx, len(sorted_vals) - 1)]


def print_dist(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label}: no data")
        return
    values.sort()
    print(
        f"  {label:>25s}  n={len(values):>3}  "
        f"p10={percentile(values, 10):>8.1f}  "
        f"p25={percentile(values, 25):>8.1f}  "
        f"p50={percentile(values, 50):>8.1f}  "
        f"p75={percentile(values, 75):>8.1f}  "
        f"p90={percentile(values, 90):>8.1f}"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-per-dungeon", type=int, default=5,
                        help="Top logs to sample per dungeon (default 5)")
    args = parser.parse_args()

    client = WCLClient()
    all_samples: list[RunSample] = []

    for eid, dungeon in _DUNGEONS.items():
        print(f"\n--- {dungeon.name} (encounter {eid}) ---")
        avoidable_ids = get_avoidable_abilities(eid)

        try:
            top_logs = client.get_top_logs_for_encounter(
                eid, metric="speed", limit=args.logs_per_dungeon
            )
        except WCLQueryError as e:
            print(f"  SKIP: {e}")
            continue

        if not top_logs:
            print("  No logs found")
            continue

        for log in top_logs:
            code = log["report_code"]
            fid = log["fight_id"]
            ks = log.get("keystone_level")
            duration = log.get("duration", 0)

            print(f"  Log {code}/{fid} (key +{ks}, {duration/1000:.0f}s)")

            # Get fight details: deaths, damage taken, casts, interrupts
            try:
                fight_data = client.get_report_fights(code)
            except WCLQueryError:
                print("    SKIP: can't fetch fights")
                continue

            target_fight = None
            for f in fight_data:
                if f.get("id") == fid:
                    target_fight = f
                    break

            if not target_fight:
                print("    SKIP: fight not found")
                continue

            fight_deaths = target_fight.get("friendlyPlayers", [])

            # Get player details from this fight
            try:
                player_data = client.query("""
                query($code: String!, $fightIDs: [Int!]!) {
                  reportData {
                    report(code: $code) {
                      playerDetails(fightIDs: $fightIDs)
                      table(dataType: Summary, fightIDs: $fightIDs)
                      damageTaken: table(dataType: DamageTaken, fightIDs: $fightIDs, viewBy: Ability)
                    }
                  }
                }
                """, {"code": code, "fightIDs": [fid]})
            except WCLQueryError as e:
                print(f"    SKIP: {e}")
                continue

            report = player_data.get("reportData", {}).get("report", {})

            # Parse damage taken by ability to calculate avoidable ratio
            dmg_taken_table = report.get("damageTaken", {}).get("data", {}).get("entries", [])
            total_dmg = sum(e.get("total", 0) for e in dmg_taken_table)
            avoidable_dmg = sum(
                e.get("total", 0) for e in dmg_taken_table
                if e.get("guid") in avoidable_ids
            )
            ratio = avoidable_dmg / total_dmg if total_dmg > 0 else 0

            # Parse summary table for group-level stats
            summary = report.get("table", {}).get("data", {})
            total_deaths = 0
            if isinstance(summary, dict):
                total_deaths = summary.get("totalDeaths", 0) or 0
            elif isinstance(summary, list):
                for item in summary:
                    if isinstance(item, dict):
                        total_deaths += item.get("totalDeaths", 0) or 0

            total_casts = 0
            total_interrupts = 0
            total_healing_received = 0

            avoidable_names = [name for _, name in dungeon.avoidable_abilities] + \
                             [name for _, name in UNIVERSAL_AVOIDABLE]

            print(f"    Deaths: {total_deaths}, Duration: {duration/1000:.0f}s, Key: +{ks}")
            print(f"    Total DMG taken: {total_dmg/1e6:.1f}M, Avoidable: {avoidable_dmg/1e6:.1f}M ({ratio*100:.1f}%)")
            if dmg_taken_table:
                top_avoidable = sorted(
                    [e for e in dmg_taken_table if e.get("guid") in avoidable_ids],
                    key=lambda e: e.get("total", 0),
                    reverse=True
                )[:3]
                for e in top_avoidable:
                    print(f"      Avoidable: {e.get('name', '?'):30s} {e.get('total',0)/1e6:.1f}M")

            all_samples.append(RunSample(
                dungeon=dungeon.name,
                keystone_level=ks,
                report_code=code,
                fight_id=fid,
                duration_ms=duration,
                deaths=total_deaths,
                total_damage_taken=total_dmg,
                avoidable_damage_taken=avoidable_dmg,
                avoidable_ratio=ratio,
                healing_received=total_healing_received,
                casts_total=total_casts,
                interrupts=total_interrupts,
                role="mixed",
                spec="mixed",
                player_name="group",
            ))

    if not all_samples:
        print("\nNo samples collected.")
        return 0

    # Aggregate report
    print(f"\n{'='*70}")
    print(f"  AGGREGATE: {len(all_samples)} top logs across {len(_DUNGEONS)} dungeons")
    print(f"{'='*70}")

    ks_levels = [s.keystone_level for s in all_samples if s.keystone_level]
    if ks_levels:
        ks_levels.sort()
        print(f"\n  Key levels: min=+{min(ks_levels)}, max=+{max(ks_levels)}, "
              f"median=+{ks_levels[len(ks_levels)//2]}")
        print(f"  Distribution: {', '.join(f'+{k}' for k in ks_levels)}")

    print_dist("deaths (group total)", [float(s.deaths) for s in all_samples])
    print_dist("avoidable_ratio %", [s.avoidable_ratio * 100 for s in all_samples])
    print_dist("total_dmg_taken (M)", [s.total_damage_taken / 1e6 for s in all_samples])
    print_dist("avoidable_dmg (M)", [s.avoidable_damage_taken / 1e6 for s in all_samples])

    dur_min = [s.duration_ms / 60000 for s in all_samples if s.duration_ms > 0]
    print_dist("duration (min)", dur_min)

    # Per-dungeon breakdown
    by_dungeon = defaultdict(list)
    for s in all_samples:
        by_dungeon[s.dungeon].append(s)

    print(f"\n  Per-dungeon avoidable ratios:")
    for dname, samples in sorted(by_dungeon.items()):
        ratios = [s.avoidable_ratio * 100 for s in samples]
        ratios.sort()
        ks = [s.keystone_level for s in samples if s.keystone_level]
        avg_ratio = sum(ratios) / len(ratios)
        ks_str = f"+{min(ks)}-{max(ks)}" if ks else "?"
        print(f"    {dname:30s} keys {ks_str:>8s}  avg avoidable: {avg_ratio:5.1f}%  "
              f"range: {ratios[0]:.1f}-{ratios[-1]:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
