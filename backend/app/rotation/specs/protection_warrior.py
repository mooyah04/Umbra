"""Protection Warrior rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="protection_warrior",
    display_name="Protection Warrior",
    class_id=1,
    spec_name="Protection",
    aliases={},
    rotation_ids=frozenset({
        23922,   # Shield Slam
        6343,    # Thunder Clap
        6572,    # Revenge
        163201,  # Execute
        190456,  # Ignore Pain
        385952,  # Shield Charge
    }),
    cooldown_ids=frozenset({
        107574,  # Avatar
        871,     # Shield Wall
        12975,   # Last Stand
        2565,    # Shield Block
        1160,    # Demoralizing Shout
        228920,  # Ravager
        384318,  # Thunderous Roar
        376079,  # Champion's Spear
    }),
    utility_ids=frozenset({
        6552,    # Pummel (interrupt)
        23920,   # Spell Reflection
        97462,   # Rallying Cry
        100,     # Charge
        3411,    # Intervene
        6544,    # Heroic Leap
        18499,   # Berserker Rage
        107570,  # Storm Bolt
        46968,   # Shockwave
        5246,    # Intimidating Shout
        1715,    # Hamstring
        355,     # Taunt
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
