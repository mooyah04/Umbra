"""Simulate the impact of the survivability scoring changes.

Compares old vs new scoring for specific run data points to validate
the recalibration produces sensible results.

Usage:
  cd backend
  python -m scripts.simulate_scoring_impact
"""
import sys


def old_avoidable_score(avoidable_ratio: float) -> float:
    return max(0, 100 - avoidable_ratio * 300)


def new_avoidable_score(avoidable_ratio: float) -> float:
    if avoidable_ratio <= 0.15:
        return 100.0
    if avoidable_ratio >= 0.80:
        return 15.0
    return 100.0 - (avoidable_ratio - 0.15) / 0.65 * 85.0


def old_death_score(deaths: int, avoidable_deaths: int = 0) -> float:
    if deaths == 0: base = 100
    elif deaths == 1: base = 80
    elif deaths == 2: base = 55
    elif deaths == 3: base = 30
    elif deaths == 4: base = 10
    else: base = 0
    if avoidable_deaths > 0 and deaths > 0:
        base = max(0, base - min(base, avoidable_deaths * 10))
    return base


def new_death_score(deaths: int, keystone_level: int, avoidable_deaths: int = 0) -> float:
    if deaths == 0: base = 100
    elif deaths == 1: base = 80
    elif deaths == 2: base = 55
    elif deaths == 3: base = 30
    elif deaths == 4: base = 10
    else: base = 0
    if avoidable_deaths > 0 and deaths > 0:
        base = max(0, base - min(base, avoidable_deaths * 10))
    ks_lenience = min(10, max(0, keystone_level - 12))
    return min(100, base + ks_lenience)


def old_hrps_score(hrps: float, keystone_level: int) -> float:
    level_mult = 1.0 + max(0, keystone_level - 2) * 0.15
    if hrps < 2000 * level_mult: return 100
    elif hrps < 5000 * level_mult:
        return 90 - ((hrps - 2000 * level_mult) / (3000 * level_mult)) * 30
    elif hrps < 10000 * level_mult:
        return 60 - ((hrps - 5000 * level_mult) / (5000 * level_mult)) * 40
    else:
        return max(0, 20 - ((hrps - 10000 * level_mult) / (10000 * level_mult)) * 20)


def new_hrps_score(hrps: float, keystone_level: int) -> float:
    level_mult = 1.0 + max(0, keystone_level - 2) * 0.18
    if hrps < 2000 * level_mult: return 100
    elif hrps < 5000 * level_mult:
        return 90 - ((hrps - 2000 * level_mult) / (3000 * level_mult)) * 30
    elif hrps < 10000 * level_mult:
        return 60 - ((hrps - 5000 * level_mult) / (5000 * level_mult)) * 40
    else:
        return max(0, 20 - ((hrps - 10000 * level_mult) / (10000 * level_mult)) * 20)


def survivability(death: float, avoidable: float, healing: float) -> float:
    return death * 0.50 + avoidable * 0.25 + healing * 0.25


