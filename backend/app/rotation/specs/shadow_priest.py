"""Shadow Priest rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="shadow_priest",
    display_name="Shadow Priest",
    class_id=5,
    spec_name="Shadow",
    aliases={},
    rotation_ids=frozenset({
        8092,    # Mind Blast
        15407,   # Mind Flay
        32379,   # Shadow Word: Death
        589,     # Shadow Word: Pain
        34914,   # Vampiric Touch
        335467,  # Devouring Plague
        263165,  # Void Torrent
        48045,   # Mind Sear
        205385,  # Shadow Crash
        391109,  # Dark Ascension
        391528,  # (placeholder; remove)
        373481,  # Mind Spike: Insanity
        228260,  # Void Eruption
        391109,  # Dark Ascension (dup)
    }) - frozenset({391528}),
    cooldown_ids=frozenset({
        34433,   # Shadowfiend
        123040,  # Mindbender
        228260,  # Voidform / Void Eruption
        391109,  # Dark Ascension
        10060,   # Power Infusion
        47585,   # Dispersion
        15286,   # Vampiric Embrace
        391109,  # Dark Ascension
    }),
    utility_ids=frozenset({
        15487,   # Silence (interrupt)
        528,     # Dispel Magic
        586,     # Fade
        8122,    # Psychic Scream
        64044,   # Psychic Horror
        605,     # Mind Control
        453,     # Mind Soothe
        73325,   # Leap of Faith
        17,      # Power Word: Shield
        2061,    # Flash Heal
        213634,  # Purify Disease
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
