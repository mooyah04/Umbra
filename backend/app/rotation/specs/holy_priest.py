"""Holy Priest rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="holy_priest",
    display_name="Holy Priest",
    class_id=5,
    spec_name="Holy",
    aliases={},
    rotation_ids=frozenset({
        2060,    # Heal
        2061,    # Flash Heal
        33076,   # Prayer of Mending
        596,     # Prayer of Healing
        139,     # Renew
        2050,    # Holy Word: Serenity
        34861,   # Holy Word: Sanctify
        88625,   # Holy Word: Chastise
        204883,  # Circle of Healing
        32546,   # Binding Heal
        585,     # Smite
        14914,   # Holy Fire
        589,     # Shadow Word: Pain
    }),
    cooldown_ids=frozenset({
        64843,   # Divine Hymn
        200183,  # Apotheosis
        47788,   # Guardian Spirit
        64901,   # Symbol of Hope
        265202,  # Holy Word: Salvation
        372835,  # Lightwell
        372760,  # Divine Star
        120517,  # Halo
    }),
    utility_ids=frozenset({
        15487,   # Silence (interrupt — only if talented into)
        528,     # Dispel Magic
        527,     # Purify
        586,     # Fade
        73325,   # Leap of Faith
        8122,    # Psychic Scream
        605,     # Mind Control
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
