"""Demonology Warlock rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="demonology_warlock",
    display_name="Demonology Warlock",
    class_id=9,
    spec_name="Demonology",
    aliases={},
    rotation_ids=frozenset({
        686,     # Shadow Bolt
        264178,  # Demonbolt
        105174,  # Hand of Gul'dan
        104316,  # Call Dreadstalkers
        264119,  # Summon Vilefiend
        267171,  # Demonic Strength
        267211,  # Bilescourge Bombers
        196277,  # Implosion
        264130,  # Power Siphon
        603,     # Doom
        30283,   # Shadowfury (damage + rotational in M+)
    }) - frozenset({30283}),
    cooldown_ids=frozenset({
        265187,  # Summon Demonic Tyrant
        111898,  # Grimoire: Felguard
        104773,  # Unending Resolve
        108416,  # Dark Pact
        108359,  # Dark Regeneration
        212295,  # Nether Ward
        387159,  # Nether Portal
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
        212459,  # Call Fel Lord (taunt)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
