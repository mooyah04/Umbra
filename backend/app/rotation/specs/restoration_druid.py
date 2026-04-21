"""Restoration Druid rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="restoration_druid",
    display_name="Restoration Druid",
    class_id=11,
    spec_name="Restoration",
    aliases={},
    rotation_ids=frozenset({
        8936,    # Regrowth
        774,     # Rejuvenation
        48438,   # Wild Growth
        18562,   # Swiftmend
        33763,   # Lifebloom
        102351,  # Cenarion Ward
        145205,  # Efflorescence
        5185,    # Healing Touch
        189853,  # Dreamwalker (passive proxy)
        197721,  # Flourish
        8921,    # Moonfire (filler DPS)
        93402,   # Sunfire (filler DPS)
        190984,  # Wrath (filler DPS)
        78674,   # Starsurge (rare)
    }) - frozenset({189853}),
    cooldown_ids=frozenset({
        740,     # Tranquility
        33891,   # Incarnation: Tree of Life
        391528,  # Convoke the Spirits
        102342,  # Ironbark
        29166,   # Innervate
        22812,   # Barkskin
        61336,   # Survival Instincts (bear form)
        203651,  # Overgrowth
    }),
    utility_ids=frozenset({
        106839,  # Skull Bash (interrupt if talented)
        88423,   # Nature's Cure
        2782,    # Remove Corruption
        33786,   # Cyclone
        339,     # Entangling Roots
        1850,    # Dash
        252216,  # Tiger Dash
        783,     # Travel Form
        5215,    # Prowl
        6795,    # Growl (bear, rare)
        77761,   # Stampeding Roar
        132158,  # Nature's Swiftness
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
