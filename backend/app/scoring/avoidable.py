"""Avoidable damage ability IDs per M+ dungeon.

These are abilities that players should dodge, move out of, or avoid entirely.
Getting hit by these indicates poor awareness / mechanics knowledge.

Organized by encounter_id (WCL dungeon encounter ID).
Each entry is a set of (ability_id, ability_name) tuples.

This list covers current M+ Season 1 (Midnight) dungeons.
Ability IDs sourced from WCL damage-taken breakdowns and community resources.
"""

# encounter_id -> [(ability_id, ability_name), ...]
AVOIDABLE_ABILITIES: dict[int, list[tuple[int, str]]] = {
    # ── Pit of Saron (10658) ─────────────────────────────────────────────
    10658: [
        (69021, "Icy Blast"),
        (69024, "Icy Blast Ground"),
        (68989, "Overlord's Brand"),
        (69012, "Explosive Barrage"),
        (70827, "Ice Shards"),
    ],

    # ── Maisara Caverns (12874) ──────────────────────────────────────────
    12874: [
        # Placeholder - needs real ability IDs from WCL
    ],

    # ── Nexus-Point Xenas (12915) ────────────────────────────────────────
    12915: [
        # Placeholder - needs real ability IDs from WCL
    ],

    # ── Seat of the Triumvirate (361753) ─────────────────────────────────
    361753: [
        (244598, "Void Diffusion"),
        (246026, "Collapsing Void"),
        (244579, "Hungering Vortex"),
        (248133, "Felblaze Rush"),
    ],

    # ── Algeth'ar Academy (112526) ───────────────────────────────────────
    112526: [
        (388862, "Astral Whirlwind"),
        (388537, "Mana Void"),
        (388954, "Arcane Fissure"),
    ],

    # ── Skyreach (not yet mapped) ────────────────────────────────────────
    # ── Windrunner Spire (not yet mapped) ────────────────────────────────

    # ── Common trash mob avoidable abilities (appear across dungeons) ────
    # These can be checked regardless of encounter_id
}

# Abilities that are avoidable regardless of dungeon (common mob/affix abilities)
UNIVERSAL_AVOIDABLE: list[tuple[int, str]] = [
    (209862, "Volcanic Plume"),       # Volcanic affix
    (240559, "Grievous Wound"),       # Grievous affix (avoidable by staying above 90%)
    (343520, "Storming"),             # Storming affix
    (342494, "Belligerent Boast"),    # Prideful
]


def get_avoidable_abilities(encounter_id: int) -> set[int]:
    """Get the set of avoidable ability IDs for a dungeon encounter.

    Returns ability IDs (not names) for fast lookup.
    Includes both dungeon-specific and universal avoidable abilities.
    """
    ids = set()

    # Dungeon-specific
    for ability_id, _ in AVOIDABLE_ABILITIES.get(encounter_id, []):
        ids.add(ability_id)

    # Universal
    for ability_id, _ in UNIVERSAL_AVOIDABLE:
        ids.add(ability_id)

    return ids


def get_all_avoidable_ability_ids() -> set[int]:
    """Get all known avoidable ability IDs across all dungeons."""
    ids = set()
    for abilities in AVOIDABLE_ABILITIES.values():
        for ability_id, _ in abilities:
            ids.add(ability_id)
    for ability_id, _ in UNIVERSAL_AVOIDABLE:
        ids.add(ability_id)
    return ids
