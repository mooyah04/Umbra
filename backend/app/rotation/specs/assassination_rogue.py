"""Assassination Rogue rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="assassination_rogue",
    display_name="Assassination Rogue",
    class_id=4,
    spec_name="Assassination",
    aliases={},
    rotation_ids=frozenset({
        1329,    # Mutilate
        32645,   # Envenom
        1943,    # Rupture
        703,     # Garrote
        51723,   # Fan of Knives
        185565,  # Poisoned Knife
        79140,   # Vendetta (legacy)
        360194,  # Deathmark
        121411,  # Crimson Tempest
        200806,  # Exsanguinate
        381623,  # Kingsbane
    }),
    cooldown_ids=frozenset({
        360194,  # Deathmark
        381623,  # Kingsbane
        13750,   # Adrenaline Rush (off-spec, unlikely but listed)
        1856,    # Vanish
        5277,    # Evasion
        31224,   # Cloak of Shadows
        381802,  # Indiscriminate Carnage (Hero talent proxy)
        385627,  # Kingsbane (alt)
    }),
    utility_ids=frozenset({
        1766,    # Kick (interrupt)
        2094,    # Blind
        408,     # Kidney Shot
        1776,    # Gouge
        36554,   # Shadowstep
        2823,    # Deadly Poison (apply)
        315584,  # Instant Poison (apply)
        3408,    # Crippling Poison (apply)
        5761,    # Numbing Poison (apply)
        8679,    # Wound Poison (apply)
        1784,    # Stealth
        114018,  # Shroud of Concealment
        57934,   # Tricks of the Trade
        185313,  # Shadow Dance (if talented)
        31230,   # Cheat Death (passive; shown if WCL logs it)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
