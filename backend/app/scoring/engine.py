"""Role-aware scoring engine for Umbra.

Computes a 0-100 composite score per role, then maps to a letter grade (S+ to F-).
Each role uses different category weights reflecting what matters for that role in M+.

Runs are weighted by keystone level — higher keys have more impact on the final score.
Key timing is a universal modifier applied to all roles equally.
"""

from dataclasses import dataclass
from app.models import DungeonRun, Role
from app.scoring.roles import healer_can_interrupt


# ── Grade thresholds ────────────────────────────────────────────────────────

GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (95, "S+"), (90, "S"),  (85, "A+"), (80, "A"),
    (75, "A-"), (70, "B+"), (65, "B"),  (60, "B-"),
    (55, "C+"), (50, "C"),  (45, "C-"), (40, "D+"),
    (35, "D"),  (30, "D-"), (20, "F"),  (0, "F-"),
]


def composite_to_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F-"


# ── Key level weighting ─────────────────────────────────────────────────────

def _key_weight(keystone_level: int) -> float:
    """Weight a run by its keystone level.

    Higher keys matter more. A +15 has 3x the weight of a +5.
    Minimum weight of 1.0 for any key.

    Scale:
      +2  = 1.0    +5  = 1.3    +8  = 1.6
      +10 = 2.0    +12 = 2.4    +15 = 3.0
    """
    return max(1.0, keystone_level * 0.2)


def _weighted_average(runs: list[DungeonRun], score_fn) -> float:
    """Compute a weighted average of per-run scores, weighted by key level."""
    if not runs:
        return 0

    total_weight = 0.0
    total_score = 0.0
    for run in runs:
        weight = _key_weight(run.keystone_level)
        score = score_fn(run)
        total_score += score * weight
        total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0


# ── Category scorers ────────────────────────────────────────────────────────

def _score_damage_output(runs: list[DungeonRun]) -> float:
    """DPS performance across runs, weighted by key level.

    The dps field contains the WCL rankPercent (0-100 percentile),
    representing how this player compares to others of the same spec.
    """
    return _weighted_average(runs, lambda r: min(100, max(0, r.dps)))


def _score_healing_throughput(runs: list[DungeonRun]) -> float:
    """Healing performance for healers, weighted by key level."""
    return _weighted_average(runs, lambda r: min(100, max(0, r.hps)))


def _score_utility_dps_tank(runs: list[DungeonRun]) -> float:
    """Utility score for DPS and tanks: primarily interrupts.

    Scoring scale (per dungeon run):
    - Interrupts: 15+ = excellent, 8-14 = good, 3-7 = okay, 0-2 = poor
    - Dispels: bonus if the class can dispel
    """
    def score_fn(run):
        interrupt_score = min(100, (run.interrupts / 15) * 100)
        if run.dispels > 0:
            dispel_score = min(100, (run.dispels / 5) * 100)
            return interrupt_score * 0.8 + dispel_score * 0.2
        return interrupt_score

    return _weighted_average(runs, score_fn)


def _score_utility_healer(runs: list[DungeonRun]) -> float:
    """Utility score for healers: primarily dispels.

    Most healer specs cannot interrupt (only Resto Shaman and Holy Paladin can).
    Healers are scored primarily on dispels — their core utility contribution.
    If the spec can interrupt, interrupts count as a bonus.
    """
    if not runs:
        return 0

    # Check if this healer spec can interrupt (use first run's spec)
    # We need class_id which isn't on DungeonRun, so we check if they
    # actually interrupted — if they did, they can
    has_any_interrupts = any(r.interrupts > 0 for r in runs)

    def score_fn(run):
        # Dispels: primary metric for healers (8+ = excellent, 4 = good, 0 = poor)
        dispel_score = min(100, (run.dispels / 8) * 100)

        if has_any_interrupts:
            # This healer can interrupt — give bonus for interrupts
            interrupt_score = min(100, (run.interrupts / 10) * 100)
            return dispel_score * 0.6 + interrupt_score * 0.4
        else:
            # This healer cannot interrupt — score purely on dispels
            return dispel_score

    return _weighted_average(runs, score_fn)


