"""Guardian Druid rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="guardian_druid",
    display_name="Guardian Druid",
    class_id=11,
    spec_name="Guardian",
    aliases={},
    rotation_ids=frozenset({
        33917,   # Mangle
        77758,   # Thrash (Bear)
        213771,  # Swipe (Bear)
        6807,    # Maul
        192081,  # Ironfur
        8921,    # Moonfire
        80313,   # Pulverize
        155835,  # Bristling Fur
        22842,   # Frenzied Regeneration
    }),
    cooldown_ids=frozenset({
        61336,   # Survival Instincts
        22812,   # Barkskin
        50334,   # Berserk (Bear)
        102558,  # Incarnation: Guardian of Ursoc
        204066,  # Lunar Beam
        391528,  # Convoke the Spirits (if talented)
        29166,   # Innervate (can be used defensively)
    }),
    utility_ids=frozenset({
        106839,  # Skull Bash (interrupt)
        6795,    # Growl (Taunt)
        99,      # Incapacitating Roar
        77761,   # Stampeding Roar
        2782,    # Remove Corruption
        88423,   # Nature's Cure (off-spec)
        1850,    # Dash
        252216,  # Tiger Dash
        783,     # Travel Form
        5215,    # Prowl
        102359,  # Mass Entanglement
        132469,  # Typhoon
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
