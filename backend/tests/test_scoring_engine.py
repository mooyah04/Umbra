"""Scoring engine tests — no DB, pure dataclass-in-memory.

These tests pin behavior that's easy to break when tuning weights:
- Grade threshold boundaries
- Role weight application
- Key-level weighting in averages
- CPM scorer uses role/spec benchmarks, not the old universal curve
"""
from datetime import datetime

import pytest

from app.models import DungeonRun, Role
from app.scoring.engine import (
    GRADE_THRESHOLDS,
    ROLE_WEIGHTS,
    _key_weight,
    _score_casts_per_minute,
    _score_damage_output,
    _score_healing_throughput,
    _timing_modifier,
    composite_to_grade,
    score_player_runs,
)


def _run(role=Role.dps, spec="Frost", keystone_level=10, **overrides) -> DungeonRun:
    defaults = dict(
        role=role, spec_name=spec, keystone_level=keystone_level,
        encounter_id=10658, dps=60, hps=0, ilvl=620, duration=1_800_000,
        deaths=0, interrupts=8, dispels=2,
        avoidable_damage_taken=0, damage_taken_total=0,
        casts_total=900, cooldown_usage_pct=70, timed=True,
        logged_at=datetime(2026, 4, 1), wcl_report_id="r1", fight_id=1,
    )
    defaults.update(overrides)
    return DungeonRun(**defaults)


# ── Grade thresholds ────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (100, "S+"), (95, "S+"), (94.9, "S"), (90, "S"), (89, "A+"),
    (75, "A-"), (50, "C"), (0, "F-"), (-10, "F-"),
])
def test_composite_to_grade(score, expected):
    assert composite_to_grade(score) == expected


def test_grade_thresholds_descending():
    """Thresholds must be monotonically decreasing for composite_to_grade to work."""
    values = [t for t, _ in GRADE_THRESHOLDS]
    assert values == sorted(values, reverse=True)


# ── Role weights invariant ──────────────────────────────────────────────────

@pytest.mark.parametrize("role", [Role.dps, Role.healer, Role.tank])
def test_role_weights_sum_to_one(role):
    """Any drift here invalidates every composite score."""
    total = sum(ROLE_WEIGHTS[role].categories.values())
    assert abs(total - 1.0) < 1e-9, f"{role}: weights sum to {total}"


# ── Key level weighting ─────────────────────────────────────────────────────

def test_key_weight_has_floor():
    assert _key_weight(0) == 1.0
    assert _key_weight(-5) == 1.0


def test_key_weight_monotonic_above_floor():
    # Below key 5 the function floors at 1.0 — only test the range where it scales.
    for lo, hi in [(6, 10), (10, 15), (15, 20)]:
        assert _key_weight(hi) > _key_weight(lo)


def test_higher_keys_dominate_average():
    """A single +15 should outweigh a single +2 in a weighted average."""
    high = _run(keystone_level=15, casts_total=30 * 35, duration=30 * 60000)   # ~35 CPM
    low = _run(keystone_level=2, casts_total=30 * 5, duration=30 * 60000)      # ~5 CPM
    avg = _score_casts_per_minute([high, low])
    assert avg > 50, "high-key performance should dominate"


# ── Timing modifier ─────────────────────────────────────────────────────────

def test_timing_modifier_all_timed_is_positive_max():
    runs = [_run(timed=True, keystone_level=10) for _ in range(3)]
    assert _timing_modifier(runs) == pytest.approx(8.0)


def test_timing_modifier_none_timed_is_negative_max():
    runs = [_run(timed=False, keystone_level=10) for _ in range(3)]
    assert _timing_modifier(runs) == pytest.approx(-8.0)


def test_timing_modifier_empty_is_zero():
    assert _timing_modifier([]) == 0


# ── CPM uses benchmarks (no fallback on missing data) ───────────────────────

def test_cpm_returns_zero_on_no_cast_data():
    """Old code returned 50 (neutral) — that masked AFK players. Should be 0."""
    run = _run(casts_total=0, duration=1_800_000)
    assert _score_casts_per_minute([run]) == 0.0


