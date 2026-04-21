"""Balance Druid rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="balance_druid",
    display_name="Balance Druid",
    class_id=11,
    spec_name="Balance",
    aliases={},
    rotation_ids=frozenset({
        190984,  # Wrath
        194153,  # Starfire
        78674,   # Starsurge
        93402,   # Sunfire
        8921,    # Moonfire
        191034,  # Starfall
        202770,  # Fury of Elune
        205636,  # Force of Nature
        88747,   # Wild Mushroom
        191037,  # Starlord (buff)
        197626,  # Starsurge (DF variant) — may dup
    }) - frozenset({197626, 191037}),
    cooldown_ids=frozenset({
        194223,  # Celestial Alignment
        102560,  # Incarnation: Chosen of Elune
        78675,   # Solar Beam
        61336,   # Survival Instincts
        22812,   # Barkskin
        29166,   # Innervate
        391528,  # Convoke the Spirits (if talented)
        323764,  # Convoke variant
    }),
    utility_ids=frozenset({
        106839,  # Skull Bash (interrupt Bear/Cat)
        93983,   # Typhoon
        132469,  # Typhoon (alt)
        2782,    # Remove Corruption
        88423,   # Nature's Cure
        33786,   # Cyclone
        339,     # Entangling Roots
        102342,  # Ironbark
        783,     # Travel Form
        1850,    # Dash
        252216,  # Tiger Dash
        29166,   # Innervate (dup)
        5215,    # Prowl
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
