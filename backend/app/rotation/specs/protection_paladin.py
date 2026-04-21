"""Protection Paladin rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="protection_paladin",
    display_name="Protection Paladin",
    class_id=2,
    spec_name="Protection",
    aliases={},
    rotation_ids=frozenset({
        31935,   # Avenger's Shield
        275779,  # Judgment (Prot)
        53595,   # Hammer of the Righteous
        204019,  # Blessed Hammer
        53600,   # Shield of the Righteous
        85673,   # Word of Glory
        26573,   # Consecration
        24275,   # Hammer of Wrath
        431717,  # Hammer of Light
    }),
    cooldown_ids=frozenset({
        31850,   # Ardent Defender
        86659,   # Guardian of Ancient Kings
        375576,  # Divine Toll
        31884,   # Avenging Wrath
        633,     # Lay on Hands
        498,     # Divine Protection
        642,     # Divine Shield
        1022,    # Blessing of Protection
        6940,    # Blessing of Sacrifice
        204018,  # Blessing of Spellwarding
        389539,  # Sentinel
        432459,  # Eye of Tyr
    }),
    utility_ids=frozenset({
        853,     # Hammer of Justice
        62124,   # Hand of Reckoning (Taunt)
        4987,    # Cleanse
        1044,    # Blessing of Freedom
        96231,   # Rebuke (interrupt)
        115750,  # Blinding Light
        305539,  # Turn Evil
    }),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
