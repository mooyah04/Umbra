"""Player identity validation — names, realms, regions."""
import pytest

from app.validators import (
    ValidationError,
    realm_to_slug,
    validate_name,
    validate_player_identity,
    validate_realm,
    validate_region,
)


# ── Region ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("us", "US"),
    ("EU", "EU"),
    ("  kr ", "KR"),
    ("Tw", "TW"),
])
def test_region_canonicalizes(raw, expected):
    assert validate_region(raw) == expected


@pytest.mark.parametrize("bad", ["", "USA", "xx", "eur", None])
def test_region_rejects_bad(bad):
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        validate_region(bad)


# ── Names ───────────────────────────────────────────────────────────────────

def test_name_strips_whitespace():
    assert validate_name("  Mooyuh  ") == "Mooyuh"


def test_name_titlecases_first_letter():
    assert validate_name("mooyuh") == "Mooyuh"


def test_name_preserves_accented_chars():
    assert validate_name("élonmunk") == "Élonmunk"


def test_name_rejects_slashes():
    # Path-injection-ish payloads
    with pytest.raises(ValidationError):
        validate_name("Foo/Bar")
    with pytest.raises(ValidationError):
        validate_name("Foo\\Bar")


def test_name_rejects_empty_and_whitespace():
    for bad in ["", "   ", "\t", "\n"]:
        with pytest.raises(ValidationError):
            validate_name(bad)


def test_name_rejects_too_long():
    with pytest.raises(ValidationError):
        validate_name("A" * 30)


def test_name_rejects_too_short():
    with pytest.raises(ValidationError):
        validate_name("A")


def test_name_strips_control_chars():
    # Null byte attempt
    assert validate_name("Mooyuh\x00") == "Mooyuh"


# ── Realms ──────────────────────────────────────────────────────────────────

def test_realm_preserves_spaces():
    assert validate_realm("Tarren Mill") == "Tarren Mill"


def test_realm_preserves_apostrophes():
    assert validate_realm("Zul'jin") == "Zul'jin"


def test_realm_preserves_hyphens():
    assert validate_realm("Azjol-Nerub") == "Azjol-Nerub"


def test_realm_collapses_multiple_spaces():
    assert validate_realm("Tarren   Mill") == "Tarren Mill"


def test_realm_rejects_slashes():
    with pytest.raises(ValidationError):
        validate_realm("Foo/Bar")


def test_realm_rejects_empty():
    for bad in ["", "   ", "\t"]:
        with pytest.raises(ValidationError):
            validate_realm(bad)


# ── Realm slug ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("display,slug", [
    ("Tarren Mill", "tarren-mill"),
    ("Zul'jin", "zuljin"),
    ("Azjol-Nerub", "azjol-nerub"),
    ("Area 52", "area-52"),
])
def test_realm_to_slug(display, slug):
    assert realm_to_slug(display) == slug


# ── Combined ────────────────────────────────────────────────────────────────

def test_validate_player_identity_happy_path():
    name, realm, region = validate_player_identity(
        "  mooyuh  ", "Tarren Mill", "eu"
    )
    assert (name, realm, region) == ("Mooyuh", "Tarren Mill", "EU")


def test_validate_player_identity_raises_first_error():
    """First invalid field should bubble up with a useful message."""
    with pytest.raises(ValidationError) as ei:
        validate_player_identity("X", "Tarren Mill", "EU")
    assert "name length" in str(ei.value).lower()
