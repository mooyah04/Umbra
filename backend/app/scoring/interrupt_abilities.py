"""Interrupt cast spell IDs per class/spec.

Complements `app.scoring.roles` (role + interrupt capability flags)
and `app.scoring.methodology` (hand-curated display names) with the
numeric cast IDs we need to filter WCL's Casts events table when
building per-run utility ability breakdowns.

Kept separate from cc_abilities / dispel_abilities so each "category"
of utility stays easy to extend when Blizzard renames or repurposes
an ability.

WoW class IDs:
  1=Warrior, 2=Paladin, 3=Hunter, 4=Rogue, 5=Priest, 6=DeathKnight,
  7=Shaman, 8=Mage, 9=Warlock, 10=Monk, 11=Druid, 12=DemonHunter,
  13=Evoker
"""

# Class-level interrupt cast IDs. Used for non-healer specs by default,
# plus Mistweaver (keeps the monk kick) and Holy Pally / Resto Shaman
# (healer specs that retain the class interrupt).
CLASS_INTERRUPT: dict[int, tuple[int, str]] = {
    1: (6552, "Pummel"),
    2: (96231, "Rebuke"),
    3: (147362, "Counter Shot"),
    4: (1766, "Kick"),
    6: (47528, "Mind Freeze"),
    7: (57994, "Wind Shear"),
    8: (2139, "Counterspell"),
    9: (19647, "Spell Lock"),      # Felhunter pet interrupt
    10: (116705, "Spear Hand Strike"),
    12: (183752, "Disrupt"),
}


# Spec-specific overrides. None values indicate the spec has no
# baseline interrupt (the pure healers without a class-level kick,
# plus Preservation Evoker).
SPEC_INTERRUPT: dict[tuple[int, str], tuple[int, str] | None] = {
    # Druid — interrupt varies per spec
    (11, "Balance"): (78675, "Solar Beam"),
    (11, "Feral"): (106839, "Skull Bash"),
    (11, "Guardian"): (106839, "Skull Bash"),
    (11, "Restoration"): None,
    # Priest — only Shadow has Silence
    (5, "Shadow"): (15487, "Silence"),
    (5, "Discipline"): None,
    (5, "Holy"): None,
    # Evoker — Preservation has no kick
    (13, "Devastation"): (351338, "Quell"),
    (13, "Augmentation"): (351338, "Quell"),
    (13, "Preservation"): None,
}


def get_interrupt_cast(
    class_id: int, spec_name: str,
) -> tuple[int, str] | None:
    """Return (cast_id, name) for the spec's interrupt, or None.

    Spec override wins; falls back to class-level entry. Returns None
    only for specs that have no baseline interrupt at all (Resto
    Druid, Disc/Holy Priest, Preservation Evoker).
    """
    if (class_id, spec_name) in SPEC_INTERRUPT:
        return SPEC_INTERRUPT[(class_id, spec_name)]
    return CLASS_INTERRUPT.get(class_id)


def build_utility_lookup(
    class_id: int, spec_name: str,
) -> dict[int, tuple[str, str]]:
    """Return {spell_id: (ability_name, category)} for every utility
    cast we track on this class/spec.

    Category values: "interrupt", "cc", "dispel".

    Used by the /runs/{id}/utility endpoint to filter WCL Casts events
    and categorize each hit into the bucket the frontend renders
    under. Centralizing this per-player lookup here keeps the CC +
    interrupt + dispel modules decoupled while presenting a single
    merged view to the caller.
    """
    from app.scoring.cc_abilities import CC_ABILITIES
    from app.scoring.dispel_abilities import get_dispel_casts

    out: dict[int, tuple[str, str]] = {}
    interrupt = get_interrupt_cast(class_id, spec_name)
    if interrupt is not None:
        out[interrupt[0]] = (interrupt[1], "interrupt")
    for spell_id, name in CC_ABILITIES.get(class_id, []):
        out.setdefault(spell_id, (name, "cc"))
    for spell_id, name in get_dispel_casts(class_id):
        out.setdefault(spell_id, (name, "dispel"))
    return out
