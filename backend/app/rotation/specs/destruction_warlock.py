"""Destruction Warlock rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="destruction_warlock",
    display_name="Destruction Warlock",
    class_id=9,
    spec_name="Destruction",
    aliases={},
    rotation_ids=frozenset({
        29722,   # Incinerate
        116858,  # Chaos Bolt
        348,     # Immolate
        17962,   # Conflagrate
        5740,    # Rain of Fire
        80240,   # Havoc
        17877,   # Shadowburn
        196447,  # Channel Demonfire
        387976,  # Dimensional Rift
        108683,  # Fire and Brimstone (self-buff)
        689,     # Drain Life
    }),
    cooldown_ids=frozenset({
        1122,    # Summon Infernal
        1122,    # dup
        104773,  # Unending Resolve
        108416,  # Dark Pact
        108359,  # Dark Regeneration
        212295,  # Nether Ward
        267217,  # Nether Portal (Destro variant)
        113858,  # Dark Soul: Instability (legacy)
    }),
    utility_ids=frozenset({
        19647,   # Spell Lock
        89766,   # Axe Toss
        5782,    # Fear
        6789,    # Mortal Coil
        30283,   # Shadowfury
        48020,   # Demonic Circle: Teleport
        48018,   # Demonic Circle: Summon
        20707,   # Soulstone
        29893,   # Create Soulwell
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
