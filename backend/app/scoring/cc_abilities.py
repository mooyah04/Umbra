"""Crowd control ability IDs per class for tracking CC usage in M+.

These are hard CC abilities that players can use on enemy mobs to prevent
casts, reduce damage intake, or control dangerous packs. Good CC usage
is a key differentiator in high M+ keys.

Organized by class_id. Each entry is a list of (debuff_id, ability_name) tuples.
debuff_id is the WCL debuff/aura ID that appears on the enemy target.

WoW class IDs:
  1=Warrior, 2=Paladin, 3=Hunter, 4=Rogue, 5=Priest, 6=DeathKnight,
  7=Shaman, 8=Mage, 9=Warlock, 10=Monk, 11=Druid, 12=DemonHunter,
  13=Evoker
"""

# class_id -> [(debuff_id, ability_name), ...]
CC_ABILITIES: dict[int, list[tuple[int, str]]] = {
    # Warrior (1)
    1: [
        (5246, "Intimidating Shout"),    # AoE fear
        (132169, "Storm Bolt"),          # Single-target stun
        (132168, "Shockwave"),           # Cone stun
    ],

    # Paladin (2)
    2: [
        (853, "Hammer of Justice"),      # Single-target stun
        (20066, "Repentance"),           # Incapacitate (talent)
        (105421, "Blinding Light"),      # AoE disorient
    ],

    # Hunter (3)
    3: [
        (3355, "Freezing Trap"),         # Single-target CC
        (117526, "Binding Shot"),        # AoE root/stun
        (19386, "Wyvern Sting"),         # Sleep (talent)
        (186387, "Bursting Shot"),       # AoE knockback/disorient
    ],

    # Rogue (4)
    4: [
        (6770, "Sap"),                   # Pre-combat CC
        (2094, "Blind"),                 # Disorient
        (1833, "Cheap Shot"),            # Stun (stealth)
        (408, "Kidney Shot"),            # Combo-point stun
        (1776, "Gouge"),                 # Incapacitate
    ],

    # Priest (5)
    5: [
        (605, "Mind Control"),           # Mind control
        (8122, "Psychic Scream"),        # AoE fear
        (200196, "Holy Word: Chastise"), # Stun/incapacitate
        (64044, "Psychic Horror"),       # Stun (talent)
    ],

    # Death Knight (6)
    6: [
        (108194, "Asphyxiate"),          # Single-target stun
        (207167, "Blinding Sleet"),      # AoE disorient
        (91800, "Gnaw"),                 # Ghoul stun
    ],

    # Shaman (7)
    7: [
        (118905, "Static Charge"),       # Capacitor Totem stun
        (51514, "Hex"),                  # Hex (CC)
        (197214, "Sundering"),           # Incapacitate (Enhancement talent)
    ],

    # Mage (8)
    8: [
        (118, "Polymorph"),              # Single-target CC
        (157981, "Blast Wave"),          # AoE slow/knockback
        (31661, "Dragon's Breath"),      # Cone disorient
        (122, "Frost Nova"),             # AoE root
        (82691, "Ring of Frost"),        # AoE incapacitate
    ],

    # Warlock (9)
    9: [
        (710, "Banish"),                 # Banish (demon/aberration)
        (6789, "Mortal Coil"),           # Horror
        (5484, "Howl of Terror"),        # AoE fear
        (30283, "Shadowfury"),           # AoE stun
    ],

    # Monk (10)
    10: [
        (115078, "Paralysis"),           # Single-target incapacitate
        (119381, "Leg Sweep"),           # AoE stun
        (116844, "Ring of Peace"),       # AoE knockback zone
    ],

    # Druid (11)
    11: [
        (2637, "Hibernate"),             # Sleep (beast/dragonkin)
        (99, "Incapacitating Roar"),     # AoE incapacitate
        (5211, "Mighty Bash"),           # Single-target stun
        (102359, "Mass Entanglement"),   # AoE root
        (339, "Entangling Roots"),       # Single-target root
    ],

    # Demon Hunter (12)
    12: [
        (217832, "Imprison"),            # Single-target CC
        (179057, "Chaos Nova"),          # AoE stun
        (211881, "Fel Eruption"),        # Stun (talent)
        (207684, "Sigil of Misery"),     # AoE fear
    ],

    # Evoker (13)
    13: [
        (360806, "Sleep Walk"),          # Incapacitate (Preservation)
        (357214, "Wing Buffet"),         # Knockback
        (370452, "Shattering Star"),     # AoE CC (Devastation)
        (372048, "Oppressing Roar"),     # AoE dispel + slow
    ],
}


def get_cc_ability_ids(class_id: int) -> set[int]:
    """Get the set of CC ability debuff IDs for a class.

    Returns debuff IDs for fast lookup against the WCL Debuffs table.
    """
    return {ability_id for ability_id, _ in CC_ABILITIES.get(class_id, [])}
