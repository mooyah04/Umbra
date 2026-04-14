"""CPM benchmark table + scoring curve."""
import pytest

from app.models import Role
from app.scoring.cpm_benchmarks import (
    ROLE_BENCHMARKS,
    SPEC_BENCHMARKS,
    get_benchmark,
    score_cpm,
)


def test_role_benchmarks_have_all_roles():
    for role in (Role.dps, Role.healer, Role.tank):
        assert role in ROLE_BENCHMARKS


def test_spec_override_wins_over_role_default():
    spec_b = get_benchmark(Role.dps, "Fury")
    role_b = get_benchmark(Role.dps, "SomeUnknownSpec")
    assert spec_b == SPEC_BENCHMARKS["Fury"]
    assert role_b == ROLE_BENCHMARKS[Role.dps]


def test_missing_spec_falls_back_to_role():
    assert get_benchmark(Role.dps, None) == ROLE_BENCHMARKS[Role.dps]
    assert get_benchmark(Role.dps, "NotARealSpec") == ROLE_BENCHMARKS[Role.dps]


@pytest.mark.parametrize("role", [Role.dps, Role.healer, Role.tank])
def test_benchmark_thresholds_are_ordered(role):
    b = ROLE_BENCHMARKS[role]
    assert b.poor < b.fair < b.good < b.excellent


@pytest.mark.parametrize("spec_name,b", list(SPEC_BENCHMARKS.items()))
def test_spec_benchmarks_are_ordered(spec_name, b):
    assert b.poor < b.fair < b.good < b.excellent, f"{spec_name} thresholds not ordered"


def test_score_cpm_anchor_points():
    b = ROLE_BENCHMARKS[Role.dps]
    assert score_cpm(b.poor, b) == 0
    assert score_cpm(b.fair, b) == pytest.approx(50)
    assert score_cpm(b.good, b) == pytest.approx(80)
    assert score_cpm(b.excellent, b) == pytest.approx(100)
    assert score_cpm(b.excellent + 100, b) == 100
    assert score_cpm(0, b) == 0


def test_score_cpm_monotonic_within_tier():
    b = ROLE_BENCHMARKS[Role.dps]
    values = [score_cpm(x, b) for x in range(0, 60)]
    for prev, nxt in zip(values, values[1:]):
        assert nxt >= prev, "score_cpm must be monotonically non-decreasing"