def test_cpm_differs_between_specs_at_same_raw_rate():
    """Fury at 22 CPM is bad; MM at 22 CPM is great. Benchmarks must differ."""
    fury = _run(spec="Fury", casts_total=30 * 22, duration=30 * 60000)
    mm = _run(spec="Marksmanship", casts_total=30 * 22, duration=30 * 60000)
    fury_score = _score_casts_per_minute([fury])
    mm_score = _score_casts_per_minute([mm])
    assert mm_score > fury_score + 40, "spec-aware benchmarks not being applied"


def test_cpm_class_disambiguates_ambiguous_spec_names():
    """Resto Druid and Resto Shaman both have spec_name='Restoration' in ingest.
    Class-aware lookup must route each to its own benchmark rather than both
    falling back to the role default.
    """
    # Prot Warrior and Prot Paladin — both role=tank, spec='Protection' in ingest.
    # They have different benchmarks: Warrior excellent=44, Paladin excellent=38.
    # At 40 CPM: Warrior is ~80 (between good 36 and excellent 44), Paladin is 100.
    warr = _run(role=Role.tank, spec="Protection",
                casts_total=30 * 40, duration=30 * 60000)
    pal = _run(role=Role.tank, spec="Protection",
               casts_total=30 * 40, duration=30 * 60000)
    warr_score = _score_casts_per_minute([warr], class_id=1)
    pal_score = _score_casts_per_minute([pal], class_id=2)
    assert pal_score > warr_score, (
        "class_id-aware CPM must distinguish Prot Warrior (higher benchmark) "
        "from Prot Paladin (lower benchmark) at the same raw CPM"
    )


# ── Full pipeline ───────────────────────────────────────────────────────────

def test_score_player_runs_returns_all_expected_categories():
    """Distinct encounter_ids so Phase 2 selection keeps all three runs;
    this test is asserting the shape of a populated multi-dungeon
    composite, not selection behavior.
    """
    runs = [_run(encounter_id=enc) for enc in (10658, 10661, 10662)]
    result = score_player_runs(runs, Role.dps, zone_dps_percentile=70.0)
    for cat in ROLE_WEIGHTS[Role.dps].categories:
        assert cat in result.category_scores, f"missing {cat}"
    assert result.runs_analyzed == 3
    assert 0 <= result.composite_score <= 100
    assert result.overall_grade in {g for _, g in GRADE_THRESHOLDS}


def test_zone_percentile_overrides_damage_output():
    """When zone_dps_percentile is passed, it replaces the raw DPS avg."""
    runs = [_run(dps=10) for _ in range(3)]  # terrible raw DPS field
    result = score_player_runs(runs, Role.dps, zone_dps_percentile=95.0)
    assert result.category_scores["damage_output"] == 95.0


def test_healer_uses_healing_throughput_category():
    runs = [_run(role=Role.healer, spec="Restoration Druid", hps=80) for _ in range(3)]
    result = score_player_runs(runs, Role.healer)
    assert "healing_throughput" in result.category_scores
    assert "damage_output" in result.category_scores  # healers are graded on damage too


def test_empty_runs_produce_f_grade():
    result = score_player_runs([], Role.dps, zone_dps_percentile=0)
    assert result.runs_analyzed == 0
    assert result.composite_score <= 20


# ── Percentile-vs-raw guard ─────────────────────────────────────────────────
# Ingest overwrites `dps` with WCL rankPercent (0-100) only when zoneRankings
# returns a match; otherwise the raw absolute DPS (millions) stays there.
# The scorer must skip out-of-range values rather than min(100, raw)=100,
# which silently inflated grades for runs without a ranking match.

def test_damage_output_skips_raw_dps_values():
    """Raw DPS numbers (millions) must not clamp to 100."""
    # Mix: one genuine 40th-percentile run + one run where ingest left
    # the raw DPS (no zoneRankings match). Result should reflect only
    # the percentile run, not saturate at 100.
    runs = [
        _run(dps=40),          # valid percentile
        _run(dps=60_571_184),  # raw — this was a real Elonmunk observation
    ]
    assert _score_damage_output(runs) == pytest.approx(40)


def test_damage_output_all_raw_returns_none():
    """A player with NO runs tagged with a percentile signals missing
    data (None) so the composite can renormalize the remaining weights
    instead of treating the category as a genuine 0 — the old behavior
    crushed per-dungeon grades on unranked legacy dungeons (Pit of Saron
    in Midnight S1) even for flawless runs.
    """
    runs = [_run(dps=30_000_000), _run(dps=45_000_000)]
    assert _score_damage_output(runs) is None


