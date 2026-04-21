"""Holy Paladin rotation data."""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="holy_paladin",
    display_name="Holy Paladin",
    class_id=2,
    spec_name="Holy",
    aliases={},
    rotation_ids=frozenset({
        20473,   # Holy Shock
        82326,   # Holy Light
        19750,   # Flash of Light
        85673,   # Word of Glory
        85222,   # Light of Dawn
        35395,   # Crusader Strike
        275773,  # Judgment (Holy)
        53563,   # Beacon of Light
        223306,  # Bestow Faith
        183998,  # Light of the Martyr
    }),
    cooldown_ids=frozenset({
        31884,   # Avenging Wrath
        216331,  # Avenging Crusader
        304971,  # Divine Toll
        633,     # Lay on Hands
        498,     # Divine Protection
        642,     # Divine Shield
        1022,    # Blessing of Protection
        6940,    # Blessing of Sacrifice
        31821,   # Aura Mastery
        200025,  # Beacon of Virtue
    }),
    utility_ids=frozenset({
        853,     # Hammer of Justice
        62124,   # Hand of Reckoning (Taunt)
        4987,    # Cleanse
        1044,    # Blessing of Freedom
        1038,    # Blessing of Kings (if present)
        26573,   # Consecration
        96231,   # Rebuke (interrupt)
        115750,  # Blinding Light
        115310,  # (Monk — wrong, remove this actually)
    }) - frozenset({115310}),
    ignore_ids=frozenset(),
    last_reviewed="2026-04-21",
)
