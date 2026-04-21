"""Restoration Shaman rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="restoration_shaman",
    display_name="Restoration Shaman",
    class_id=7,
    spec_name="Restoration",
    aliases={},
    rotation_ids=frozenset({
        61295,   # Riptide
        77472,   # Healing Wave
        8004,    # Healing Surge
        1064,    # Chain Heal
        73920,   # Healing Rain
        157153,  # Cloudburst Totem
        197995,  # Wellspring
        444995,  # Surging Totem (Farseer hero)
        188389,  # Flame Shock (damage fillers)
        188196,  # Lightning Bolt
        188443,  # Chain Lightning
    }),
    cooldown_ids=frozenset({
        108280,  # Healing Tide Totem
        114052,  # Ascendance (Resto)
        98008,   # Spirit Link Totem
        198838,  # Earthen Wall Totem
        207399,  # Ancestral Protection Totem
        16191,   # Mana Tide Totem
        108271,  # Astral Shift
    }),
    utility_ids=frozenset({
        57994,   # Wind Shear (interrupt)
        51886,   # Cleanse Spirit
        77130,   # Purify Spirit
        370,     # Purge
        192058,  # Capacitor Totem
        2484,    # Earthbind Totem
        51485,   # Earthgrab Totem
        8143,    # Tremor Totem
        192077,  # Wind Rush Totem
        546,     # Water Walking
        556,     # Astral Recall
        30884,   # Nature's Guardian
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
