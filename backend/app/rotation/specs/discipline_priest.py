"""Discipline Priest rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="discipline_priest",
    display_name="Discipline Priest",
    class_id=5,
    spec_name="Discipline",
    aliases={},
    rotation_ids=frozenset({
        585,     # Smite
        47540,   # Penance (heal cast)
        47666,   # Penance (damage cast)
        17,      # Power Word: Shield
        589,     # Shadow Word: Pain
        32379,   # Shadow Word: Death
        194509,  # Power Word: Radiance
        8092,    # Mind Blast
        214621,  # Schism
        373178,  # Light's Wrath
        120517,  # Halo
        120644,  # Halo (shadow talent)
        596,     # Prayer of Healing
        2061,    # Flash Heal
        33076,   # Prayer of Mending
        139,     # Renew
    }),
    cooldown_ids=frozenset({
        47536,   # Rapture
        246287,  # Evangelism
        10060,   # Power Infusion
        64843,   # Divine Hymn
        33206,   # Pain Suppression
        62618,   # Power Word: Barrier
        47585,   # Dispersion
        421453,  # Ultimate Penitence
    }),
    utility_ids=frozenset({
        15487,   # Silence (interrupt)
        528,     # Dispel Magic
        527,     # Purify
        586,     # Fade
        73325,   # Leap of Faith
        8122,    # Psychic Scream
        605,     # Mind Control
        453,     # Mind Soothe
        17,      # PW:S (already rotation but also defensive utility)
    }) - frozenset({17}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
