"""Fairness-focused tests for scoring edge cases.

These lock in the audit fixes:
- Non-dispelling classes don't lose points for not dispelling.
- Healers who use CC get credit for it.
- DTPS/HRPS thresholds scale with key level (high keys don't auto-penalize).
- Softer death curve.
- has_cc_data check is per-run, not across-the-run-set.
"""
from datetime import datetime

import pytest

from app.models import DungeonRun, Role
from app.scoring.dispel_capability import CLASSES_WITH_DISPEL, class_has_dispel
from app.scoring.engine import (
    _score_survivability,
    _score_utility_dps_tank,
    _score_utility_healer,
)


def _run(role=Role.dps, spec="Frost", keystone_level=10, **kw) -> DungeonRun:
    defaults = dict(
        role=role, spec_name=spec, keystone_level=keystone_level,
        encounter_id=10658, dps=60, hps=0, ilvl=620, duration=1_800_000,
        deaths=0, interrupts=8, dispels=0,
        avoidable_damage_taken=0, damage_taken_total=0,
        casts_total=900, cooldown_usage_pct=70, timed=True,
        logged_at=datetime(2026, 4, 1), wcl_report_id="r1", fight_id=1,
    )
    defaults.update(kw)
    return DungeonRun(**defaults)


# ── #1 Non-dispelling classes shouldn't lose points for no dispels ─────────

def test_rogue_perfect_kicks_can_reach_near_100():
    """A Rogue (class 4, no dispel) who kicks perfectly and uses CC well
    should hit near-100 on utility — previously capped at ~80 due to dispel
    weight they couldn't earn."""
    runs = [_run(interrupts=15, dispels=0, cc_casts=10)]
    score = _score_utility_dps_tank(runs, class_id=4)  # Rogue
    assert score >= 99, f"Rogue perfect-play utility too low: {score}"


def test_shaman_perfect_play_also_high():
    """Control: a Shaman (class 7, has dispel) in equivalent perfect play
    should also reach near-100 — the dispel slot isn't wasted."""
    runs = [_run(interrupts=15, dispels=5, cc_casts=10)]
    score = _score_utility_dps_tank(runs, class_id=7)
    assert score >= 99


def test_rogue_not_penalized_for_0_dispels_shaman_is():
    """A Rogue with 0 dispels shouldn't be scored on them at all; a Shaman
    with 0 dispels IS scored down because the dispel is in their kit and
    they chose not to use it. Rogue score should be strictly higher for
    the same interrupt count."""
    runs = [_run(interrupts=10, dispels=0, cc_casts=None)]
    rogue_score = _score_utility_dps_tank(runs, class_id=4)
    shaman_score = _score_utility_dps_tank(runs, class_id=7)
    assert rogue_score > shaman_score, \
        f"Rogue ({rogue_score}) should beat same-kick Shaman ({shaman_score})"


def test_class_has_dispel_covers_every_healer_class():
    """Every healer class must have dispel capability — healers are the
    dispel workhorses in M+."""
    for class_id in (2, 5, 7, 10, 11, 13):  # Pal, Pri, Sham, Monk, Druid, Evoker
        assert class_has_dispel(class_id)


def test_non_dispelling_classes_explicit():
    assert not class_has_dispel(1)   # Warrior
    assert not class_has_dispel(4)   # Rogue
    assert not class_has_dispel(6)   # DK
    assert not class_has_dispel(12)  # DH


# ── #2 Healers get credit for CC ────────────────────────────────────────────

def test_healer_cc_raises_utility_score():
    """A Mistweaver using Paralysis regularly should score higher on utility
    than one who doesn't."""
    base = [_run(role=Role.healer, spec="Mistweaver", dispels=6, interrupts=0,
                 cc_casts=0)]
    with_cc = [_run(role=Role.healer, spec="Mistweaver", dispels=6, interrupts=0,
                    cc_casts=8)]
    base_score = _score_utility_healer(base, class_id=10)
    cc_score = _score_utility_healer(with_cc, class_id=10)
    assert cc_score > base_score, \
        f"CC usage should raise healer utility: base={base_score}, cc={cc_score}"


def test_healer_no_cc_data_falls_back_to_dispel_only():
    """Old runs without cc_casts tracking shouldn't be penalized.

    Uses a sentinel encounter_id not in the registry so the healer
    scorer falls back to the legacy flat-8 dispel benchmark. If this
    test used a real active-season encounter, the per-dungeon
    benchmark (e.g. Pit of Saron ~65) would dominate the assertion
    and make "8 dispels should be a perfect score" wrong — which is
    a different behavior we test in test_scoring_dispel_opportunity.

    Uses Discipline Priest so the spec is NOT in
    `HEALER_SPECS_WITH_INTERRUPT` — otherwise the 0-interrupts
    fixture pulls the score down through the kick-credit path
    (Mistweaver was added to that set 2026-04-27 Batch 2 audit).
    """
    runs = [_run(role=Role.healer, spec="Discipline", dispels=8, interrupts=0,
                 cc_casts=None, encounter_id=99999)]
    score = _score_utility_healer(runs, class_id=5)
    # 8/8 dispels against the flat fallback benchmark = 100
    assert score == 100


