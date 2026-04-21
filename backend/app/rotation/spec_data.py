"""Per-spec rotation data — the source of truth for classifying a
player's cast timeline into rotation / cooldown / utility buckets, for
merging fragmented spell IDs (Odyn's Fury is four IDs in the combat log
but one button for the player), and for showing a reference opener the
player can compare themselves against.

Each spec has its own module under `specs/`. Data is stubbed but
additive — a spec without a module falls back to the unclassified Phase 1
display. Adding a new spec is purely additive: drop a file in `specs/`,
register it in registry.py, and the lookup picks it up.

Coverage priority is by popularity. Fury Warrior is the pilot spec used
to validate the pipeline end-to-end before fanning out to other specs.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OpenerStep:
    """One step in the reference opener sequence.

    `spell_id` is the canonical (post-alias) ID the frontend will match
    against the player's actual casts. `note` is optional free-form text
    — "pre-pull", "hold until proc", etc. — shown under the icon.
    """
    spell_id: int
    name: str
    icon: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class SpecRotationData:
    key: str
    display_name: str
    class_id: int
    spec_name: str
    # Merge map: fragment_spell_id -> canonical_spell_id. Applied before
    # any other classification so downstream lookups only ever see the
    # canonical ID. Example: Odyn's Fury has four IDs in WCL events
    # (main-hand hit, main-hand proc, off-hand hit, off-hand proc) that
    # all represent one button press to the player.
    aliases: dict[int, int] = field(default_factory=dict)
    # Core damage-dealing / resource-generating / spender abilities that
    # show up on the "Rotation" tab of every guide.
    rotation_ids: frozenset[int] = frozenset()
    # Major cooldowns (offensive + defensive). Shown in a dedicated
    # section so users can see CD usage patterns distinctly from
    # filler rotation.
    cooldown_ids: frozenset[int] = frozenset()
    # Kicks, CC, dispels, movement, defensives — useful to track but
    # not part of the DPS rotation comparison.
    utility_ids: frozenset[int] = frozenset()
    # Trinket procs, dungeon item casts, racials, and other noise that
    # shouldn't show up as "rotation" at all. Filtered out before the
    # response goes to the frontend.
    ignore_ids: frozenset[int] = frozenset()
    # Reference opener — ordered list of expected early casts. Frontend
    # displays this side-by-side with the player's actual opener so the
    # user can see their own deviation from the guide.
    reference_opener: tuple[OpenerStep, ...] = ()
    # Public rotation guide link. Frontend surfaces as "Full rotation
    # guide" button. Phase 2 uses Icy Veins as the standard source; can
    # be overridden per spec if a better guide exists.
    guide_url: str | None = None
    # Short attribution + date-reviewed line so future curators know
    # when the data was last sanity-checked.
    last_reviewed: str | None = None


def classify(data: SpecRotationData, spell_id: int) -> str:
    """Return the category tag for a post-alias spell ID.

    "rotation" | "cooldown" | "utility" | "unknown". Callers should
    handle "unknown" as "display but don't group" — most likely a
    curation gap (spec data missing an entry) worth flagging.
    """
    if spell_id in data.rotation_ids:
        return "rotation"
    if spell_id in data.cooldown_ids:
        return "cooldown"
    if spell_id in data.utility_ids:
        return "utility"
    return "unknown"


def resolve_alias(data: SpecRotationData, spell_id: int) -> int:
    """Return the canonical spell ID for a fragment, or the ID itself."""
    return data.aliases.get(spell_id, spell_id)
