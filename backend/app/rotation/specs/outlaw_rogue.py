"""Outlaw Rogue rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="outlaw_rogue",
    display_name="Outlaw Rogue",
    class_id=4,
    spec_name="Outlaw",
    aliases={},
    rotation_ids=frozenset({
        193315,  # Sinister Strike
        185763,  # Pistol Shot
        2098,    # Dispatch
        315341,  # Between the Eyes
        13877,   # Blade Flurry
        315508,  # Roll the Bones
        51690,   # Killing Spree
        196937,  # Ghostly Strike
        137619,  # Marked for Death
        193531,  # Slice and Dice (self-buff, used like a rotation button)
        381989,  # Keep it Rolling
    }),
    cooldown_ids=frozenset({
        13750,   # Adrenaline Rush
        381989,  # Keep it Rolling
        1856,    # Vanish
        5277,    # Evasion
        31224,   # Cloak of Shadows
        199804,  # Between the Eyes (CD window use)
    }),
    utility_ids=frozenset({
        1766,    # Kick (interrupt)
        2094,    # Blind
        408,     # Kidney Shot
        1776,    # Gouge
        36554,   # Shadowstep (if talented)
        1784,    # Stealth
        114018,  # Shroud of Concealment
        57934,   # Tricks of the Trade
        1725,    # Distract
        195457,  # Grappling Hook
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
