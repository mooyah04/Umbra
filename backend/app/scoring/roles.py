"""Mapping of WoW class ID + spec name to role.

WoW class IDs (as of The War Within):
  1=Warrior, 2=Paladin, 3=Hunter, 4=Rogue, 5=Priest, 6=DeathKnight,
  7=Shaman, 8=Mage, 9=Warlock, 10=Monk, 11=Druid, 12=DemonHunter,
  13=Evoker
"""

from app.models import Role

# (class_id, spec_name) -> Role
# spec_name values match what WCL returns in encounterRankings
SPEC_ROLE_MAP: dict[tuple[int, str], Role] = {
    # Warrior (1)
    (1, "Arms"): Role.dps,
    (1, "Fury"): Role.dps,
    (1, "Protection"): Role.tank,
    # Paladin (2)
    (2, "Holy"): Role.healer,
    (2, "Protection"): Role.tank,
    (2, "Retribution"): Role.dps,
    # Hunter (3)
    (3, "Beast Mastery"): Role.dps,
    (3, "Marksmanship"): Role.dps,
    (3, "Survival"): Role.dps,
    # Rogue (4)
    (4, "Assassination"): Role.dps,
    (4, "Outlaw"): Role.dps,
    (4, "Subtlety"): Role.dps,
    # Priest (5)
    (5, "Discipline"): Role.healer,
    (5, "Holy"): Role.healer,
    (5, "Shadow"): Role.dps,
    # Death Knight (6)
    (6, "Blood"): Role.tank,
    (6, "Frost"): Role.dps,
    (6, "Unholy"): Role.dps,
    # Shaman (7)
    (7, "Elemental"): Role.dps,
    (7, "Enhancement"): Role.dps,
    (7, "Restoration"): Role.healer,
    # Mage (8)
    (8, "Arcane"): Role.dps,
    (8, "Fire"): Role.dps,
    (8, "Frost"): Role.dps,
    # Warlock (9)
    (9, "Affliction"): Role.dps,
    (9, "Demonology"): Role.dps,
    (9, "Destruction"): Role.dps,
    # Monk (10)
    (10, "Brewmaster"): Role.tank,
    (10, "Mistweaver"): Role.healer,
    (10, "Windwalker"): Role.dps,
    # Druid (11)
    (11, "Balance"): Role.dps,
    (11, "Feral"): Role.dps,
    (11, "Guardian"): Role.tank,
    (11, "Restoration"): Role.healer,
    # Demon Hunter (12)
    (12, "Havoc"): Role.dps,
    (12, "Vengeance"): Role.tank,
    (12, "Devourer"): Role.dps,  # Midnight-added DH ranged DPS spec
    # Evoker (13)
    (13, "Augmentation"): Role.dps,
    (13, "Devastation"): Role.dps,
    (13, "Preservation"): Role.healer,
}


# Healer specs that have a baseline interrupt ability
HEALER_SPECS_WITH_INTERRUPT: set[tuple[int, str]] = {
    (2, "Holy"),          # Paladin - Rebuke
    (7, "Restoration"),   # Shaman - Wind Shear
    (10, "Mistweaver"),   # Monk - Spear Hand Strike (added 2026-04-27 Batch 2 audit)
}


def get_role(class_id: int, spec_name: str) -> Role:
    """Look up the role for a class/spec combo. Defaults to DPS if unknown."""
    return SPEC_ROLE_MAP.get((class_id, spec_name), Role.dps)


def healer_can_interrupt(class_id: int, spec_name: str) -> bool:
    """Check if a healer spec has a baseline interrupt ability."""
    return (class_id, spec_name) in HEALER_SPECS_WITH_INTERRUPT
