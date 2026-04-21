"""Feral Druid rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="feral_druid",
    display_name="Feral Druid",
    class_id=11,
    spec_name="Feral",
    aliases={},
    rotation_ids=frozenset({
        5221,    # Shred
        1822,    # Rake
        1079,    # Rip
        22568,   # Ferocious Bite
        106830,  # Thrash (Cat)
        106785,  # Swipe (Cat)
        202028,  # Brutal Slash
        155625,  # Moonfire (Cat)
        285381,  # Primal Wrath
        274837,  # Feral Frenzy
        106951,  # Berserk (self-buff, rotational in its use)
        5217,    # Tiger's Fury
        62606,   # Savage Roar (if present)
        213764,  # Swipe (alt)
    }),
    cooldown_ids=frozenset({
        102543,  # Incarnation: Avatar of Ashamane
        106951,  # Berserk
        5217,    # Tiger's Fury
        61336,   # Survival Instincts
        22812,   # Barkskin
        319454,  # Heart of the Wild
        391528,  # Convoke the Spirits
        22842,   # Frenzied Regeneration
    }) - frozenset({106951, 5217}),
    utility_ids=frozenset({
        106839,  # Skull Bash (interrupt)
        93402,   # Sunfire (off-spec minor)
        33786,   # Cyclone
        339,     # Entangling Roots
        1850,    # Dash
        252216,  # Tiger Dash
        783,     # Travel Form
        5215,    # Prowl
        22570,   # Maim
        29166,   # Innervate
        2782,    # Remove Corruption
        6795,    # Growl (Taunt)
        50259,   # Dash (if variant)
    }) - frozenset({93402}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
