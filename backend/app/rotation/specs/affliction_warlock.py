"""Affliction Warlock rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="affliction_warlock",
    display_name="Affliction Warlock",
    class_id=9,
    spec_name="Affliction",
    aliases={},
    rotation_ids=frozenset({
        686,     # Shadow Bolt
        172,     # Corruption
        316099,  # Unstable Affliction
        980,     # Agony
        63106,   # Siphon Life
        324536,  # Malefic Rapture
        27243,   # Seed of Corruption
        198590,  # Drain Soul
        278350,  # Vile Taint
        48181,   # Haunt
        386997,  # Soul Rot
        603,     # Doom
    }),
    cooldown_ids=frozenset({
        205180,  # Summon Darkglare
        205179,  # Phantom Singularity
        104773,  # Unending Resolve
        108416,  # Dark Pact
        108359,  # Dark Regeneration
        212295,  # Nether Ward
    }),
    utility_ids=frozenset({
        19647,   # Spell Lock (Felhunter interrupt)
        132409,  # Spell Lock (pet cast via command)
        89766,   # Axe Toss (Felguard stun)
        5782,    # Fear
        6789,    # Mortal Coil
        30283,   # Shadowfury
        48020,   # Demonic Circle: Teleport
        48018,   # Demonic Circle: Summon
        104773,  # Unending Resolve (already CD)
        20707,   # Soulstone
        29893,   # Create Soulwell
        755,     # Health Funnel
        20707,   # Soulstone (dup)
    }) - frozenset({104773}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