def test_kicking_healer_still_scored_on_interrupts():
    """Resto Shaman (can kick) should still get interrupt credit."""
    no_kicks = [_run(role=Role.healer, spec="Restoration", dispels=8,
                     interrupts=0, cc_casts=None)]
    with_kicks = [_run(role=Role.healer, spec="Restoration", dispels=8,
                       interrupts=10, cc_casts=None)]
    # class_id=7 (Shaman) — can kick
    assert _score_utility_healer(with_kicks, class_id=7) > \
           _score_utility_healer(no_kicks, class_id=7)


# ── #3 DTPS/HRPS fallbacks scale with key level ────────────────────────────

def test_high_key_player_not_auto_branded_unsafe():
    """A +15 DPS taking 15k DTPS used to score ~10 (fail) on the old
    absolute thresholds. With key-level scaling, the multiplier at +15 is
    ~2.95, so 15k DTPS is well under the 10k*mult=29.5k 'good' threshold."""
    high_key = _run(
        role=Role.dps, keystone_level=15,
        damage_taken_total=15000 * 1800,  # 15k DTPS over 30-min key
        duration=1_800_000, deaths=0,
    )
    low_key = _run(
        role=Role.dps, keystone_level=2,
        damage_taken_total=15000 * 1800,  # same absolute DTPS at +2
        duration=1_800_000, deaths=0,
    )
    high_score = _score_survivability([high_key])
    low_score = _score_survivability([low_key])
    assert high_score > low_score + 15, \
        f"High-key player should score much higher: high={high_score}, low={low_score}"


def test_low_dtps_still_scores_100_at_any_key_level():
    """A clean run with tiny DTPS (e.g., skip a lot of damage) should
    still hit 100 regardless of key level."""
    runs = [_run(role=Role.dps, keystone_level=15,
                 damage_taken_total=1000 * 1800, duration=1_800_000, deaths=0)]
    # level_mult at +15 = 2.95. Threshold for "100" = 5000*2.95 = 14750
    # 1000 DTPS is well below → should get 100 on avoidable component.
    score = _score_survivability(runs)
    assert score >= 90  # death=100 + high avoidable + healing neutral


# ── #6 Softer death curve ──────────────────────────────────────────────────

def test_one_death_softer_penalty():
    """1 death should no longer drop you from 100 → 65. New curve: 1=80."""
    no_death = [_run(deaths=0, damage_taken_total=0)]
    one_death = [_run(deaths=1, damage_taken_total=0)]
    diff = _score_survivability(no_death) - _score_survivability(one_death)
    # Old diff: (100-65)*0.5 = 17.5. New: (100-80)*0.5 = 10. Much softer.
    assert diff < 15, f"1-death penalty still too harsh: {diff}"
    # But still negative — 1 death should still hurt.
    assert diff > 0


def test_five_deaths_still_zero():
    """Catastrophic deaths should still cap at 0 on the death component."""
    runs = [_run(deaths=5, damage_taken_total=0)]
    score = _score_survivability(runs)
    # death=0, avoidable fallback 75 (no data), healing neutral 75
    # = 0*0.5 + 75*0.25 + 75*0.25 = 37.5 (with healing_received=None fallback)
    # Actually healing_received defaults to None on our constructor, so
    # has_healing_data is False → score = 0*0.6 + 75*0.4 = 30
    assert score <= 40


# ── #8 Per-run has_cc check — mixed old/new runs ───────────────────────────

def test_mixed_old_and_new_runs_no_mutual_penalty():
    """If some runs have cc_casts tracked and others don't, old runs
    shouldn't be penalized for not having CC data."""
    old_run = _run(interrupts=10, dispels=0, cc_casts=None)   # pre-tracking
    new_run = _run(interrupts=10, dispels=0, cc_casts=8)      # with tracking

    # The old run's score should NOT include a 0-cc penalty.
    # Score old run in isolation = score when mixed with new run.
    old_alone = _score_utility_dps_tank([old_run], class_id=4)
    mixed = _score_utility_dps_tank([old_run, new_run], class_id=4)
    # Mixed score should reflect average of the two — if old was penalized
    # by CC-component-present, the math would be off.
    # Sanity check: both scores in reasonable range, mixed is between them.
    new_alone = _score_utility_dps_tank([new_run], class_id=4)
    assert min(old_alone, new_alone) <= mixed <= max(old_alone, new_alone) + 0.1
