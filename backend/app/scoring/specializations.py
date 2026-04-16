"""Blizzard specialization-id → (class_id, spec_name) lookup.

Used when decoding Blizzard API responses that expose `specialization.id`
(mythic keystone leaderboards, character profiles) — we need the class
id + spec name to upsert Player rows and route scoring.

Class ids match WCL's classID mapping (1-13) so the rest of the pipeline
stays agnostic to where the spec came from.

Spec names match the labels used in `app.scoring.roles.SPEC_ROLE_MAP`.
"""
from __future__ import annotations

# (class_id, spec_name)
SPEC_ID_TO_CLASS: dict[int, tuple[int, str]] = {
    # Warrior (1)
    71: (1, "Arms"),
    72: (1, "Fury"),
    73: (1, "Protection"),
    # Paladin (2)
    65: (2, "Holy"),
    66: (2, "Protection"),
    70: (2, "Retribution"),
    # Hunter (3)
    253: (3, "Beast Mastery"),
    254: (3, "Marksmanship"),
    255: (3, "Survival"),
    # Rogue (4)
    259: (4, "Assassination"),
    260: (4, "Outlaw"),
    261: (4, "Subtlety"),
    # Priest (5)
    256: (5, "Discipline"),
    257: (5, "Holy"),
    258: (5, "Shadow"),
    # Death Knight (6)
    250: (6, "Blood"),
    251: (6, "Frost"),
    252: (6, "Unholy"),
    # Shaman (7)
    262: (7, "Elemental"),
    263: (7, "Enhancement"),
    264: (7, "Restoration"),
    # Mage (8)
    62: (8, "Arcane"),
    63: (8, "Fire"),
    64: (8, "Frost"),
    # Warlock (9)
    265: (9, "Affliction"),
    266: (9, "Demonology"),
    267: (9, "Destruction"),
    # Monk (10)
    268: (10, "Brewmaster"),
    269: (10, "Windwalker"),
    270: (10, "Mistweaver"),
    # Druid (11)
    102: (11, "Balance"),
    103: (11, "Feral"),
    104: (11, "Guardian"),
    105: (11, "Restoration"),
    # Demon Hunter (12)
    577: (12, "Havoc"),
    581: (12, "Vengeance"),
    # (12, "Devourer") — Midnight-added 4th DH spec. Spec ID unknown
    # until we see one in a live leaderboard response; populate then.
    # Evoker (13)
    1467: (13, "Devastation"),
    1468: (13, "Preservation"),
    1473: (13, "Augmentation"),
}


def resolve_spec(spec_id: int) -> tuple[int, str] | None:
    """Look up (class_id, spec_name) for a Blizzard specialization id.

    Returns None if the spec id is unknown — caller should log + skip
    the leaderboard entry rather than fall back to a guess.
    """
    return SPEC_ID_TO_CLASS.get(spec_id)
