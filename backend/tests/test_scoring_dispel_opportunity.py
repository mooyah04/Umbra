"""Per-dungeon dispel opportunity for utility scoring.

The scoring engine's utility scorer used to treat every dungeon as if
it had a uniform supply of dispellable debuffs. Healers in a dispel-poor
dungeon got 0 dispels and lost ~75% of their utility category because
of it — penalized for something they couldn't do.

We added a tri-state `DungeonData.dispellable_debuffs`:
  - None: not sampled, legacy behavior (assume opportunity)
  - (): sampled and confirmed empty — drop dispel from scoring
  - tuple: sampled with data — treat as opportunity-present

These tests pin the per-run behavior without requiring live sampler
data. Real per-dungeon data populates as the sampler runs.
"""
from datetime import datetime
from unittest.mock import patch

import pytest

from app.models import DungeonRun, Role
from app.scoring.engine import (
    _score_utility_dps_tank,
    _score_utility_healer,
)


def _mk_run(*, encounter_id=1, dispels=0, interrupts=0, cc_casts=0,
            role=Role.dps, spec="Assassination"):
    return DungeonRun(
        id=0, player_id=0, encounter_id=encounter_id, keystone_level=10,
        role=role, spec_name=spec,
        dps=0, hps=0, ilvl=640,
        duration=1800000,
        deaths=0,
        interrupts=interrupts, dispels=dispels,
        avoidable_damage_taken=0, damage_taken_total=1,
        casts_total=100, cooldown_usage_pct=0,
        wcl_report_id="x", fight_id=0, timed=True,
        logged_at=datetime(2026, 4, 1),
        cc_casts=cc_casts,
    )


# ── DPS/Tank scorer ──────────────────────────────────────────────────────────


def test_dps_zero_dispels_in_no_opportunity_dungeon_drops_weight():
    """Resto Druid (class 11, healer) is tested in healer section below;
    for DPS this uses a Mage (class 8, has dispel). Same mage with 0 CC
    in a dungeon with no dispellable debuffs should score on kicks only
    — same math as a non-dispel class."""
    runs = [_mk_run(encounter_id=99, dispels=0, interrupts=15)]
    # Dungeon 99 has confirmed-empty dispellables.
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=()):
        sampled = _score_utility_dps_tank(runs, class_id=8)
    # Same run against an unsampled dungeon = legacy behavior (dispel
    # component stays in at 0).
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=None):
        legacy = _score_utility_dps_tank(runs, class_id=8)
    # Under the no-opportunity path, dispel weight redistributes away.
    # Legacy path keeps dispel=0 counted, so the redistributed path
    # should score higher.
    assert sampled > legacy


def test_dps_unsampled_dungeon_preserves_legacy_behavior():
    """A dungeon that hasn't been sampled yet (dispellable_debuffs=None)
    must not silently change scoring behavior. This is the back-compat
    gate — crucial during rollout when only some dungeons are populated."""
    runs = [_mk_run(encounter_id=99, dispels=0, interrupts=15, cc_casts=10)]
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=None):
        # Legacy: dispel component in at 0.
        score_unsampled = _score_utility_dps_tank(runs, class_id=8)
    # Replicate the same run pre-refactor by routing through the non-
    # dispel branch via class_id that can't dispel — should differ.
    score_no_class_dispel = _score_utility_dps_tank(
        [_mk_run(encounter_id=99, dispels=0, interrupts=15, cc_casts=10)],
        class_id=4,  # Rogue - no dispel
    )
    # Mage's score with dispels=0 in unsampled dungeon must be LOWER
    # than a Rogue's (Rogue gets the dispel weight redistributed to
    # kicks + CC). This confirms unsampled behavior preserves the
    # dispel-penalty for dispel-capable classes.
    assert score_unsampled < score_no_class_dispel


def test_dps_sampled_with_data_same_as_legacy():
    """A dungeon sampled with non-empty dispellables should score the
    same as legacy (opportunity exists, dispels count normally)."""
    runs = [_mk_run(encounter_id=99, dispels=3, interrupts=15, cc_casts=8)]
    with patch(
        "app.scoring.engine.get_dispellable_debuffs",
        return_value=((12345, "Some Debuff"),),
    ):
        sampled = _score_utility_dps_tank(runs, class_id=8)
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=None):
        legacy = _score_utility_dps_tank(runs, class_id=8)
    assert sampled == legacy


# ── Healer scorer ────────────────────────────────────────────────────────────


