"""CPM (casts-per-minute) benchmarks per role, with optional spec overrides.

Why this file exists separately: raw CPM benchmarks vary hugely by role and spec.
A 25 CPM number means "below average" for a Fury Warrior and "crushing it" for a
Restoration Druid. Keeping benchmarks in a dedicated module lets us tune them
without touching scoring logic, and gives a clean extension point for spec-level
tuning once we have live sampling data.

Benchmarks are expressed as (poor, fair, good, excellent) CPM thresholds.
Scoring interpolates linearly:
  cpm <= poor        -> 0
  poor < cpm <= fair -> 0..50
  fair < cpm <= good -> 50..80
  good < cpm <= exc  -> 80..100
  cpm > excellent    -> 100
"""

from dataclasses import dataclass

from app.models import Role


@dataclass(frozen=True)
class CPMBenchmark:
    poor: float       # at/below this = 0
    fair: float       # scales 0 -> 50
    good: float       # scales 50 -> 80
    excellent: float  # scales 80 -> 100; above = 100


# Role-level defaults. Tuned from live Midnight S1 data (2026-04-16 audit
# against Elonmunk/Dobbermon runs + community baselines). Prior values had
# every player pegging at 100 — the category gave zero signal. Thresholds
# now sit above observed p50 but below observed p90 for each role.
ROLE_BENCHMARKS: dict[Role, CPMBenchmark] = {
    # DPS baseline assumes a mid-pack spec (e.g. Frost Mage, Ret Paladin).
    # Extreme specs (Fury, MM Hunter) should live in SPEC_BENCHMARKS below.
    Role.dps: CPMBenchmark(poor=10, fair=18, good=26, excellent=35),

    # Healers cast heal spells continuously but the rate is lower than DPS.
    # Observed live range for top healers: 30-50 CPM — bumped from 28 to 36
    # excellent so "top 15% only" gates 100. Prior value saturated Dobbermon
    # on every run.
    Role.healer: CPMBenchmark(poor=10, fair=18, good=26, excellent=36),

    # Tanks spam mitigation + builder/spender; GCD-locked rotations.
    Role.tank: CPMBenchmark(poor=12, fair=20, good=28, excellent=36),
}


# Spec-specific overrides. Keyed by spec_name (matches DungeonRun.spec_name).
# Start with known outliers; grow with data. Missing specs fall back to role benchmark.
SPEC_BENCHMARKS: dict[str, CPMBenchmark] = {
    # High-CPM melee DPS
    "Fury": CPMBenchmark(poor=20, fair=32, good=42, excellent=52),
    "Outlaw": CPMBenchmark(poor=20, fair=30, good=40, excellent=50),
    "Windwalker": CPMBenchmark(poor=18, fair=28, good=38, excellent=48),
    "Feral": CPMBenchmark(poor=18, fair=28, good=38, excellent=46),

    # Low-CPM ranged DPS (slower casts, longer GCDs, or pet-heavy)
    "Marksmanship": CPMBenchmark(poor=8, fair=14, good=20, excellent=28),
    "Balance": CPMBenchmark(poor=8, fair=14, good=20, excellent=28),
    "Destruction": CPMBenchmark(poor=8, fair=14, good=20, excellent=26),
    "Beast Mastery": CPMBenchmark(poor=10, fair=16, good=22, excellent=30),

    # Unambiguous tanks.
    "Brewmaster": CPMBenchmark(poor=16, fair=26, good=38, excellent=50),
    "Vengeance": CPMBenchmark(poor=16, fair=26, good=36, excellent=46),
    "Guardian": CPMBenchmark(poor=16, fair=26, good=36, excellent=44),
    "Blood": CPMBenchmark(poor=16, fair=26, good=36, excellent=46),

    # Unambiguous healer.
    "Discipline": CPMBenchmark(poor=10, fair=16, good=22, excellent=30),
    "Mistweaver": CPMBenchmark(poor=10, fair=18, good=26, excellent=36),
    "Preservation": CPMBenchmark(poor=10, fair=18, good=26, excellent=36),
}


# Class-aware benchmarks for specs whose name alone is ambiguous. WCL returns
# spec_name as just the spec (e.g. "Protection", "Restoration"), so "Protection
# Paladin" vs "Protection Warrior" can't be disambiguated without the class id.
# Keys are (class_id, spec_name). Checked before SPEC_BENCHMARKS.
CLASS_SPEC_BENCHMARKS: dict[tuple[int, str], CPMBenchmark] = {
    # Protection: class 1 = Warrior, class 2 = Paladin.
    (1, "Protection"): CPMBenchmark(poor=16, fair=26, good=36, excellent=44),
    (2, "Protection"): CPMBenchmark(poor=14, fair=22, good=30, excellent=38),
    # Holy: class 2 = Paladin healer, class 5 = Priest healer.
    (2, "Holy"): CPMBenchmark(poor=10, fair=18, good=26, excellent=34),
    (5, "Holy"): CPMBenchmark(poor=10, fair=18, good=26, excellent=34),
    # Restoration: class 7 = Shaman, class 11 = Druid. Both observed 30-50 CPM
    # live; re-anchored at 42 excellent to match what top healers actually do
    # (prior single-entry 26 was pegging every run at 100).
    (7, "Restoration"): CPMBenchmark(poor=10, fair=22, good=32, excellent=42),
    (11, "Restoration"): CPMBenchmark(poor=10, fair=22, good=32, excellent=42),
    # Frost: class 6 = DK (melee), class 8 = Mage (ranged caster). Completely
    # different rotations — DK hits ~30 CPM, Mage ~25.
    (6, "Frost"): CPMBenchmark(poor=12, fair=22, good=30, excellent=38),
    (8, "Frost"): CPMBenchmark(poor=10, fair=18, good=25, excellent=32),
}


def get_benchmark(
    role: Role,
    spec_name: str | None = None,
    class_id: int | None = None,
) -> CPMBenchmark:
    """Return the tightest-matching benchmark.

    Resolution order (first hit wins):
      1. (class_id, spec_name) in CLASS_SPEC_BENCHMARKS — disambiguates
         same-spec-different-class pairs (Protection Warrior vs Paladin,
         Restoration Druid vs Shaman, etc.)
      2. spec_name in SPEC_BENCHMARKS — covers unambiguous specs (Fury,
         Outlaw, Brewmaster, Discipline...).
      3. ROLE_BENCHMARKS[role] — default.
    """
    if class_id is not None and spec_name and (class_id, spec_name) in CLASS_SPEC_BENCHMARKS:
        return CLASS_SPEC_BENCHMARKS[(class_id, spec_name)]
    if spec_name and spec_name in SPEC_BENCHMARKS:
        return SPEC_BENCHMARKS[spec_name]
    return ROLE_BENCHMARKS[role]


def score_cpm(cpm: float, benchmark: CPMBenchmark) -> float:
    """Map a raw CPM value to a 0-100 score using the benchmark thresholds."""
    if cpm <= benchmark.poor:
        return 0.0
    if cpm <= benchmark.fair:
        span = max(1e-6, benchmark.fair - benchmark.poor)
        return ((cpm - benchmark.poor) / span) * 50.0
    if cpm <= benchmark.good:
        span = max(1e-6, benchmark.good - benchmark.fair)
        return 50.0 + ((cpm - benchmark.fair) / span) * 30.0
    if cpm <= benchmark.excellent:
        span = max(1e-6, benchmark.excellent - benchmark.good)
        return 80.0 + ((cpm - benchmark.good) / span) * 20.0
    return 100.0
