"""Windwalker Monk rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="windwalker_monk",
    display_name="Windwalker Monk",
    class_id=10,
    spec_name="Windwalker",
    aliases={},
    rotation_ids=frozenset({
        100780,  # Tiger Palm
        100784,  # Blackout Kick
        107428,  # Rising Sun Kick
        113656,  # Fists of Fury
        101546,  # Spinning Crane Kick
        152175,  # Whirling Dragon Punch
        392983,  # Strike of the Windlord
        322109,  # Touch of Death
        117952,  # Crackling Jade Lightning
        388193,  # Chi Burst
        388615,  # Faeline Stomp / Jadefire Stomp
        322101,  # Expel Harm
    }),
    cooldown_ids=frozenset({
        137639,  # Storm, Earth, and Fire
        123904,  # Invoke Xuen
        152173,  # Serenity
        122470,  # Touch of Karma
        122783,  # Diffuse Magic
        115203,  # Fortifying Brew
        115176,  # Zen Meditation
    }),
    utility_ids=frozenset({
        116705,  # Spear Hand Strike (interrupt)
        119381,  # Leg Sweep
        115078,  # Paralysis
        119996,  # Transcendence: Transfer
        101643,  # Transcendence
        109132,  # Roll
        115008,  # Chi Torpedo
        116841,  # Tiger's Lust
        115546,  # Provoke
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
