"""Augmentation Evoker rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="augmentation_evoker",
    display_name="Augmentation Evoker",
    class_id=13,
    spec_name="Augmentation",
    aliases={},
    rotation_ids=frozenset({
        395160,  # Eruption
        361469,  # Living Flame
        357208,  # Fire Breath
        396286,  # Upheaval
        362969,  # Azure Strike
        357211,  # Pyre
        409311,  # Prescience
        360827,  # Blistering Scales
    }),
    cooldown_ids=frozenset({
        403631,  # Breath of Eons
        395152,  # Ebon Might
        404977,  # Time Skip
        370553,  # Tip the Scales
        363916,  # Obsidian Scales
        374348,  # Renewing Blaze
    }),
    utility_ids=frozenset({
        351338,  # Quell (interrupt)
        368432,  # Unravel
        374251,  # Cauterizing Flame
        370665,  # Rescue
        357214,  # Wing Buffet
        368970,  # Tail Swipe
        374968,  # Time Spiral
        360806,  # Sleep Walk
        357170,  # Time Stop
        358267,  # Hover
        355913,  # Emerald Blossom
        360995,  # Verdant Embrace
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
