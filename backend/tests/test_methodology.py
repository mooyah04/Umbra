"""Spec-aware methodology builder.

Spot-checks that the pre-rendered copy produced by build_methodology()
lines up with the underlying scoring data for representative specs
(healer without a kick, rogue without a dispel, healer with a kick).

Failing any of these most likely means the interrupt/dispel override
tables in methodology.py have drifted from the authoritative capability
modules — not an actual regression in the engine itself.
"""
from app.scoring.methodology import build_methodology


def test_resto_druid_has_no_interrupt_and_can_dispel():
    # Resto Druid is the canonical "healer without a kick" case. Utility
    # scoring redistributes the interrupt weight to dispels + CC, so the
    # copy has to reflect that or the player reads the number wrong.
    m = build_methodology(11, "Restoration")
    assert m["class_name"] == "Druid"
    assert m["role"] == "healer"
    assert m["interrupt"]["has_interrupt"] is False
    assert m["interrupt"]["ability_name"] is None
    assert m["dispels"]["can_dispel"] is True
    # Resto Druid's Magic dispel comes from Nature's Cure — the dispel
    # text should mention it explicitly.
    assert "Nature's Cure" in (m["dispels"]["text"] or "")
    # Major CDs should include Tranquility (baseline) and Convoke.
    cd_names = [cd["name"] for cd in m["major_cooldowns"]]
    assert "Tranquility" in cd_names
    assert "Convoke the Spirits" in cd_names
    # The utility paragraph must say "no interrupt" clearly — otherwise
    # the user reads it thinking their (zero) kicks tanked their grade.
    util_desc = m["categories"]["utility"]["description"]
    assert "doesn't have a baseline interrupt" in util_desc
    assert "Nature's Cure" in util_desc


def test_assassination_rogue_has_kick_but_no_dispel():
    # Rogue is the canonical "DPS without a dispel" case. Utility weight
    # should redistribute from dispels into kicks + CC.
    m = build_methodology(4, "Assassination")
    assert m["role"] == "dps"
    assert m["interrupt"]["ability_name"] == "Kick"
    assert m["dispels"]["can_dispel"] is False
    assert m["dispels"]["text"] is None
    util_desc = m["categories"]["utility"]["description"]
    assert "Kick" in util_desc
    assert "no practical PvE dispel" in util_desc


def test_holy_paladin_is_healer_with_interrupt():
    # Holy Paladin and Resto Shaman are the two healer specs with a kick.
    # Copy should say "you have a baseline interrupt" rather than the
    # no-kick framing — regression target since the override table
    # is handled by fall-through to class-level, not explicit override.
    m = build_methodology(2, "Holy")
    assert m["role"] == "healer"
    assert m["interrupt"]["has_interrupt"] is True
    assert m["interrupt"]["ability_name"] == "Rebuke"
    # Holy Pally Cleanse upgrades to also remove Magic.
    assert "Magic" in (m["dispels"]["text"] or "")
    util_desc = m["categories"]["utility"]["description"]
    assert "baseline interrupt (Rebuke)" in util_desc


def test_balance_druid_uses_solar_beam_not_class_fallback():
    # Druid interrupts are spec-specific (no class-level fallback).
    # Confirm the override table is the resolver, not a silent None.
    m = build_methodology(11, "Balance")
    assert m["interrupt"]["ability_name"] == "Solar Beam"


def test_guardian_druid_skull_bash():
    m = build_methodology(11, "Guardian")
    assert m["interrupt"]["ability_name"] == "Skull Bash"


def test_preservation_evoker_has_no_kick():
    # Pres is the one Evoker spec without Quell.
    m = build_methodology(13, "Preservation")
    assert m["interrupt"]["has_interrupt"] is False


def test_augmentation_evoker_has_quell():
    m = build_methodology(13, "Augmentation")
    assert m["interrupt"]["ability_name"] == "Quell"


def test_cooldown_copy_names_the_tracked_cds():
    # Fire Mage is scored on Combustion. The copy has to surface that
    # ability name explicitly so players can go "oh, I should press that".
    m = build_methodology(8, "Fire")
    cd_desc = m["categories"]["cooldown_usage"]["description"]
    assert "Combustion" in cd_desc


def test_spec_without_tracked_cds_explains_the_gap():
    # Affliction has no BuffsTable-visible major CD right now (see
    # cooldowns.py comments). Methodology should frame this as a data
    # gap, not as "you're bad at using CDs".
    m = build_methodology(9, "Affliction")
    cd_desc = m["categories"]["cooldown_usage"]["description"]
    cd_improve = m["categories"]["cooldown_usage"]["howToImprove"]
    # Description must explain the gap; improve text must absolve the
    # player (the blank grade isn't their fault).
    assert "reliably-trackable" in cd_desc or "debuff-detection" in cd_desc
    assert "data-availability" in cd_improve or "nothing you can do" in cd_improve.lower()


def test_unknown_spec_degrades_cleanly():
    # Endpoint receives spec_name as a URL param, so an unknown value
    # (typo, deprecated spec, test scrape) must not 500 — it should
    # fall back to DPS-shaped data.
    m = build_methodology(1, "NotARealSpec")
    assert m["role"] == "dps"
    # Warrior's interrupt is Pummel via class-level fallback.
    assert m["interrupt"]["ability_name"] == "Pummel"


def test_cpm_benchmark_uses_spec_override():
    # Fury Warrior lives in SPEC_BENCHMARKS with excellent=52. The
    # copy should surface the same numbers the scorer applies.
    m = build_methodology(1, "Fury")
    b = m["cpm_benchmark"]
    assert b["excellent"] == 52
    cpm_desc = m["categories"]["casts_per_minute"]["description"]
    assert "52" in cpm_desc
