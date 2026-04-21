"""Elemental Shaman rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="elemental_shaman",
    display_name="Elemental Shaman",
    class_id=7,
    spec_name="Elemental",
    aliases={},
    rotation_ids=frozenset({
        188196,  # Lightning Bolt
        188443,  # Chain Lightning
        51505,   # Lava Burst
        8042,    # Earth Shock
        61882,   # Earthquake
        188389,  # Flame Shock
        196840,  # Frost Shock
        210714,  # Icefury
        375982,  # Primordial Wave
        191634,  # Stormkeeper
        117014,  # Elemental Blast
    }),
    cooldown_ids=frozenset({
        198067,  # Fire Elemental
        192249,  # Storm Elemental
        114050,  # Ascendance (Elemental)
        108271,  # Astral Shift
        192058,  # Capacitor Totem
        16191,   # Mana Tide Totem
    }),
    utility_ids=frozenset({
        57994,   # Wind Shear (interrupt)
        51886,   # Cleanse Spirit
        370,     # Purge
        2484,    # Earthbind Totem
        192058,  # Capacitor Totem
        51485,   # Earthgrab Totem
        108271,  # Astral Shift (defensive)
        30884,   # Nature's Guardian
        546,     # Water Walking
        556,     # Astral Recall
        8143,    # Tremor Totem
        192077,  # Wind Rush Totem
    }) - frozenset({108271, 192058}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
