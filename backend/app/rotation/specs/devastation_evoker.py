"""Devastation Evoker rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="devastation_evoker",
    display_name="Devastation Evoker",
    class_id=13,
    spec_name="Devastation",
    aliases={},
    rotation_ids=frozenset({
        361469,  # Living Flame
        362969,  # Azure Strike
        356995,  # Disintegrate
        357211,  # Pyre
        357208,  # Fire Breath
        359073,  # Eternity Surge
        370452,  # Shattering Star
        357210,  # Deep Breath
        353759,  # Landslide (utility overlap)
        368847,  # Firestorm (if talented)
    }) - frozenset({353759}),
    cooldown_ids=frozenset({
        375087,  # Dragonrage
        370553,  # Tip the Scales
        357210,  # Deep Breath
        363916,  # Obsidian Scales (defensive)
        374348,  # Renewing Blaze
        360806,  # Sleep Walk (rare)
    }) - frozenset({357210}),
    utility_ids=frozenset({
        351338,  # Quell (interrupt)
        357170,  # Time Stop
        355913,  # Emerald Blossom
        358385,  # Landslide
        360806,  # Sleep Walk
        368970,  # Tail Swipe
        357214,  # Wing Buffet
        368432,  # Unravel (dispel magic-immune shields)
        374251,  # Cauterizing Flame
        370665,  # Rescue
        374968,  # Time Spiral
        370960,  # Emerald Communion
        360995,  # Verdant Embrace
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
