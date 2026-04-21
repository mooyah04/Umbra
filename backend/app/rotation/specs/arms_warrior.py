"""Arms Warrior rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="arms_warrior",
    display_name="Arms Warrior",
    class_id=1,
    spec_name="Arms",
    aliases={
        # Execute — Sudden Death proc variant maps to the canonical
        # Arms Execute ID so frequency reads as "one button" rather
        # than two split rows.
        260798: 163201,
    },
    rotation_ids=frozenset({
        12294,   # Mortal Strike
        7384,    # Overpower
        163201,  # Execute (Arms)
        1464,    # Slam
        1680,    # Whirlwind
        227847,  # Bladestorm
        772,     # Rend
        845,     # Cleave
        6343,    # Thunder Clap
        260643,  # Skullsplitter
        260708,  # Sweeping Strikes
    }),
    cooldown_ids=frozenset({
        107574,  # Avatar
        167105,  # Colossus Smash
        262161,  # Warbreaker
        384318,  # Thunderous Roar
        376079,  # Champion's Spear
    }),
    utility_ids=frozenset({
        6552,    # Pummel (interrupt)
        23920,   # Spell Reflection
        97462,   # Rallying Cry
        118038,  # Die by the Sword
        1715,    # Hamstring
        100,     # Charge
        3411,    # Intervene
        6544,    # Heroic Leap
        18499,   # Berserker Rage
        107570,  # Storm Bolt
        64382,   # Shattering Throw
        46968,   # Shockwave
        5246,    # Intimidating Shout
        190456,  # Ignore Pain
        355,     # Taunt
    }),
    ignore_ids=frozenset({
        384110,  # Wrecking Throw — niche cleave talent, not rotational
    }),
    last_reviewed="2026-04-21",
)
