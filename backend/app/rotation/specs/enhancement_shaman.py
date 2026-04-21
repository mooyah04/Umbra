"""Enhancement Shaman rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="enhancement_shaman",
    display_name="Enhancement Shaman",
    class_id=7,
    spec_name="Enhancement",
    aliases={},
    rotation_ids=frozenset({
        17364,   # Stormstrike
        115356,  # Windstrike
        60103,   # Lava Lash
        187874,  # Crash Lightning
        196840,  # Frost Shock
        188389,  # Flame Shock
        197214,  # Sundering
        342240,  # Ice Strike
        117014,  # Elemental Blast
        375982,  # Primordial Wave
        333974,  # Fire Nova
        188196,  # Lightning Bolt
        188443,  # Chain Lightning
    }),
    cooldown_ids=frozenset({
        51533,   # Feral Spirit
        114051,  # Ascendance (Enhancement)
        108271,  # Astral Shift
        192058,  # Capacitor Totem
        198067,  # Fire Elemental
    }),
    utility_ids=frozenset({
        57994,   # Wind Shear (interrupt)
        51886,   # Cleanse Spirit
        370,     # Purge
        2484,    # Earthbind Totem
        51485,   # Earthgrab Totem
        546,     # Water Walking
        8143,    # Tremor Totem
        192077,  # Wind Rush Totem
        58875,   # Spirit Walk
        20608,   # Reincarnation (passive)
        30884,   # Nature's Guardian
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
