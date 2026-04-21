"""Sample real Augmentation Evoker uplift values from top WCL logs so
we can calibrate the scoring curve against real data instead of
guessing thresholds.

For each top Aug on the requested dungeon encounter:
  1. Resolve source IDs for the Aug and their 4 teammates.
  2. Run compute_uplift to produce total uplift damage.
  3. Print uplift DPS, uplift as % of group damage, and per-buff split.

Usage:
    python -m scripts.validate_aug_uplift
    python -m scripts.validate_aug_uplift --encounter 12811 --limit 10
"""
from __future__ import annotations

import argparse

from app.pipeline.aug_uplift import compute_uplift
from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client


DEFAULT_ENCOUNTER = 12811  # Magister's Terrace — Midnight S1
DEFAULT_LIMIT = 10

# All 8 Midnight S1 encounter IDs, newest to oldest intro order.
ALL_MIDNIGHT_S1_ENCOUNTERS: list[tuple[int, str]] = [
    (12811, "Magister's Terrace"),
    (12805, "Windrunner Spire"),
    (12874, "Maisara Caverns"),
    (12915, "Nexus-Point Xenas"),
    (10658, "Pit of Saron"),
    (61209, "Skyreach"),
    (112526, "Algeth'ar Academy"),
    (361753, "The Seat of the Triumvirate"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encounter", type=int, default=DEFAULT_ENCOUNTER)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument(
        "--all-dungeons",
        action="store_true",
        help="Iterate over all 8 Midnight S1 dungeons instead of a single encounter.",
    )
    args = parser.parse_args()

    if args.all_dungeons:
        return _run_all_dungeons(args.limit)
    return _run_single(args.encounter, args.limit)


def _run_all_dungeons(limit_per: int) -> int:
    """Iterate over the full Midnight S1 pool and report an aggregate
    distribution — used to recalibrate the scoring thresholds against
    a multi-dungeon sample instead of a single-encounter window.
    """
    all_dps: list[float] = []
    all_pct: list[float] = []
    by_encounter: list[tuple[str, list[float]]] = []

    for encounter_id, name in ALL_MIDNIGHT_S1_ENCOUNTERS:
        print(f"\n===== {name} (id={encounter_id}) — top {limit_per} =====")
        # Capture the per-encounter list for the summary.
        before_len = len(all_dps)
        rc = _run_single(encounter_id, limit_per, aggregate_dps=all_dps, aggregate_pct=all_pct)
        after = all_dps[before_len:]
        by_encounter.append((name, after))
        if rc != 0:
            print(f"  (encounter {encounter_id} errored — skipping in aggregate)")

    if not all_dps:
        print("\nNo uplift samples collected.")
        return 1

    print("\n\n===== AGGREGATE across all 8 Midnight S1 dungeons =====")
    sorted_dps = sorted(all_dps)
    sorted_pct = sorted(all_pct)
    n = len(sorted_dps)
    def pct(arr, p):
        idx = max(0, min(n - 1, int(round(p / 100 * (n - 1)))))
        return arr[idx]
    print(f"  samples: {n}")
    print(f"  uplift DPS  min={sorted_dps[0]/1000:.0f}k  "
          f"p10={pct(sorted_dps, 10)/1000:.0f}k  "
          f"p25={pct(sorted_dps, 25)/1000:.0f}k  "
          f"p50={pct(sorted_dps, 50)/1000:.0f}k  "
          f"p75={pct(sorted_dps, 75)/1000:.0f}k  "
          f"p90={pct(sorted_dps, 90)/1000:.0f}k  "
          f"max={sorted_dps[-1]/1000:.0f}k")
    print(f"  uplift %    min={sorted_pct[0]:.1f}%  "
          f"p25={pct(sorted_pct, 25):.1f}%  "
          f"p50={pct(sorted_pct, 50):.1f}%  "
          f"p75={pct(sorted_pct, 75):.1f}%  "
          f"max={sorted_pct[-1]:.1f}%")

    print("\n  per-dungeon p50 uplift DPS:")
    for name, samples in by_encounter:
        if not samples:
            print(f"    {name:35s}  no samples")
            continue
        s = sorted(samples)
        mid = s[len(s) // 2]
        print(f"    {name:35s}  n={len(s):2d}  p50={mid/1000:5.0f}k  "
              f"min={s[0]/1000:4.0f}k  max={s[-1]/1000:4.0f}k")

    return 0


def _run_single(
    encounter_id: int,
    limit: int,
    aggregate_dps: list[float] | None = None,
    aggregate_pct: list[float] | None = None,
) -> int:
    """Sample top N Augs for a single encounter. When aggregate lists
    are provided (multi-dungeon mode), appends each sample's metrics
    to the lists for later rollup."""
    print(
        f"\n=== Aug uplift sampler: top {limit} Augs on encounter "
        f"{encounter_id} ===\n"
    )

    try:
        top = wcl_client.get_top_characters_for_spec(
            encounter_id=encounter_id,
            class_name="Evoker",
            spec_name="Augmentation",
            metric="dps",
            limit=limit,
        )
    except (WCLQueryError, WCLRateLimitedError) as e:
        print(f"WCL query failed: {e}")
        return 2

    if not top:
        print("No rankings returned — check encounter ID.")
        return 1

    all_uplift_dps: list[float] = []
    all_uplift_pct: list[float] = []

    for idx, entry in enumerate(top, start=1):
        name = entry["name"]
        report_code = entry["report_code"]
        fight_id = entry["fight_id"]
        print(f"[{idx}] {name} — {report_code} fight {fight_id}")

        # Resolve actor IDs and fight timing.
        try:
            header = wcl_client.get_report_header_and_fights(report_code)
        except (WCLQueryError, WCLRateLimitedError) as e:
            print(f"    header fetch failed: {e}")
            continue

        fights = header.get("fights", [])
        fight = next((f for f in fights if f.get("id") == fight_id), None)
        if not fight:
            print(f"    fight {fight_id} not found in report")
            continue
        fight_start_ms = int(fight.get("startTime") or 0)
        fight_end_ms = int(fight.get("endTime") or 0)
        duration_s = max(1.0, (fight_end_ms - fight_start_ms) / 1000.0)

        actors_by_name = header.get("actors_by_name", {}) or {}
        aug_ids = actors_by_name.get(name) or []
        if not aug_ids:
            print(f"    {name!r} not in actor list")
            continue
        aug_source_id = aug_ids[0]

        friendly_players = set(fight.get("friendlyPlayers") or [])
        teammate_ids = [pid for pid in friendly_players if pid != aug_source_id]

        try:
            result = compute_uplift(
                report_code=report_code,
                fight_id=fight_id,
                aug_source_id=aug_source_id,
                fight_end_ms=fight_end_ms,
                teammate_source_ids=teammate_ids,
            )
        except Exception as e:
            print(f"    uplift compute failed: {e}")
            continue

        uplift = result["total_uplift_damage"]
        uplift_dps = uplift / duration_s
        all_uplift_dps.append(uplift_dps)
        if aggregate_dps is not None:
            aggregate_dps.append(uplift_dps)

        # Fetch teammates' total damage for context (% of group damage).
        total_group_dmg = 0.0
        for tid in teammate_ids:
            try:
                evs = wcl_client.get_player_events(
                    report_code, [fight_id], data_type="DamageDone", source_id=tid
                )
            except Exception:
                continue
            total_group_dmg += sum(
                ev.get("amount", 0) for ev in evs
                if ev.get("type") in ("damage", "calculateddamage")
                and isinstance(ev.get("amount"), (int, float))
            )
        uplift_pct = (uplift / total_group_dmg * 100.0) if total_group_dmg > 0 else 0.0
        all_uplift_pct.append(uplift_pct)
        if aggregate_pct is not None:
            aggregate_pct.append(uplift_pct)

        print(f"    duration: {duration_s:.0f}s · group dmg: {total_group_dmg/1e6:.1f}M")
        print(f"    uplift damage: {uplift/1e6:.1f}M ({uplift_dps/1000:.0f}k DPS)")
        print(f"    uplift as % of teammate damage: {uplift_pct:.1f}%")
        ebon = result["per_buff"].get(395152, 0.0)
        pres = result["per_buff"].get(409311, 0.0)
        print(f"    per-buff split: Ebon Might={ebon/1e6:.1f}M  Prescience={pres/1e6:.1f}M")
        print()

    if all_uplift_dps:
        sorted_dps = sorted(all_uplift_dps)
        sorted_pct = sorted(all_uplift_pct)
        n = len(sorted_dps)
        def pct(arr, p):
            if not arr: return 0
            idx = max(0, min(n - 1, int(round(p / 100 * (n - 1)))))
            return arr[idx]
        print("=== Distribution across top Augs ===")
        print(f"  uplift DPS:  min={sorted_dps[0]/1000:.0f}k  "
              f"p25={pct(sorted_dps, 25)/1000:.0f}k  "
              f"p50={pct(sorted_dps, 50)/1000:.0f}k  "
              f"p75={pct(sorted_dps, 75)/1000:.0f}k  "
              f"max={sorted_dps[-1]/1000:.0f}k")
        print(f"  uplift %:    min={sorted_pct[0]:.1f}%  "
              f"p25={pct(sorted_pct, 25):.1f}%  "
              f"p50={pct(sorted_pct, 50):.1f}%  "
              f"p75={pct(sorted_pct, 75):.1f}%  "
              f"max={sorted_pct[-1]:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
