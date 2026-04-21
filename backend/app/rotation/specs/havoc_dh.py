"""Havoc Demon Hunter rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="havoc_dh",
    display_name="Havoc Demon Hunter",
    class_id=12,
    spec_name="Havoc",
    aliases={},
    rotation_ids=frozenset({
        162794,  # Chaos Strike
        162243,  # Demon's Bite
        188499,  # Blade Dance
        198013,  # Eye Beam
        195072,  # Fel Rush
        342817,  # Glaive Tempest
        258920,  # Immolation Aura
        258860,  # Essence Break
        204596,  # Sigil of Flame
        185123,  # Throw Glaive
        232893,  # Felblade
        210152,  # Death Sweep (Meta variant)
        199552,  # Annihilation (Meta variant)
    }),
    cooldown_ids=frozenset({
        191427,  # Metamorphosis
        198793,  # Vengeful Retreat
        196718,  # Darkness
        198589,  # Blur
        263648,  # Soul Rending
        370965,  # The Hunt
        258925,  # Fel Barrage (if talented)
    }),
    utility_ids=frozenset({
        183752,  # Disrupt (interrupt)
        179057,  # Chaos Nova
        207684,  # Sigil of Misery
        202138,  # Sigil of Chains
        217832,  # Imprison
        188501,  # Spectral Sight
        195072,  # Fel Rush (also rotation)
        131347,  # Glide
        188501,  # Spectral Sight (dup)
    }) - frozenset({195072}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
