"""Role-aware scoring engine for Umbra.

Computes a 0-100 composite score per role, then maps to a letter grade (S+ to F-).
Each role uses different category weights reflecting what matters for that role in M+.

Runs are weighted by keystone level — higher keys have more impact on the final score.
Key timing is a universal ±8 modifier applied to all roles equally.
"""

from dataclasses import dataclass
from app.models import DungeonRun, Role
from app.scoring.cpm_benchmarks import get_benchmark, score_cpm
from app.scoring.dispel_capability import class_has_dispel
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


def _score_utility_dps_tank(runs: list[DungeonRun], class_id: int | None = None) -> float:
    """Utility score for DPS and tanks: interrupts, dispels, and CC.

    Weights adapt per-run to what the class can actually do, so a class
    with no dispel (Rogue/Warrior/DK/DH) isn't punished for something
    outside their kit. Per-run cc-data check means old runs without
    cc_casts get the fair no-cc weights, not the new-run dispel penalty.
    """
    can_dispel = class_has_dispel(class_id)

    def score_fn(run):
        # Interrupt score with critical kick bonus
        base_kicks = run.interrupts
        crit_kicks = getattr(run, "critical_interrupts", None)
        if crit_kicks is not None and crit_kicks > 0:
            # Critical interrupts count 1.5x — reward kicking the right spells
            effective_kicks = (base_kicks - crit_kicks) + (crit_kicks * 1.5)
        else:
            effective_kicks = base_kicks
        interrupt_score = min(100, (effective_kicks / 15) * 100)

        # Dispel component only applies to classes that can dispel. Everyone
        # else redistributes the weight to the remaining components.
        dispel_score = min(100, (run.dispels / 5) * 100) if can_dispel else 0

        # CC — per-run check so we don't penalize historical runs that were
        # ingested before we tracked cc_casts.
        has_cc = getattr(run, "cc_casts", None) is not None
        cc_score = min(100, ((run.cc_casts or 0) / 10) * 100) if has_cc else 0

        # Build weights dynamically based on what's applicable.
        # Interrupts are always the core — 55% if all 3 components,
        # scaling up when dispels/cc are excluded.
        if can_dispel and has_cc:
            return interrupt_score * 0.55 + dispel_score * 0.20 + cc_score * 0.25
        elif can_dispel:  # no CC data
            return interrupt_score * 0.80 + dispel_score * 0.20
        elif has_cc:  # no dispel capability
            return interrupt_score * 0.70 + cc_score * 0.30
        else:  # no dispel, no CC data
            return interrupt_score

    return _weighted_average(runs, score_fn)


def _score_utility_healer(runs: list[DungeonRun], class_id: int | None = None) -> float:
    """Utility score for healers: dispels + interrupts (if specced) + CC.

    All healer specs have some CC ability (Paralysis, Sleep Walk, Psychic
    Scream, Hammer of Justice, Hex, Entangling Roots), and modern M+
    rewards using them. The old scorer ignored CC entirely.

    Dispels stay the primary metric (every healer dispels heavily in M+).
    Interrupts only factor in for Resto Shaman / Holy Paladin (the only
    healer specs with an interrupt in the current game).
    """
    if not runs:
        return 0

    spec_name = runs[0].spec_name if runs else "Unknown"
    can_kick = False
    if class_id is not None:
        can_kick = healer_can_interrupt(class_id, spec_name)

    def score_fn(run):
        # Dispels — 8+ per run = excellent for a healer
        dispel_score = min(100, (run.dispels / 8) * 100)

        # Per-run CC availability (old runs predate cc_casts tracking)
        has_cc = getattr(run, "cc_casts", None) is not None
        # Healers are expected to CC less than DPS (6+ = excellent)
        cc_score = min(100, ((run.cc_casts or 0) / 6) * 100) if has_cc else 0

        # Interrupts — healer specs that can kick (Resto Sham, Holy Pal)
        if can_kick:
            interrupt_score = min(100, (run.interrupts / 10) * 100)
        else:
            interrupt_score = 0

        # Distribute weights. Dispels dominate; CC and kicks fill in.
        if can_kick and has_cc:
            return dispel_score * 0.50 + interrupt_score * 0.30 + cc_score * 0.20
        elif can_kick:
            return dispel_score * 0.60 + interrupt_score * 0.40
        elif has_cc:
            return dispel_score * 0.75 + cc_score * 0.25
        else:
            return dispel_score

    return _weighted_average(runs, score_fn)


