"""Input validation for player identity (name/realm/region).

Centralizing this means every entry point — HTTP routes, bulk ingest body,
crawler CLI — applies the same rules. Character names and realm names reach
WCL's API and our DB, so garbage input shows up in both as cache misses and
row-level clutter.

Design principles:
- Reject early with a clear message; don't silently coerce.
- Normalize to a canonical form so cache lookups ("ZuLjIn" vs "Zuljin") hit.
- Be permissive about unicode in display names (WoW allows accented chars)
  but strict about control characters, path separators, and length bounds.
"""
from __future__ import annotations

import re
import unicodedata

# WoW character name rules (Blizzard): letters only (including accented), 2-12 chars.
# We stay slightly looser on length to tolerate clients that don't normalize,
# but still reject anything with slashes, control chars, or HTML-ish content.
_NAME_MAX = 24
_NAME_MIN = 2
_REALM_MAX = 50
_REALM_MIN = 2

# Accept letters (any script), combining marks, apostrophes, spaces, hyphens.
_NAME_ALLOWED = re.compile(r"^[^\s/\\]+$", re.UNICODE)
_REALM_ALLOWED = re.compile(r"^[\w\s'\-]+$", re.UNICODE)

VALID_REGIONS = frozenset({"US", "EU", "KR", "TW", "CN"})


class ValidationError(ValueError):
    """Raised when player identity input fails validation."""


def _strip_control_chars(s: str) -> str:
    """Remove C0/C1 control characters while preserving all printable glyphs."""
    return "".join(c for c in s if unicodedata.category(c)[0] != "C")


def validate_region(region: str) -> str:
    """Return the canonical upper-case region code, or raise ValidationError."""
    if not region:
        raise ValidationError("region is required")
    normalized = region.strip().upper()
    if normalized not in VALID_REGIONS:
        raise ValidationError(
            f"invalid region '{region}': must be one of {sorted(VALID_REGIONS)}"
        )
    return normalized


def validate_name(name: str) -> str:
    """Canonicalize a character name.

    Returns the stripped name with NFC unicode normalization and title-case
    first letter. Rejects empty, too-long, slash-containing, or non-printable
    input.
    """
    if not name:
        raise ValidationError("name is required")
    cleaned = _strip_control_chars(name).strip()
    cleaned = unicodedata.normalize("NFC", cleaned)
    if not cleaned:
        raise ValidationError("name is empty after stripping")
    if len(cleaned) < _NAME_MIN or len(cleaned) > _NAME_MAX:
        raise ValidationError(
            f"name length {len(cleaned)} out of range ({_NAME_MIN}-{_NAME_MAX})"
        )
    if not _NAME_ALLOWED.match(cleaned):
        raise ValidationError(
            f"name '{name}' contains disallowed characters (whitespace or path separator)"
        )
    # First letter upper-case to match Blizzard display convention.
    return cleaned[0].upper() + cleaned[1:]


def validate_realm(realm: str) -> str:
    """Canonicalize a realm display name.

    Accepts spaces, apostrophes, hyphens; rejects slashes and control chars.
    Returns the trimmed, NFC-normalized display form. Use `realm_to_slug` to
    produce the WCL-friendly slug from this output.
    """
    if not realm:
        raise ValidationError("realm is required")
    cleaned = _strip_control_chars(realm).strip()
    cleaned = unicodedata.normalize("NFC", cleaned)
    # Collapse any run of whitespace to a single space (handles double-spaces).
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        raise ValidationError("realm is empty after stripping")
    if len(cleaned) < _REALM_MIN or len(cleaned) > _REALM_MAX:
        raise ValidationError(
            f"realm length {len(cleaned)} out of range ({_REALM_MIN}-{_REALM_MAX})"
        )
    if not _REALM_ALLOWED.match(cleaned):
        raise ValidationError(
            f"realm '{realm}' contains disallowed characters"
        )
    return cleaned


def realm_to_slug(realm: str) -> str:
    """Convert a realm display name to the WCL URL slug.

    "Tarren Mill"  -> "tarren-mill"
    "Zul'jin"      -> "zuljin"
    "Azjol-Nerub"  -> "azjol-nerub"
    """
    slug = realm.lower().replace("'", "").replace(" ", "-")
    # Collapse double-hyphens that could form from odd inputs.
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def validate_player_identity(
    name: str, realm: str, region: str
) -> tuple[str, str, str]:
    """Validate all three at once, returning the canonical tuple.

    Raises ValidationError with the first problem encountered.
    """
    return validate_name(name), validate_realm(realm), validate_region(region)
