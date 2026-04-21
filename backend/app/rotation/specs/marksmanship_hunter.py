"""Marksmanship Hunter rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="marksmanship_hunter",
    display_name="Marksmanship Hunter",
    class_id=3,
    spec_name="Marksmanship",
    aliases={},
    rotation_ids=frozenset({
        19434,   # Aimed Shot
        185358,  # Arcane Shot
        257044,  # Rapid Fire
        56641,   # Steady Shot
        257620,  # Multi-Shot
        53351,   # Kill Shot
        212431,  # Explosive Shot
        260243,  # Volley
        378771,  # Salvo
        459735,  # Sentinel
    }),
    cooldown_ids=frozenset({
        288613,  # Trueshot
        186387,  # Bursting Shot (off-CD damage + knockback)
        260402,  # Double Tap
        186257,  # Aspect of the Cheetah
        186265,  # Aspect of the Turtle
    }),
    utility_ids=frozenset({
        147362,  # Counter Shot (interrupt)
        781,     # Disengage
        19801,   # Tranquilizing Shot
        5384,    # Feign Death
        109248,  # Binding Shot
        187650,  # Freezing Trap
        187698,  # Tar Trap
        162488,  # Steel Trap
        34477,   # Misdirection
        264735,  # Survival of the Fittest
        308491,  # Survival of the Fittest (talent)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
