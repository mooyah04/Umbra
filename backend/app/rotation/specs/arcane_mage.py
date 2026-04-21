"""Arcane Mage rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="arcane_mage",
    display_name="Arcane Mage",
    class_id=8,
    spec_name="Arcane",
    aliases={},
    rotation_ids=frozenset({
        30451,   # Arcane Blast
        44425,   # Arcane Barrage
        5143,    # Arcane Missiles
        153626,  # Arcane Orb
        1449,    # Arcane Explosion
        12051,   # Evocation
        321507,  # Touch of the Magi
        365350,  # Arcane Surge
        376103,  # Radiant Spark
        384631,  # Flurry (Spellslinger)
    }),
    cooldown_ids=frozenset({
        12042,   # Arcane Power (legacy, if present)
        365350,  # Arcane Surge
        235313,  # Blazing Barrier (defensive)
        11426,   # Ice Barrier (defensive)
        235450,  # Prismatic Barrier
        45438,   # Ice Block
        110960,  # Greater Invisibility
        55342,   # Mirror Image
    }),
    utility_ids=frozenset({
        2139,    # Counterspell (interrupt)
        66,      # Invisibility
        475,     # Remove Curse
        1953,    # Blink
        212653,  # Shimmer
        108978,  # Alter Time
        122,     # Frost Nova
        31589,   # Slow
        118,     # Polymorph
        113724,  # Ring of Frost
        130,     # Slow Fall
        80353,   # Time Warp
        324220,  # Mass Barrier (if talented)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
