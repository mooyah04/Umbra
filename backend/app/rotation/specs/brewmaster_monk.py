"""Brewmaster Monk rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="brewmaster_monk",
    display_name="Brewmaster Monk",
    class_id=10,
    spec_name="Brewmaster",
    aliases={},
    rotation_ids=frozenset({
        121253,  # Keg Smash
        115181,  # Breath of Fire
        100780,  # Tiger Palm
        100784,  # Blackout Kick
        107428,  # Rising Sun Kick
        205523,  # Blackout Strike (if present)
        115308,  # Elusive Brawler (passive)
        322507,  # Celestial Brew
        119582,  # Purifying Brew
        322101,  # Exploding Keg
        325153,  # Exploding Keg (dup)
        109132,  # Roll
    }) - frozenset({325153, 109132, 115308}),
    cooldown_ids=frozenset({
        322507,  # Celestial Brew
        115203,  # Fortifying Brew
        115399,  # Black Ox Brew
        132578,  # Invoke Niuzao
        325153,  # Exploding Keg
        122470,  # Touch of Karma
        122783,  # Diffuse Magic
        115176,  # Zen Meditation
    }) - frozenset({322507}),
    utility_ids=frozenset({
        116705,  # Spear Hand Strike (interrupt)
        119381,  # Leg Sweep
        115078,  # Paralysis
        119996,  # Transcendence: Transfer
        101643,  # Transcendence
        109132,  # Roll
        115008,  # Chi Torpedo
        116841,  # Tiger's Lust
        322109,  # Touch of Death (damage but utility scaled)
        115546,  # Provoke (Taunt)
        117952,  # Crackling Jade Lightning
        213664,  # Nimble Brew (legacy)
        198898,  # Song of Chi-Ji (knockdown, rare)
    }) - frozenset({322109}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
