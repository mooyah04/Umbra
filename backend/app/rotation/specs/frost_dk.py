"""Frost Death Knight rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="frost_dk",
    display_name="Frost Death Knight",
    class_id=6,
    spec_name="Frost",
    aliases={},
    rotation_ids=frozenset({
        49020,   # Obliterate
        49143,   # Frost Strike
        49184,   # Howling Blast
        196770,  # Remorseless Winter
        207230,  # Frostscythe
        194913,  # Glacial Advance
        305392,  # Chill Streak
        152279,  # Breath of Sindragosa
        316239,  # Soul Reaper (Frost variant)
    }),
    cooldown_ids=frozenset({
        51271,   # Pillar of Frost
        47568,   # Empower Rune Weapon
        152279,  # Breath of Sindragosa
        48792,   # Icebound Fortitude
        48707,   # Anti-Magic Shell
        51052,   # Anti-Magic Zone
    }),
    utility_ids=frozenset({
        47528,   # Mind Freeze (interrupt)
        49576,   # Death Grip
        56222,   # Dark Command (Taunt, if in build)
        61999,   # Raise Ally
        50977,   # Death Gate
        212552,  # Wraith Walk
        327574,  # Sacrificial Pact
        48265,   # Death's Advance
        327574,  # Sacrificial Pact (dup)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