def test_healer_no_opportunity_drops_dispel_weight():
    """Resto Druid with 0 dispels in a no-dispel dungeon shouldn't get
    crushed to a tiny utility score. Pre-fix this would return ~0
    (dispel_score=0 * 75% + tiny CC). Post-fix the dispel weight
    redistributes out and the score reflects actual kicks + CC."""
    runs = [_mk_run(
        encounter_id=99, dispels=0, interrupts=0, cc_casts=6,
        role=Role.healer, spec="Restoration",
    )]
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=()):
        no_opp = _score_utility_healer(runs, class_id=11)
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=None):
        legacy = _score_utility_healer(runs, class_id=11)
    # No-opportunity path: dispel drops, CC is the only signal -> 100.
    # Legacy: dispel at 0 * 75% + CC at 100 * 25% = 25.
    assert no_opp > legacy
    assert no_opp >= 90  # cc_casts=6 ≈ 100 and it's the only component
    assert legacy <= 30  # dispel penalty dominates


def test_healer_sampled_with_data_matches_legacy():
    """A dungeon with confirmed dispellables should score like legacy —
    no change in behavior for the dungeons that have dispels."""
    runs = [_mk_run(
        encounter_id=99, dispels=4, interrupts=0, cc_casts=3,
        role=Role.healer, spec="Restoration",
    )]
    with patch(
        "app.scoring.engine.get_dispellable_debuffs",
        return_value=((12345, "X"),),
    ):
        sampled = _score_utility_healer(runs, class_id=11)
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=None):
        legacy = _score_utility_healer(runs, class_id=11)
    assert sampled == legacy


def test_healer_per_dungeon_benchmark_scales_with_volume():
    """Same number of landed dispels should score differently in a
    dispel-poor dungeon vs a dispel-heavy one. Pre-fix both scored
    against a flat 8. Post-fix Skyreach's ~6/run expected vs Pit of
    Saron's ~65/run expected produces very different outcomes."""
    # 5 dispels in dispel-heavy (benchmark 65) = 5/65 * 100 ≈ 7.7
    # 5 dispels in dispel-poor (benchmark 6) = 5/6 * 100 ≈ 83 (capped at 100 naturally)
    runs_heavy = [_mk_run(
        encounter_id=99, dispels=5, interrupts=0, cc_casts=None,
        role=Role.healer, spec="Restoration",
    )]
    with patch(
        "app.scoring.engine.get_dispellable_debuffs",
        return_value=((1, "X"),),
    ), patch(
        "app.scoring.engine.get_expected_defensive_dispels_per_run",
        return_value=65.0,
    ):
        heavy_score = _score_utility_healer(runs_heavy, class_id=11)

    with patch(
        "app.scoring.engine.get_dispellable_debuffs",
        return_value=((1, "X"),),
    ), patch(
        "app.scoring.engine.get_expected_defensive_dispels_per_run",
        return_value=6.0,
    ):
        poor_score = _score_utility_healer(runs_heavy, class_id=11)

    # Same 5 dispels should look much better in the dispel-poor dungeon.
    assert poor_score > heavy_score
    assert poor_score > 75
    assert heavy_score < 15


def test_healer_unsampled_dungeon_uses_legacy_benchmark():
    """A dungeon without a per-dungeon benchmark should fall back to 8,
    preserving back-compat during rollout before every dungeon's been
    sampled for volume."""
    runs = [_mk_run(
        encounter_id=99, dispels=8, interrupts=0, cc_casts=None,
        role=Role.healer, spec="Restoration",
    )]
    with patch(
        "app.scoring.engine.get_dispellable_debuffs",
        return_value=((1, "X"),),
    ), patch(
        "app.scoring.engine.get_expected_defensive_dispels_per_run",
        return_value=None,  # unsampled
    ):
        score = _score_utility_healer(runs, class_id=11)
    # 8 dispels / flat 8 benchmark * 100 = 100
    assert score == 100


def test_healer_no_opportunity_no_kicks_no_cc_fallback_to_neutral():
    """Edge case: Resto Druid (no kick) in a no-dispel dungeon that
    somehow also has no CC tracked on the run. Score must not crash
    to 0 (which would be "you played terribly" when in fact there was
    nothing to score)."""
    runs = [_mk_run(
        encounter_id=99, dispels=0, interrupts=0, cc_casts=0,
        role=Role.healer, spec="Restoration",
    )]
    # Monkey-patch the cc_casts=None case (pre-tracking legacy runs).
    runs[0].cc_casts = None
    with patch("app.scoring.engine.get_dispellable_debuffs", return_value=()):
        score = _score_utility_healer(runs, class_id=11)
    # Neutral 50 — the "we have nothing to score you on" fallback.
    assert score == 50.0
