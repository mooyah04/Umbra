"""Map a WCL spec name to a WoW class ID.

Why this exists: WCL's character endpoint occasionally returns the wrong
character entity (e.g., when two chars share a name on the same realm).
The per-fight spec_name WCL reports is reliable; the top-level classID
isn't. When the spec is unambiguous (belongs to only one class), we
derive class_id from the spec and override the potentially-wrong value.

Ambiguous specs (Frost, Restoration, Holy, Protection, Survival) share
names across classes — for those we return None and the caller should
fall back to WCL's classID.
"""

# Class IDs per Blizzard:
# 1 Warrior, 2 Paladin, 3 Hunter, 4 Rogue, 5 Priest, 6 DK, 7 Shaman,
# 8 Mage, 9 Warlock, 10 Monk, 11 Druid, 12 DH, 13 Evoker.

# Unambiguous specs — spec_name maps directly to one class.
UNAMBIGUOUS_SPEC_TO_CLASS: dict[str, int] = {
    # Warrior
    "Arms": 1, "Fury": 1,
    # Paladin
    "Retribution": 2,
    # Hunter
    "Beast Mastery": 3, "Marksmanship": 3,
    # Rogue
    "Assassination": 4, "Outlaw": 4, "Subtlety": 4,
    # Priest
    "Discipline": 5, "Shadow": 5,
    # Death Knight
    "Blood": 6, "Unholy": 6,
    # Shaman
    "Elemental": 7, "Enhancement": 7,
    # Mage
    "Arcane": 8, "Fire": 8,
    # Warlock
    "Affliction": 9, "Demonology": 9, "Destruction": 9,
    # Monk
    "Brewmaster": 10, "Mistweaver": 10, "Windwalker": 10,
    # Druid
    "Balance": 11, "Feral": 11, "Guardian": 11,
    # Demon Hunter
    "Havoc": 12, "Vengeance": 12,
    # Evoker
    "Devastation": 13, "Preservation": 13, "Augmentation": 13,
}

# Ambiguous specs — (spec_name, possible_class_ids).
# Callers should pick the one that matches WCL's classID; if WCL's value
# isn't among the options, fall back to the first (most common) class.
AMBIGUOUS_SPECS: dict[str, tuple[int, ...]] = {
    "Frost": (6, 8),            # DK or Mage
    "Restoration": (7, 11),     # Shaman or Druid
    "Holy": (2, 5),             # Paladin or Priest
    "Protection": (1, 2),       # Warrior or Paladin
    "Survival": (3,),           # Hunter only in modern WoW, kept here for safety
}


# Map WCL's per-fight 'type' field (class name) to the canonical class_id.
# WCL sometimes spells compound names joined ('DeathKnight') and sometimes
# spaced ('Death Knight'); accept both.
CLASS_NAME_TO_ID: dict[str, int] = {
    "Warrior": 1,
    "Paladin": 2,
    "Hunter": 3,
    "Rogue": 4,
    "Priest": 5,
    "DeathKnight": 6, "Death Knight": 6,
    "Shaman": 7,
    "Mage": 8,
    "Warlock": 9,
    "Monk": 10,
    "Druid": 11,
    "DemonHunter": 12, "Demon Hunter": 12,
    "Evoker": 13,
}


def class_id_from_name(class_name: str | None) -> int | None:
    """Return class_id from WCL's per-fight class-name string, or None if unknown."""
    if not class_name:
        return None
    # Normalize: strip whitespace, try both raw and space-less forms
    cleaned = class_name.strip()
    return CLASS_NAME_TO_ID.get(cleaned) or CLASS_NAME_TO_ID.get(cleaned.replace(" ", ""))


def resolve_class_id(spec_name: str | None, wcl_class_id: int | None) -> int | None:
    """Return the best-guess class_id for a (spec, WCL-reported class) pair.

    - Unambiguous spec wins over WCL's classID (override).
    - Ambiguous spec: prefer WCL's classID if it's a valid option; else first option.
    - Unknown spec: trust WCL's value.
    - Neither known: return None.
    """
    if spec_name and spec_name in UNAMBIGUOUS_SPEC_TO_CLASS:
        return UNAMBIGUOUS_SPEC_TO_CLASS[spec_name]

    if spec_name and spec_name in AMBIGUOUS_SPECS:
        options = AMBIGUOUS_SPECS[spec_name]
        if wcl_class_id in options:
            return wcl_class_id
        return options[0]

    return wcl_class_id