def _score_survivability(runs: list[DungeonRun]) -> float:
    """Survivability score combining death frequency and damage taken awareness.

    Two components:
    1. Death penalty (70% weight) — harsh curve, especially for DPS/healers
       who should rarely die. 7 deaths in a key = 0.
    2. Damage taken ratio (30% weight) — for DPS/healers, compares their
       damage taken against what's expected for a non-tank. High damage
       taken relative to the group signals standing in mechanics.

    Both are weighted by key level — dying in a +15 hurts more.
    """
    def death_score_fn(run):
        # Harsher curve: DPS/healers should not be dying
        if run.deaths == 0:
            return 100
        elif run.deaths == 1:
            return 65
        elif run.deaths == 2:
            return 35
        elif run.deaths == 3:
            return 15
        elif run.deaths == 4:
            return 5
        else:
            return 0  # 5+ deaths = zero, you're griefing the key

    def damage_taken_score_fn(run):
        # For non-tanks: penalize taking excessive damage
        # Tanks are expected to take damage, so they get a flat 75
        if run.role == Role.tank:
            return 75

        # Compare DPS/healer damage taken to a reasonable threshold
        # A DPS taking more than 30% of a tank's typical damage is concerning
        # We use the raw damage_taken_total as a proxy
        if run.damage_taken_total <= 0:
            return 75  # No data, neutral score

        duration_s = max(1, run.duration / 1000)
        dtps = run.damage_taken_total / duration_s  # damage taken per second

        # Benchmarks for DPS/healer DTPS in M+:
        # Under 5k DTPS = excellent (dodging everything)
        # 5-10k = normal (some unavoidable damage)
        # 10-20k = concerning (eating mechanics)
        # 20k+ = standing in fire
        if dtps < 5000:
            return 100
        elif dtps < 10000:
            return 80 - ((dtps - 5000) / 5000) * 20  # 80 -> 60
        elif dtps < 20000:
            return 60 - ((dtps - 10000) / 10000) * 40  # 60 -> 20
        else:
            return max(0, 20 - ((dtps - 20000) / 10000) * 20)

    death_avg = _weighted_average(runs, death_score_fn)
    dmg_taken_avg = _weighted_average(runs, damage_taken_score_fn)

    # Combine: deaths matter most, but damage taken catches the "barely alive" players
    return death_avg * 0.7 + dmg_taken_avg * 0.3


def _timing_modifier(runs: list[DungeonRun]) -> float:
    """Universal modifier based on key timing rate, weighted by key level.

    Timing a +15 counts more than timing a +2.
    Returns a value between -5 and +5.
    """
    if not runs:
        return 0

    total_weight = 0.0
    timed_weight = 0.0
    for run in runs:
        weight = _key_weight(run.keystone_level)
        total_weight += weight
        if run.timed:
            timed_weight += weight

    timed_rate = timed_weight / total_weight if total_weight > 0 else 0.5
    return (timed_rate - 0.5) * 10


# ── Role weight profiles ────────────────────────────────────────────────────

@dataclass
class RoleWeights:
    categories: dict[str, float]  # category_name -> weight (must sum to 1.0)


ROLE_WEIGHTS: dict[Role, RoleWeights] = {
    Role.dps: RoleWeights(
        categories={
            "damage_output": 0.50,
            "utility": 0.25,
            "survivability": 0.25,
        }
    ),
    Role.healer: RoleWeights(
        categories={
            "healing_throughput": 0.35,
            "damage_output": 0.20,
            "utility": 0.25,
            "survivability": 0.20,
        }
    ),
    Role.tank: RoleWeights(
        categories={
            "damage_output": 0.25,
            "utility": 0.30,
            "survivability": 0.45,
        }
    ),
}

# Category name -> scorer function (role-specific overrides below)
CATEGORY_SCORERS = {
    "damage_output": _score_damage_output,
    "healing_throughput": _score_healing_throughput,
    "utility": _score_utility_dps_tank,  # default for DPS/tanks
    "survivability": _score_survivability,
}

# Healer uses a different utility scorer
HEALER_CATEGORY_OVERRIDES = {
    "utility": _score_utility_healer,
}


# ── Main scoring function ───────────────────────────────────────────────────

@dataclass
class ScoreResult:
    role: Role
    overall_grade: str
    composite_score: float
    category_scores: dict[str, float]  # category_name -> 0-100
    timing_modifier: float
    runs_analyzed: int


def score_player_runs(
    runs: list[DungeonRun],
    role: Role,
    zone_dps_percentile: float | None = None,
) -> ScoreResult:
    """Score a set of dungeon runs for a player in a specific role.

    All category scores use weighted averages where higher keystone
    levels have more impact on the final score.

    If zone_dps_percentile is provided (from zoneRankings), it's used as
    the damage_output score since it covers ALL runs including archived ones,
    giving a more complete picture than per-fight data alone.
    """
    weights = ROLE_WEIGHTS[role]
    category_scores: dict[str, float] = {}
    composite = 0.0

    # Use healer-specific scorers when applicable
    scorers = dict(CATEGORY_SCORERS)
    if role == Role.healer:
        scorers.update(HEALER_CATEGORY_OVERRIDES)

    for category_name, weight in weights.categories.items():
        # Use zone rankings percentile for damage output if available
        if category_name == "damage_output" and zone_dps_percentile is not None:
            score = zone_dps_percentile
        else:
            scorer = scorers[category_name]
            score = scorer(runs)
        category_scores[category_name] = round(score, 1)
        composite += score * weight

    # Apply universal timing modifier
    timing_mod = _timing_modifier(runs)
    category_scores["timing_modifier"] = round(timing_mod, 1)
    composite = max(0, min(100, composite + timing_mod))

    return ScoreResult(
        role=role,
        overall_grade=composite_to_grade(composite),
        composite_score=round(composite, 1),
        category_scores=category_scores,
        timing_modifier=timing_mod,
        runs_analyzed=len(runs),
    )
