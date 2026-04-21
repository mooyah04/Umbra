"""Subtlety Rogue rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="subtlety_rogue",
    display_name="Subtlety Rogue",
    class_id=4,
    spec_name="Subtlety",
    aliases={},
    rotation_ids=frozenset({
        185438,  # Shadowstrike
        53,      # Backstab
        196819,  # Eviscerate
        1943,    # Rupture
        212283,  # Symbols of Death
        319175,  # Black Powder
        197835,  # Shuriken Storm
        114014,  # Shuriken Toss
        280719,  # Secret Technique
        328547,  # Serrated Bone Spike
    }),
    cooldown_ids=frozenset({
        185313,  # Shadow Dance
        121471,  # Shadow Blades
        1856,    # Vanish
        5277,    # Evasion
        31224,   # Cloak of Shadows
        385616,  # Echoing Reprimand (if shared; Sub has variants)
        277925,  # Shuriken Tornado
    }),
    utility_ids=frozenset({
        1766,    # Kick (interrupt)
        2094,    # Blind
        408,     # Kidney Shot
        1776,    # Gouge
        36554,   # Shadowstep
        1784,    # Stealth
        114018,  # Shroud of Concealment
        57934,   # Tricks of the Trade
        2823,    # Deadly/Instant Poison (apply)
        3408,    # Crippling Poison (apply)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
