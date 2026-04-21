"""Frost Mage rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="frost_mage",
    display_name="Frost Mage",
    class_id=8,
    spec_name="Frost",
    aliases={},
    rotation_ids=frozenset({
        116,     # Frostbolt
        30455,   # Ice Lance
        44614,   # Flurry
        84714,   # Frozen Orb
        199786,  # Glacial Spike
        190356,  # Blizzard
        153595,  # Comet Storm
        205021,  # Ray of Frost
        120,     # Cone of Cold
        31687,   # Summon Water Elemental
        257537,  # Ebonbolt (if present)
    }),
    cooldown_ids=frozenset({
        12472,   # Icy Veins
        235219,  # Cold Snap
        45438,   # Ice Block
        11426,   # Ice Barrier
        110960,  # Greater Invisibility
        55342,   # Mirror Image
        84714,   # Frozen Orb
        198144,  # Ice Form (talent)
    }) - frozenset({84714}),
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
        33395,   # Freeze (pet)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
