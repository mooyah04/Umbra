"""Mistweaver Monk rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="mistweaver_monk",
    display_name="Mistweaver Monk",
    class_id=10,
    spec_name="Mistweaver",
    aliases={},
    rotation_ids=frozenset({
        115175,  # Soothing Mist
        124682,  # Enveloping Mist
        116670,  # Vivify
        115151,  # Renewing Mist
        107428,  # Rising Sun Kick
        191837,  # Essence Font
        100780,  # Tiger Palm
        100784,  # Blackout Kick
        322101,  # Expel Harm
        101546,  # Spinning Crane Kick
        117952,  # Crackling Jade Lightning
        388615,  # Faeline Stomp / Jadefire Stomp
        388193,  # Chi Burst
    }),
    cooldown_ids=frozenset({
        115310,  # Revival
        322118,  # Invoke Yu'lon
        325197,  # Invoke Chi-Ji
        116849,  # Life Cocoon
        116680,  # Thunder Focus Tea
        115203,  # Fortifying Brew
        122783,  # Diffuse Magic
        115176,  # Zen Meditation
    }),
    utility_ids=frozenset({
        116705,  # Spear Hand Strike (interrupt, if talented)
        119381,  # Leg Sweep
        115078,  # Paralysis
        115450,  # Detox (magic + poison)
        119996,  # Transcendence: Transfer
        101643,  # Transcendence
        109132,  # Roll
        115008,  # Chi Torpedo
        116841,  # Tiger's Lust
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
