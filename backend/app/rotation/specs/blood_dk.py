"""Blood Death Knight rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="blood_dk",
    display_name="Blood Death Knight",
    class_id=6,
    spec_name="Blood",
    aliases={},
    rotation_ids=frozenset({
        49998,   # Death Strike
        206930,  # Heart Strike
        195182,  # Marrowrend
        50842,   # Blood Boil
        43265,   # Death and Decay
        194844,  # Bonestorm
        219809,  # Tombstone
        274156,  # Consumption
        49143,   # Frost Strike (off-spec; remove)
    }) - frozenset({49143}),
    cooldown_ids=frozenset({
        55233,   # Vampiric Blood
        49028,   # Dancing Rune Weapon
        194679,  # Rune Tap
        48707,   # Anti-Magic Shell
        48792,   # Icebound Fortitude
        51052,   # Anti-Magic Zone
        383269,  # Abomination Limb (if talented)
        47568,   # Empower Rune Weapon (shared DK CD)
    }),
    utility_ids=frozenset({
        47528,   # Mind Freeze (interrupt)
        43265,   # Death and Decay (already in rotation)
        49576,   # Death Grip
        108199,  # Gorefiend's Grasp
        56222,   # Dark Command (Taunt)
        61999,   # Raise Ally
        50977,   # Death Gate
        212552,  # Wraith Walk
        327574,  # Sacrificial Pact
    }) - frozenset({43265}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
