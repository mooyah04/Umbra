"""Retribution Paladin rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="retribution_paladin",
    display_name="Retribution Paladin",
    class_id=2,
    spec_name="Retribution",
    aliases={},
    rotation_ids=frozenset({
        85256,   # Templar's Verdict
        20271,   # Judgment
        35395,   # Crusader Strike
        53385,   # Divine Storm
        24275,   # Hammer of Wrath
        184575,  # Blade of Justice
        255937,  # Wake of Ashes
        383328,  # Final Verdict (talent)
        427453,  # Justicar's Vengeance
        431717,  # Hammer of Light
        407480,  # Templar Slash (Hero talent)
        406647,  # Templar Strike
    }),
    cooldown_ids=frozenset({
        31884,   # Avenging Wrath
        231895,  # Crusade
        375576,  # Divine Toll
        343721,  # Final Reckoning
        633,     # Lay on Hands
        498,     # Divine Protection
        642,     # Divine Shield
        1022,    # Blessing of Protection
        6940,    # Blessing of Sacrifice
        389539,  # Sentinel
    }),
    utility_ids=frozenset({
        853,     # Hammer of Justice
        62124,   # Hand of Reckoning (Taunt)
        4987,    # Cleanse Toxins
        1044,    # Blessing of Freedom
        96231,   # Rebuke (interrupt)
        115750,  # Blinding Light
        26573,   # Consecration
        184662,  # Shield of Vengeance
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