def _score_survivability(runs: list[DungeonRun]) -> float:
    """Survivability score combining death frequency, avoidable damage, and healing burden.

    Three components:
    1. Death penalty (50% weight) — harsh curve. Avoidable deaths penalized
       more severely than unavoidable deaths when that data is available.
    2. Avoidable damage ratio (25% weight) — ratio of avoidable-to-total damage
       taken. Falls back to raw DTPS when avoidable data is incomplete.
    3. Healing burden (25% weight) — how much healing you consumed. DPS/healers
       who take tons of healing are a burden even if they don't die. Tanks are
       expected to receive healing so this is neutral for them.

    All components are weighted by key level — dying in a +15 hurts more.
    """
    def death_score_fn(run):
        # Softer death curve. One death in a +15 is often unavoidable even
        # for top players; the old curve (1 death = 65) was harsh. New:
        # 0=100, 1=80, 2=55, 3=30, 4=10, 5+=0.
        if run.deaths == 0:
            base = 100
        elif run.deaths == 1:
            base = 80
        elif run.deaths == 2:
            base = 55
        elif run.deaths == 3:
            base = 30
        elif run.deaths == 4:
            base = 10
        else:
            base = 0

        # Extra penalty for deaths we know were avoidable (standing in fire).
        avoidable = getattr(run, "avoidable_deaths", None)
        if avoidable is not None and avoidable > 0 and run.deaths > 0:
            avoidable_penalty = min(base, avoidable * 10)
            return max(0, base - avoidable_penalty)

        return base

    def avoidable_damage_score_fn(run):
        # Primary: avoidable-ratio when we have per-ability breakdown.
        if run.avoidable_damage_taken > 0:
            if run.damage_taken_total > 0:
                avoidable_ratio = run.avoidable_damage_taken / run.damage_taken_total
            else:
                avoidable_ratio = 0
            # 0% avoidable = 100, 10% = 70, 20% = 40, 30%+ = 10
            return max(0, 100 - avoidable_ratio * 300)

        # Tanks aren't scored on DTPS (they're supposed to take the damage).
        if run.role == Role.tank:
            return 75

        if run.damage_taken_total <= 0:
            return 75

        duration_s = max(1, run.duration / 1000)
        dtps = run.damage_taken_total / duration_s

        # DTPS scales with key level — higher keys = more incoming damage
        # by design. Absolute thresholds branded every high-key player as
        # "unsafe" even when their play was clean. Scale thresholds by key.
        # At +2 multiplier = 1.0 (same as before); +10 ~= 2.2x; +15 ~= 3.0x.
        level_mult = 1.0 + max(0, run.keystone_level - 2) * 0.15

        if dtps < 5000 * level_mult:
            return 100
        elif dtps < 10000 * level_mult:
            return 80 - ((dtps - 5000 * level_mult) / (5000 * level_mult)) * 20
        elif dtps < 20000 * level_mult:
            return 60 - ((dtps - 10000 * level_mult) / (10000 * level_mult)) * 40
        else:
            return max(0, 20 - ((dtps - 20000 * level_mult) / (10000 * level_mult)) * 20)

    def healing_burden_score_fn(run):
        healing_received = getattr(run, "healing_received", None)
        if healing_received is None:
            return 75  # No data, neutral

        # Tanks are expected to receive healing — neutral score
        if run.role == Role.tank:
            return 75

        duration_s = max(1, run.duration / 1000)
        hrps = healing_received / duration_s

        # HRPS scales with key level — same story as DTPS. Absolute thresholds
        # punished everyone in high keys for taking normal boss damage.
        level_mult = 1.0 + max(0, run.keystone_level - 2) * 0.15

        if hrps < 2000 * level_mult:
            return 100
        elif hrps < 5000 * level_mult:
            return 90 - ((hrps - 2000 * level_mult) / (3000 * level_mult)) * 30
        elif hrps < 10000 * level_mult:
            return 60 - ((hrps - 5000 * level_mult) / (5000 * level_mult)) * 40
        else:
            return max(0, 20 - ((hrps - 10000 * level_mult) / (10000 * level_mult)) * 20)

    death_avg = _weighted_average(runs, death_score_fn)
    avoidable_avg = _weighted_average(runs, avoidable_damage_score_fn)
    healing_burden_avg = _weighted_average(runs, healing_burden_score_fn)

    # Check if healing burden data is available on any run
    has_healing_data = any(
        getattr(r, "healing_received", None) is not None for r in runs
    )

    if has_healing_data:
        # Full scoring with all three components
        return death_avg * 0.50 + avoidable_avg * 0.25 + healing_burden_avg * 0.25
    else:
        # Fallback for old data without healing_received
        return death_avg * 0.60 + avoidable_avg * 0.40