def test_healing_throughput_skips_raw_hps_values():
    runs = [
        _run(role=Role.healer, hps=85),           # valid percentile
        _run(role=Role.healer, hps=59_110_540),   # raw — real Dobbermon observation
    ]
    assert _score_healing_throughput(runs) == pytest.approx(85)


def test_damage_output_accepts_boundary_values():
    """0 and 100 are valid percentile values, not raw. Keep them."""
    runs = [_run(dps=0), _run(dps=100)]
    assert _score_damage_output(runs) == pytest.approx(50)


def test_healing_throughput_all_raw_returns_none():
    """Healer equivalent of the damage-output missing-data signal."""
    runs = [
        _run(role=Role.healer, hps=40_000_000),
        _run(role=Role.healer, hps=75_000_000),
    ]
    assert _score_healing_throughput(runs) is None


# ── Weight redistribution on missing percentile data ───────────────────────

def _strong_healer_run_no_percentiles(**overrides):
    """Healer run that looks excellent on every non-percentile metric
    but has raw (unranked) dps+hps — the Peeli-on-PoS pattern."""
    defaults = dict(
        role=Role.healer,
        spec_name="Holy",
        encounter_id=10658,  # Pit of Saron, unranked in Midnight S1
        keystone_level=20,
        timed=True,
        dps=29_000_000,           # raw — no WCL percentile
        hps=170_000_000,          # raw — no WCL percentile
        deaths=1,
        interrupts=10, dispels=12,
        casts_total=1300,
        cooldown_usage_pct=100,
        duration=1_800_000,  # 30 min
        avoidable_damage_taken=0,
        damage_taken_total=0,
        cc_casts=8,
        logged_at=datetime(2026, 4, 18),
        wcl_report_id="peeli-pos-1", fight_id=1,
    )
    defaults.update(overrides)
    return DungeonRun(**defaults)


def test_unranked_dungeon_does_not_collapse_healer_grade():
    """Peeli's +20 PoS: timed, 1 death, 100% CD usage, 10+ kicks.
    Before the weight-redistribution fix, the missing percentile data
    zeroed 40% of the weight bucket and dragged the composite to D+.
    After the fix, the grade should reflect the categories we CAN
    measure — minimum B for a clean high-key healer run.
    """
    runs = [_strong_healer_run_no_percentiles(wcl_report_id=f"r{i}", fight_id=i)
            for i in range(5)]
    result = score_player_runs(runs=runs, role=Role.healer, class_id=6)

    assert "damage_output" in result.excluded_categories
    assert "healing_throughput" in result.excluded_categories
    assert result.composite_score >= 65, (
        f"clean unranked-dungeon healer scored {result.composite_score} "
        f"(grade {result.overall_grade}); expected ≥ B/65"
    )


def test_excluded_categories_empty_when_all_ranked():
    """Baseline: a fully-ranked run set populates no excluded list.
    Distinct encounter_ids so Phase 2 selection keeps all three runs;
    a single-encounter set would collapse to one selected run, which
    is fine but isn't what this baseline is asserting.
    """
    runs = [_run(role=Role.dps, dps=80, hps=0, encounter_id=enc)
            for enc in (10658, 10661, 10662)]
    result = score_player_runs(runs=runs, role=Role.dps, class_id=8)
    assert result.excluded_categories == []


# ── Phase 2: per-dungeon best-run selection ────────────────────────────────

def test_phase2_single_run_per_dungeon_is_noop():
    """When every dungeon has exactly one run, selection picks each one."""
    runs = [_run(encounter_id=enc, dps=70) for enc in (10658, 10661, 10662)]
    result = score_player_runs(runs, Role.dps, class_id=8)
    assert result.runs_analyzed == 3


def test_phase2_collapses_multiple_runs_in_same_dungeon():
    """Three runs all on Skyreach should collapse to one selected run."""
    runs = [_run(encounter_id=10658, fight_id=i, wcl_report_id=f"r{i}", dps=70)
            for i in range(3)]
    result = score_player_runs(runs, Role.dps, class_id=8)
    assert result.runs_analyzed == 1


