"""Per-spec defensive-cleanse school registry.

Maps `(class_id, spec_name)` to the set of debuff schools the spec can
remove from allies. Drives healer-utility-of-cleanses scoring so a
spec is only credited for schools its kit actually covers.

Why this exists: the BRM audit (2026-04-26) found that
`class_has_dispel(Monk)=True` was treating every Monk as a full magic
dispeller, which is wrong — Brewmaster and Windwalker have Detox
which is poison/disease only. Mistweaver has the healer Detox which
adds Magic. The same pattern repeats across classes (Holy Pal vs
Prot/Ret Pal, Resto Druid vs other Druids, Resto Shaman vs DPS Shaman,
etc.) so the per-spec mapping is the right granularity.

All 13 classes (39 specs counting Devourer) are audited as of
2026-04-27. Engine wiring (the path that *reads* this registry to
compute healer cleanse credit) is deferred until a follow-up commit
so the audit data lands first; the existing `class_has_dispel` path
keeps running until the wiring lands. Wiring change blocked on:
- Defining how `Bleed` (Evoker-only) should score, since no other
  class can clear bleeds and per-dungeon bleed availability varies.
- Confirming Cauterizing Flame's school list before locking the
  Evoker entries (sampler suggests Bleed/Poison/Disease/Curse for
  the all-spec version).
"""

from typing import Literal

# Bleed is unique to Evoker (Cauterizing Flame). All other defensive
# cleanses fall in the standard {Magic, Poison, Disease, Curse} set
# with Enrage reserved for offensive purges (Soothe, Tranq Shot) that
# never go in this registry.
DispelSchool = Literal["Magic", "Poison", "Disease", "Curse", "Enrage", "Bleed"]

# (class_id, spec_name) -> frozenset of schools the spec can defensively
# cleanse from allies. Empty set means the spec cannot cleanse anything
# (the cleanse-utility scoring path should skip these specs entirely
# rather than score them 0, which would punish a kit gap).
#
# Offensive purges (Tranquilizing Shot, Mass Dispel offensive use,
# Purge, Soothe, Consume Magic, Shattering Throw) are NOT in this
# registry — they're an offensive utility lane and need their own
# scoring path if/when one is added.
SPEC_DISPEL_SCHOOLS: dict[tuple[int, str], frozenset[DispelSchool]] = {
    # Warrior (1) — no defensive cleanse on any spec
    (1, "Arms"): frozenset(),
    (1, "Fury"): frozenset(),
    (1, "Protection"): frozenset(),

    # Paladin (2) — Holy splits from Prot/Ret. Cleanse vs Cleanse Toxins.
    (2, "Holy"): frozenset({"Magic", "Poison", "Disease"}),
    (2, "Protection"): frozenset({"Poison", "Disease"}),
    (2, "Retribution"): frozenset({"Poison", "Disease"}),

    # Death Knight (6) — no defensive cleanse on any spec.
    # Anti-Magic Shell / AMZ are absorbs, not dispels.
    (6, "Blood"): frozenset(),
    (6, "Frost"): frozenset(),
    (6, "Unholy"): frozenset(),

    # Monk (10) — MW splits from BRM/WW. Healer Detox covers Magic.
    (10, "Brewmaster"): frozenset({"Poison", "Disease"}),
    (10, "Mistweaver"): frozenset({"Magic", "Poison", "Disease"}),
    (10, "Windwalker"): frozenset({"Poison", "Disease"}),

    # Druid (11) — Resto splits from other Druids. Nature's Cure vs
    # Remove Corruption.
    (11, "Balance"): frozenset({"Poison", "Curse"}),
    (11, "Feral"): frozenset({"Poison", "Curse"}),
    (11, "Guardian"): frozenset({"Poison", "Curse"}),
    (11, "Restoration"): frozenset({"Magic", "Poison", "Curse"}),

    # Demon Hunter (12) — no defensive cleanse on any spec.
    # Consume Magic is an offensive purge from enemies, not a cleanse.
    (12, "Havoc"): frozenset(),
    (12, "Vengeance"): frozenset(),
    (12, "Devourer"): frozenset(),

    # Priest (5) — Disc/Holy share Purify; Shadow has Dispel Magic
    # (Magic only, defensive ally-cleanse mode).
    (5, "Discipline"): frozenset({"Magic", "Disease"}),
    (5, "Holy"): frozenset({"Magic", "Disease"}),
    (5, "Shadow"): frozenset({"Magic"}),

    # Shaman (7) — Resto splits from Ele/Enh. Cleanse Spirit (Curse only)
    # vs Purify Spirit (Magic + Curse).
    (7, "Elemental"): frozenset({"Curse"}),
    (7, "Enhancement"): frozenset({"Curse"}),
    (7, "Restoration"): frozenset({"Magic", "Curse"}),

    # Hunter (3) — no defensive cleanse on any spec.
    # Tranquilizing Shot is offensive (Enrage/Magic purge from enemies),
    # never an ally cleanse.
    (3, "Beast Mastery"): frozenset(),
    (3, "Marksmanship"): frozenset(),
    (3, "Survival"): frozenset(),

    # Rogue (4) — no defensive cleanse on any spec.
    (4, "Assassination"): frozenset(),
    (4, "Outlaw"): frozenset(),
    (4, "Subtlety"): frozenset(),

    # Mage (8) — Remove Curse covers Curse only; all three specs share it.
    # Spellsteal is offensive Magic purge from enemies, never an ally
    # cleanse.
    (8, "Arcane"): frozenset({"Curse"}),
    (8, "Fire"): frozenset({"Curse"}),
    (8, "Frost"): frozenset({"Curse"}),

    # Warlock (9) — no defensive cleanse on allies in any spec.
    # Imp Singe Magic and Felhunter Devour Magic are pet-side offensive
    # purges from enemies, not defensive ally cleanses.
    (9, "Affliction"): frozenset(),
    (9, "Demonology"): frozenset(),
    (9, "Destruction"): frozenset(),

    # Evoker (13) — Cauterizing Flame is the cross-spec all-spec cleanse
    # (Bleed/Poison/Disease/Curse). Naturalize is Pres-only and adds
    # Magic. Final school lists pending Logan confirmation per the
    # Batch 3 audit's open question.
    (13, "Augmentation"): frozenset({"Bleed", "Poison", "Disease", "Curse"}),
    (13, "Devastation"): frozenset({"Bleed", "Poison", "Disease", "Curse"}),
    (13, "Preservation"): frozenset({"Magic", "Bleed", "Poison", "Disease", "Curse"}),
}


def get_dispel_schools(class_id: int, spec_name: str) -> frozenset[DispelSchool]:
    """Return the set of schools this spec can defensively cleanse from
    allies. Returns an empty frozenset for unknown specs OR specs with
    no cleanse — callers should treat empty as "skip cleanse scoring"
    rather than "0 score".
    """
    return SPEC_DISPEL_SCHOOLS.get((class_id, spec_name), frozenset())
