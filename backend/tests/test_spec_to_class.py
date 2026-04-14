"""Spec name → class_id resolver, including ambiguous specs."""
import pytest

from app.scoring.spec_to_class import (
    AMBIGUOUS_SPECS,
    UNAMBIGUOUS_SPEC_TO_CLASS,
    resolve_class_id,
)


def test_brewmaster_overrides_wrong_wcl_class():
    """The exact case that broke Elonmunk's ingest: WCL returned classID=5
    (Priest) but per-fight spec was Brewmaster (Monk). Resolver must pick
    Monk, not trust WCL."""
    assert resolve_class_id("Brewmaster", 5) == 10


@pytest.mark.parametrize("spec,expected", list(UNAMBIGUOUS_SPEC_TO_CLASS.items()))
def test_unambiguous_specs_pin_class(spec, expected):
    # Regardless of what WCL says, unambiguous spec wins.
    assert resolve_class_id(spec, 999) == expected


def test_ambiguous_frost_prefers_wcl_dk():
    assert resolve_class_id("Frost", 6) == 6  # DK
    assert resolve_class_id("Frost", 8) == 8  # Mage


def test_ambiguous_frost_falls_back_when_wcl_bogus():
    # Neither 6 nor 8 — pick first option (DK).
    assert resolve_class_id("Frost", 2) == 6
    assert resolve_class_id("Frost", None) == 6


def test_ambiguous_restoration():
    assert resolve_class_id("Restoration", 7) == 7   # Shaman
    assert resolve_class_id("Restoration", 11) == 11 # Druid
    assert resolve_class_id("Restoration", 99) == 7  # fallback to first


def test_unknown_spec_trusts_wcl():
    assert resolve_class_id("NotARealSpec", 5) == 5


def test_both_unknown_returns_none():
    assert resolve_class_id(None, None) is None
    assert resolve_class_id("NotASpec", None) is None


def test_every_ambiguous_entry_has_at_least_one_option():
    for spec, opts in AMBIGUOUS_SPECS.items():
        assert len(opts) >= 1, f"{spec} has no class options"
