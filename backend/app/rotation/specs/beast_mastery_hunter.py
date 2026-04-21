"""Beast Mastery Hunter rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="beast_mastery_hunter",
    display_name="Beast Mastery Hunter",
    class_id=3,
    spec_name="Beast Mastery",
    aliases={},
    rotation_ids=frozenset({
        34026,   # Kill Command
        193455,  # Cobra Shot
        217200,  # Barbed Shot
        53351,   # Kill Shot
        321530,  # Bloodshed
        2643,    # Multi-Shot
        131894,  # A Murder of Crows
        120679,  # Dire Beast
        459735,  # Sentinel (Hero)
    }),
    cooldown_ids=frozenset({
        19574,   # Bestial Wrath
        193530,  # Aspect of the Wild
        359844,  # Call of the Wild
        201430,  # Stampede
        260402,  # Double Tap (if talented)
        186257,  # Aspect of the Cheetah
        186265,  # Aspect of the Turtle
    }),
    utility_ids=frozenset({
        147362,  # Counter Shot (interrupt)
        187707,  # Muzzle (melee interrupt variant)
        781,     # Disengage
        19801,   # Tranquilizing Shot
        5384,    # Feign Death
        109248,  # Binding Shot
        19577,   # Intimidation
        187650,  # Freezing Trap
        187698,  # Tar Trap
        162488,  # Steel Trap
        34477,   # Misdirection
        264735,  # Survival of the Fittest
        53476,   # Master's Call (pet)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
