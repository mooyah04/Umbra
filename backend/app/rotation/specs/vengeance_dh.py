"""Vengeance Demon Hunter rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="vengeance_dh",
    display_name="Vengeance Demon Hunter",
    class_id=12,
    spec_name="Vengeance",
    aliases={},
    rotation_ids=frozenset({
        263642,  # Fracture
        228477,  # Soul Cleave
        258920,  # Immolation Aura
        212084,  # Fel Devastation
        204596,  # Sigil of Flame
        247454,  # Spirit Bomb
        185245,  # Torment (Taunt)
        207407,  # Soul Carver
        320341,  # Bulk Extraction
        228478,  # Soul Cleave alt
        178740,  # Immolation Aura initial
    }) - frozenset({228478, 178740, 185245}),
    cooldown_ids=frozenset({
        187827,  # Metamorphosis (Vengeance)
        204021,  # Fiery Brand
        203720,  # Demon Spikes
        196555,  # Netherwalk
        263648,  # Soul Rending (passive proxy — drop if noisy)
        370965,  # The Hunt
        389688,  # Soul Carver (if talented)
    }) - frozenset({263648}),
    utility_ids=frozenset({
        183752,  # Disrupt (interrupt)
        179057,  # Chaos Nova
        207684,  # Sigil of Misery
        202138,  # Sigil of Chains
        217832,  # Imprison
        188501,  # Spectral Sight
        131347,  # Glide
        185245,  # Torment (Taunt)
        198793,  # Infernal Strike
        198589,  # Blur (legacy/talent)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
