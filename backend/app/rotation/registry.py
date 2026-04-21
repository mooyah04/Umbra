"""Rotation spec registry — loads curated per-spec modules and exposes
lookup by (class_id, spec_name).

Mirrors the pattern used by app.scoring.dungeons.registry. Specs whose
data hasn't been curated yet simply aren't in the lookup — the
/rotation endpoint falls back to the unclassified Phase 1 display in
that case.
"""
import importlib

from app.rotation.spec_data import SpecRotationData


# Spell IDs that should never appear in a "rotation" view regardless of
# which spec the player is — trinket procs, dungeon items, potions,
# racials. Centralized here so every per-spec file doesn't have to
# repeat them.
UNIVERSAL_IGNORE_IDS: frozenset[int] = frozenset({
    # Midnight S1 dungeon items + trinket procs seen in sampler data
    1236616,  # Light's Potential (trinket)
    383781,   # Algeth'ar Puzzle (dungeon item)
    # Utility items most classes carry
    6262,     # Healthstone
    109304,   # Exhilaration (racial/Night Fae)
    # Generic auto-attack / melee filler
    1,        # auto-attack (shouldn't show up as a cast but guard anyway)
})


# Module basenames under app.rotation.specs. Add a new spec by creating
# its file and appending the basename here. Order doesn't matter — the
# lookup is keyed by (class_id, spec_name) from the module's data.
ACTIVE_SPEC_MODULES: tuple[str, ...] = (
    # Warrior
    "arms_warrior",
    "fury_warrior",
    "protection_warrior",
    # Paladin
    "holy_paladin",
    "protection_paladin",
    "retribution_paladin",
    # Hunter
    "beast_mastery_hunter",
    "marksmanship_hunter",
    "survival_hunter",
    # Rogue
    "assassination_rogue",
    "outlaw_rogue",
    "subtlety_rogue",
    # Priest
    "discipline_priest",
    "holy_priest",
    "shadow_priest",
    # Death Knight
    "blood_dk",
    "frost_dk",
    "unholy_dk",
    # Shaman
    "elemental_shaman",
    "enhancement_shaman",
    "restoration_shaman",
    # Mage
    "arcane_mage",
    "fire_mage",
    "frost_mage",
    # Warlock
    "affliction_warlock",
    "demonology_warlock",
    "destruction_warlock",
    # Monk
    "brewmaster_monk",
    "mistweaver_monk",
    "windwalker_monk",
    # Druid
    "balance_druid",
    "feral_druid",
    "guardian_druid",
    "restoration_druid",
    # Demon Hunter
    "havoc_dh",
    "vengeance_dh",
    # Evoker
    "devastation_evoker",
    "preservation_evoker",
    "augmentation_evoker",
)


def _load_specs() -> dict[tuple[int, str], SpecRotationData]:
    specs: dict[tuple[int, str], SpecRotationData] = {}
    for module_name in ACTIVE_SPEC_MODULES:
        module = importlib.import_module(f"app.rotation.specs.{module_name}")
        data: SpecRotationData = module.SPEC
        specs[(data.class_id, data.spec_name)] = data
    return specs


_SPECS = _load_specs()


def get_spec_data(class_id: int, spec_name: str) -> SpecRotationData | None:
    """Return the curated data for (class_id, spec_name), or None when
    this spec hasn't been curated yet."""
    return _SPECS.get((class_id, spec_name))


def covered_specs() -> list[tuple[int, str]]:
    """List of (class_id, spec_name) pairs that have curated rotation
    data. Useful for an admin/status endpoint down the line."""
    return list(_SPECS.keys())
