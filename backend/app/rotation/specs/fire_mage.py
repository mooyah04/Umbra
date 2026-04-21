"""Fire Mage rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="fire_mage",
    display_name="Fire Mage",
    class_id=8,
    spec_name="Fire",
    aliases={},
    rotation_ids=frozenset({
        133,     # Fireball
        11366,   # Pyroblast
        108853,  # Fire Blast
        2948,    # Scorch
        44457,   # Living Bomb
        2120,    # Flamestrike
        257541,  # Phoenix Flames
        153561,  # Meteor
        31661,   # Dragon's Breath
        383886,  # Sun King's Blessing
        235313,  # Blazing Barrier
        257537,  # Phoenix Reborn
        382890,  # Hyperthermia (proc activator)
    }),
    cooldown_ids=frozenset({
        190319,  # Combustion
        153561,  # Meteor
        45438,   # Ice Block
        110960,  # Greater Invisibility
        55342,   # Mirror Image
        235313,  # Blazing Barrier
    }),
    utility_ids=frozenset({
        2139,    # Counterspell (interrupt)
        66,      # Invisibility
        475,     # Remove Curse
        1953,    # Blink
        212653,  # Shimmer
        108978,  # Alter Time
        122,     # Frost Nova
        118,     # Polymorph
        113724,  # Ring of Frost
        130,     # Slow Fall
        80353,   # Time Warp
        31661,   # Dragon's Breath (disorient, but also rotation)
    }) - frozenset({31661}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
