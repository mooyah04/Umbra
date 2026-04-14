"""Which classes have a practical dispel in PvE.

Scoring a class on dispels when they literally can't cast one (Rogue, DK,
Warrior, DH) is unfair — a perfectly-played Rogue is capped at 80/100 on
utility no matter what. When the class has no dispel, the utility scorer
should redistribute the dispel weight to interrupts and CC instead.

Dispel coverage here is intentionally strict: "does the class have at
least one generally-useful dispel they'd actually press in M+?" Cases
like Warrior's Shattering Throw (offensive magic immunity, situational)
don't count.
"""

# Class IDs that have a dispel useful in PvE M+.
CLASSES_WITH_DISPEL: set[int] = {
    2,   # Paladin — Cleanse (Poison/Disease, Magic for Holy)
    3,   # Hunter — Tranquilizing Shot (Magic/Enrage on enemies, dispel debuffs off friendly)
    5,   # Priest — Purify / Dispel Magic / Mass Dispel
    7,   # Shaman — Purify Spirit (Resto), Cleanse Spirit (Enh)
    8,   # Mage — Remove Curse
    9,   # Warlock — Singe Magic (Imp) / Sear Magic (Felhunter)
    10,  # Monk — Detox (Poison/Disease, Magic for MW)
    11,  # Druid — Nature's Cure / Remove Corruption
    13,  # Evoker — Expunge (Poison) / Naturalize (Preservation adds Magic)
}

# Classes that cannot dispel meaningfully in PvE M+.
# Rogue (4), Warrior (1), Death Knight (6), Demon Hunter (12).


def class_has_dispel(class_id: int | None) -> bool:
    """True if the class has at least one dispel they'd use in M+."""
    return class_id in CLASSES_WITH_DISPEL
