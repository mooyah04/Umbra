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


# ── Full pipeline ───────────────────────────────────────────────────────────

def test_score_player_runs_returns_all_expected_categories():
    runs = [_run() for _ in range(3)]
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
