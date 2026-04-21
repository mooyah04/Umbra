"""Unholy Death Knight rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="unholy_dk",
    display_name="Unholy Death Knight",
    class_id=6,
    spec_name="Unholy",
    aliases={},
    rotation_ids=frozenset({
        55090,   # Scourge Strike
        207311,  # Clawing Shadows (talent)
        85948,   # Festering Strike
        47541,   # Death Coil
        207317,  # Epidemic
        43265,   # Death and Decay
        343294,  # Soul Reaper
        115989,  # Unholy Blight (if talented)
        390279,  # Vile Contagion
    }),
    cooldown_ids=frozenset({
        42650,   # Army of the Dead
        275699,  # Apocalypse
        63560,   # Dark Transformation
        49206,   # Summon Gargoyle
        47568,   # Empower Rune Weapon
        48792,   # Icebound Fortitude
        48707,   # Anti-Magic Shell
        51052,   # Anti-Magic Zone
        46584,   # Raise Dead
    }),
    utility_ids=frozenset({
        47528,   # Mind Freeze (interrupt)
        49576,   # Death Grip
        56222,   # Dark Command
        61999,   # Raise Ally
        50977,   # Death Gate
        212552,  # Wraith Walk
        327574,  # Sacrificial Pact
        48265,   # Death's Advance
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
