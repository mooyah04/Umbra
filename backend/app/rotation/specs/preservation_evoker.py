"""Preservation Evoker rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="preservation_evoker",
    display_name="Preservation Evoker",
    class_id=13,
    spec_name="Preservation",
    aliases={},
    rotation_ids=frozenset({
        361469,  # Living Flame
        366155,  # Reversion
        364343,  # Echo
        355936,  # Dream Breath
        367226,  # Spiritbloom
        355913,  # Emerald Blossom
        360995,  # Verdant Embrace
        373861,  # Temporal Anomaly
        362969,  # Azure Strike (filler DPS)
        357211,  # Pyre (rare DPS)
    }),
    cooldown_ids=frozenset({
        363534,  # Rewind
        359816,  # Dream Flight
        370960,  # Emerald Communion
        370553,  # Tip the Scales
        363916,  # Obsidian Scales
        374348,  # Renewing Blaze
        357170,  # Time Stop
        370665,  # Rescue (utility but shown as CD)
    }) - frozenset({370665}),
    utility_ids=frozenset({
        351338,  # Quell (interrupt)
        368432,  # Unravel
        374251,  # Cauterizing Flame
        370665,  # Rescue
        357214,  # Wing Buffet
        368970,  # Tail Swipe
        374968,  # Time Spiral
        360806,  # Sleep Walk
        365585,  # Expunge
        358267,  # Hover
        404977,  # Time Skip
    }) - frozenset({404977}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