def _score_cooldown_usage(runs: list[DungeonRun]) -> float:
    """Score based on whether the player uses their major cooldowns.

    A player who never presses their CDs is leaving massive performance
    on the table. This directly catches the "used no cooldowns" problem.

    cooldown_usage_pct is stored as 0-100 (% of expected CDs that were cast).
    """
    def score_fn(run):
        # cooldown_usage_pct is already 0-100 from the pipeline
        return min(100, max(0, run.cooldown_usage_pct))

    return _weighted_average(runs, score_fn)


def _score_casts_per_minute(runs: list[DungeonRun]) -> float:
    """Score based on casts per minute, using role/spec-aware benchmarks.

    The old scorer used a single universal curve (35+ CPM = 100) which unfairly
    penalized low-CPM specs (MM Hunter, Balance Druid, healers, tanks). We now
    look up a benchmark per run based on the run's spec, falling back to the
    role default when a spec isn't in the override table.

    See app/scoring/cpm_benchmarks.py for the benchmark data and curve.
    Runs with no cast data (casts_total<=0 or duration<=0) return 0 — a real
    dungeon run always has casts, so missing data is a real signal, not neutral.
    """
    def score_fn(run):
        if run.casts_total <= 0 or run.duration <= 0:
            return 0.0

        duration_min = run.duration / 60000
        if duration_min <= 0:
            return 0.0

        cpm = run.casts_total / duration_min
        benchmark = get_benchmark(run.role, run.spec_name)
        return score_cpm(cpm, benchmark)

    return _weighted_average(runs, score_fn)