def main():
    print("=" * 90)
    print("SURVIVABILITY SCORING IMPACT SIMULATION")
    print("=" * 90)

    # Real player data from prod API
    cases = [
        {
            "name": "Sahneblyat (DPS #3, Unholy DK)",
            "keystone": 20, "deaths": 1, "avoidable_deaths": 0,
            "avoidable_ratio": 17737275 / 45214002,
            "hrps": 45127008 / (1861595 / 1000),
            "role_weight": 0.25,
            "old_composite": 87.7,
        },
        {
            "name": "Bahner (DPS #2, Subtlety Rogue)",
            "keystone": 17, "deaths": 0, "avoidable_deaths": 0,
            "avoidable_ratio": 13693572 / 28053332,
            "hrps": 28274696 / (1751444 / 1000),
            "role_weight": 0.25,
            "old_composite": 89.3,
        },
        {
            "name": "Sahneblyat +18 timed (0 deaths)",
            "keystone": 18, "deaths": 0, "avoidable_deaths": 0,
            "avoidable_ratio": 15181090 / 34291706,
            "hrps": 37281407 / (1864339 / 1000),
            "role_weight": 0.25,
            "old_composite": 87.7,
        },
        {
            "name": "Simulated +25 run (1 death, 55% avoidable)",
            "keystone": 25, "deaths": 1, "avoidable_deaths": 0,
            "avoidable_ratio": 0.55,
            "hrps": 30000,
            "role_weight": 0.25,
            "old_composite": None,
        },
        {
            "name": "Simulated +25 run (2 deaths, 60% avoidable)",
            "keystone": 25, "deaths": 2, "avoidable_deaths": 0,
            "avoidable_ratio": 0.60,
            "hrps": 35000,
            "role_weight": 0.25,
            "old_composite": None,
        },
        {
            "name": "Simulated +28 run (1 death, 65% avoidable)",
            "keystone": 28, "deaths": 1, "avoidable_deaths": 0,
            "avoidable_ratio": 0.65,
            "hrps": 40000,
            "role_weight": 0.25,
            "old_composite": None,
        },
    ]

    for c in cases:
        ks = c["keystone"]
        print(f"\n--- {c['name']} (key +{ks}) ---")

        od = old_death_score(c["deaths"], c["avoidable_deaths"])
        nd = new_death_score(c["deaths"], ks, c["avoidable_deaths"])
        oa = old_avoidable_score(c["avoidable_ratio"])
        na = new_avoidable_score(c["avoidable_ratio"])
        oh = old_hrps_score(c["hrps"], ks)
        nh = new_hrps_score(c["hrps"], ks)

        os_val = survivability(od, oa, oh)
        ns_val = survivability(nd, na, nh)
        delta = ns_val - os_val

        print(f"  {'Component':<20s} {'OLD':>8s} {'NEW':>8s} {'Delta':>8s}")
        print(f"  {'deaths':20s} {od:8.1f} {nd:8.1f} {nd-od:+8.1f}")
        print(f"  {'avoidable ({:.0%})'.format(c['avoidable_ratio']):20s} {oa:8.1f} {na:8.1f} {na-oa:+8.1f}")
        print(f"  {'healing burden':20s} {oh:8.1f} {nh:8.1f} {nh-oh:+8.1f}")
        print(f"  {'SURVIVABILITY':20s} {os_val:8.1f} {ns_val:8.1f} {delta:+8.1f}")

        if c["old_composite"] is not None:
            composite_delta = delta * c["role_weight"]
            new_comp = c["old_composite"] + composite_delta
            print(f"  Composite impact: {c['old_composite']:.1f} -> {new_comp:.1f} ({composite_delta:+.1f})")

    # Avoidable ratio curve comparison
    print(f"\n{'='*90}")
    print("AVOIDABLE RATIO CURVE: OLD vs NEW")
    print(f"{'='*90}")
    print(f"  {'Ratio':>8s}  {'OLD':>8s}  {'NEW':>8s}  {'Delta':>8s}")
    for pct in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]:
        ratio = pct / 100
        o = old_avoidable_score(ratio)
        n = new_avoidable_score(ratio)
        marker = ""
        if 55 <= pct <= 65:
            marker = "  <- top-log range"
        elif 35 <= pct <= 50:
            marker = "  <- top-player per-run range"
        print(f"  {pct:>7d}%  {o:8.1f}  {n:8.1f}  {n-o:+8.1f}{marker}")

    # Death penalty curve by key level
    print(f"\n{'='*90}")
    print("DEATH PENALTY: 1 DEATH at various key levels")
    print(f"{'='*90}")
    print(f"  {'Key':>5s}  {'OLD':>8s}  {'NEW':>8s}  {'Lenience':>8s}")
    for ks in [5, 10, 12, 14, 16, 18, 20, 22, 25, 28]:
        o = old_death_score(1)
        n = new_death_score(1, ks)
        print(f"  +{ks:>3d}   {o:8.1f}  {n:8.1f}  {n-o:+8.1f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