def test_phase2_picks_best_run_per_dungeon():
    """Within a single dungeon, the highest-composite run wins."""
    great = _run(encounter_id=10658, fight_id=1, wcl_report_id="g",
                 dps=95, deaths=0, interrupts=15, dispels=5,
                 cooldown_usage_pct=100, cc_casts=10)
    sloppy = _run(encounter_id=10658, fight_id=2, wcl_report_id="s",
                  dps=20, deaths=4, interrupts=2, dispels=0,
                  cooldown_usage_pct=20, cc_casts=0)
    result = score_player_runs([great, sloppy], Role.dps, class_id=8)
    great_only = score_player_runs([great], Role.dps, class_id=8,
                                   select_runs=False)
    # Selection should pick `great`; composite matches scoring `great` alone.
    assert result.composite_score == pytest.approx(great_only.composite_score)


def test_phase2_higher_key_wins_when_scores_close():
    """A clean +10 (composite ~70) should outrank a clean +5 (composite ~70)
    on the same dungeon because key_weight breaks the tie.
    """
    plus10 = _run(encounter_id=10658, fight_id=1, wcl_report_id="hi",
                  keystone_level=10, dps=70)
    plus5 = _run(encounter_id=10658, fight_id=2, wcl_report_id="lo",
                 keystone_level=5, dps=70)
    result = score_player_runs([plus5, plus10], Role.dps, class_id=8)
    plus10_only = score_player_runs([plus10], Role.dps, class_id=8,
                                    select_runs=False)
    assert result.composite_score == pytest.approx(plus10_only.composite_score)


def test_phase2_depleted_runs_excluded_when_timed_exists():
    """If any timed run exists in the role pool, depleted runs drop out
    entirely — even if a depleted +15 has higher score×weight than a
    timed +5, the depleted run shouldn't count.
    """
    timed_low = _run(encounter_id=10658, fight_id=1, wcl_report_id="t",
                     keystone_level=5, dps=60, timed=True, deaths=0)
    depleted_high = _run(encounter_id=10661, fight_id=2, wcl_report_id="d",
                         keystone_level=15, dps=90, timed=False, deaths=2)
    result = score_player_runs([timed_low, depleted_high], Role.dps, class_id=8)
    timed_only = score_player_runs([timed_low], Role.dps, class_id=8,
                                   select_runs=False)
    # Selection keeps only the timed run; the depleted-but-higher-key
    # run does NOT contribute to the composite.
    assert result.composite_score == pytest.approx(timed_only.composite_score)
    assert result.runs_analyzed == 1


def test_phase2_falls_back_to_depleted_when_zero_timed():
    """A player with zero timed runs still gets a grade — selection
    applies the same per-dungeon best logic to the depleted pool. They
    shouldn't be ungraded just because they're pushing keys above their
    capability.
    """
    runs = [
        _run(encounter_id=enc, fight_id=i, wcl_report_id=f"r{i}",
             keystone_level=15, dps=50, timed=False, deaths=2)
        for i, enc in enumerate((10658, 10661, 10662))
    ]
    result = score_player_runs(runs, Role.dps, class_id=8)
    assert result.runs_analyzed == 3
    assert result.composite_score > 0


def test_phase2_timing_modifier_uses_original_runs():
    """Timing modifier should reflect the player's actual timing rate,
    not the post-selection (entirely-timed) pool. Selection drops
    depleted runs from grading but the timing stat must still surface
    the truth: this player only timed half their attempts.
    """
    timed = _run(encounter_id=10658, fight_id=1, wcl_report_id="t",
                 timed=True, dps=70)
    depleted = _run(encounter_id=10661, fight_id=2, wcl_report_id="d",
                    timed=False, dps=70)
    result = score_player_runs([timed, depleted], Role.dps, class_id=8)
    # 1 of 2 timed → timing rate 0.5 → modifier 0.0 (or close).
    # If selection were applied first, both selected runs are timed →
    # timing rate 1.0 → modifier +8.0 (the wrong number).
    assert result.timing_modifier == pytest.approx(0.0)


def test_phase2_select_runs_false_preserves_legacy_behavior():
    """Tests / scripts that need raw all-runs scoring can pass
    select_runs=False to skip Phase 2 selection entirely.
    """
    runs = [_run(encounter_id=10658, fight_id=i, wcl_report_id=f"r{i}", dps=70)
            for i in range(3)]
    result = score_player_runs(runs, Role.dps, class_id=8, select_runs=False)
    assert result.runs_analyzed == 3