def _timing_modifier(runs: list[DungeonRun]) -> float:
    """Universal modifier based on key timing rate, weighted by key level.

    Timing a +15 counts more than timing a +2.
    Returns a value between -8 and +8 (P1 rebalance: widened from ±5
    to give more weight to actually timing keys — especially important
    for tanks as a route quality proxy).
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
    return (timed_rate - 0.5) * 16


# ── Role weight profiles ────────────────────────────────────────────────────

@dataclass
class RoleWeights:
    categories: dict[str, float]  # category_name -> weight (must sum to 1.0)


ROLE_WEIGHTS: dict[Role, RoleWeights] = {
    # P1 rebalance (fairness audit): reduced CPM weight (spec bias),
    # boosted survivability. Timing modifier provides +/-8 on top.
    Role.dps: RoleWeights(
        categories={
            "damage_output": 0.30,     # primary, slightly reduced from 0.35
            "utility": 0.20,           # up from 0.15 — kicks/CC are critical in M+
            "survivability": 0.25,     # up from 0.20 — not dying matters more than CPM
            "cooldown_usage": 0.15,    # unchanged
            "casts_per_minute": 0.10,  # down from 0.15 — CPM has spec bias (e.g. MM Hunter vs Fury)
        }
    ),
    # P1 rebalance: healing_throughput reduced (punishes efficient healers in
    # clean groups), healer DPS doubled (key differentiator in modern M+).
    Role.healer: RoleWeights(
        categories={
            "healing_throughput": 0.20, # down from 0.30 — penalized efficient healers
            "damage_output": 0.20,      # up from 0.10 — healer DPS is a key M+ differentiator
            "utility": 0.20,            # unchanged
            "survivability": 0.15,      # unchanged
            "cooldown_usage": 0.15,     # unchanged
            "casts_per_minute": 0.10,   # unchanged
        }
    ),
    # P1 rebalance: tank damage boosted (primary differentiator), survivability
    # reduced (over-rewarded passive play), utility slightly reduced.
    Role.tank: RoleWeights(
        categories={
            "damage_output": 0.25,     # up from 0.15 — tank DPS is a primary differentiator
            "utility": 0.15,           # down from 0.20
            "survivability": 0.25,     # down from 0.30 — was over-rewarding passive play
            "cooldown_usage": 0.20,    # unchanged
            "casts_per_minute": 0.15,  # unchanged
        }
    ),
}

# Category name -> scorer function (role-specific overrides below)
CATEGORY_SCORERS = {
    "damage_output": _score_damage_output,
    "healing_throughput": _score_healing_throughput,
    "utility": _score_utility_dps_tank,  # default for DPS/tanks
    "survivability": _score_survivability,
    "cooldown_usage": _score_cooldown_usage,
    "casts_per_minute": _score_casts_per_minute,
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
    zone_dps_ilvl_percentile: float | None = None,
    class_id: int | None = None,
) -> ScoreResult:
    """Score a set of dungeon runs for a player in a specific role.

    All category scores use weighted averages where higher keystone
    levels have more impact on the final score.

    Two DPS percentiles from zoneRankings:
    - zone_dps_percentile: vs all players of same spec (overall)
    - zone_dps_ilvl_percentile: vs same spec at similar ilvl (gear-relative)
    The overall percentile is used for the grade composite.
    Both are stored in category_scores for display.

    class_id is needed for healer utility scoring (determines if the spec
    can interrupt — only Resto Shaman and Holy Paladin can).
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
            # Utility scorers (healer and dps/tank) both take class_id now —
            # healer uses it for interrupt eligibility, dps/tank for dispel.
            if category_name == "utility":
                score = scorer(runs, class_id=class_id)
            else:
                score = scorer(runs)
        category_scores[category_name] = round(score, 1)
        composite += score * weight

    # Store ilvl-relative percentile separately (for display, not in composite)
    if zone_dps_ilvl_percentile is not None:
        category_scores["damage_output_ilvl"] = round(zone_dps_ilvl_percentile, 1)

    # Compute and record the timing stat for display, but do NOT fold it
    # into the composite. Reasons:
    #   - Higher keys are meant to be hard; penalizing players who fail to
    #     time a push key punishes them for attempting the correct content.
    #   - Mythic+ keys can be reset/re-rolled, so timing is gameable —
    #     sandbagging at low keys and only logging timed runs would inflate
    #     grades without reflecting actual play.
    #   - Key level is already rewarded inside every category via the
    #     per-run weight (higher keys count more). Timing would be double-
    #     counting on top of that.
    # The stat is still exported so the UI can show "X% keys timed".
    timing_mod = _timing_modifier(runs)
    category_scores["timing_modifier"] = round(timing_mod, 1)
    composite = max(0, min(100, composite))

    return ScoreResult(
        role=role,
        overall_grade=composite_to_grade(composite),
        composite_score=round(composite, 1),
        category_scores=category_scores,
        timing_modifier=timing_mod,
        runs_analyzed=len(runs),
    )
