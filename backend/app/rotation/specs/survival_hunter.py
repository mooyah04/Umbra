"""Survival Hunter rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="survival_hunter",
    display_name="Survival Hunter",
    class_id=3,
    spec_name="Survival",
    aliases={},
    rotation_ids=frozenset({
        186270,  # Raptor Strike
        259387,  # Mongoose Bite
        259489,  # Kill Command (SV variant)
        259495,  # Wildfire Bomb
        187708,  # Carve
        212436,  # Butchery
        320976,  # Kill Shot
        270335,  # Flanking Strike
        360952,  # Coordinated Kill
    }),
    cooldown_ids=frozenset({
        266779,  # Coordinated Assault
        186289,  # Aspect of the Eagle
        186257,  # Aspect of the Cheetah
        186265,  # Aspect of the Turtle
    }),
    utility_ids=frozenset({
        187707,  # Muzzle (melee interrupt)
        781,     # Disengage
        19801,   # Tranquilizing Shot
        5384,    # Feign Death
        109248,  # Binding Shot
        187650,  # Freezing Trap
        187698,  # Tar Trap
        162488,  # Steel Trap
        34477,   # Misdirection
        264735,  # Survival of the Fittest
        259391,  # Chakrams (if talented)
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
