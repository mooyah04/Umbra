"""Registry — loads active-season dungeon modules and exposes lookups."""
import importlib

from app.scoring.dungeons._types import DungeonData
from app.scoring.dungeons.seasons import ACTIVE_SEASON


# Universal avoidable abilities — apply regardless of dungeon (affixes, seasonal mechanics).
# Midnight S1 seasonal affix is Xal'atath's Bargain.
UNIVERSAL_AVOIDABLE: tuple[tuple[int, str], ...] = (
    (465051, "Xal'atath's Bargain: Devour"),
    (1272894, "Xal'atath's Bargain: Pulsar"),
    (462508, "Dark Prayer"),
)


def _load_active_dungeons() -> tuple[dict[int, DungeonData], list[DungeonData]]:
    """Load active-season dungeons. Dungeons with encounter_id=0 are treated
    as unresolved — kept in a separate list so they don't collide in the lookup."""
    resolved: dict[int, DungeonData] = {}
    unresolved: list[DungeonData] = []
    for module_name in ACTIVE_SEASON.dungeon_modules:
        module = importlib.import_module(f"app.scoring.dungeons.{module_name}")
        dungeon: DungeonData = module.DUNGEON
        if dungeon.encounter_id == 0:
            unresolved.append(dungeon)
        else:
            resolved[dungeon.encounter_id] = dungeon
    return resolved, unresolved


_DUNGEONS, _UNRESOLVED_DUNGEONS = _load_active_dungeons()


def get_dungeon(encounter_id: int) -> DungeonData | None:
    return _DUNGEONS.get(encounter_id)


def active_encounter_ids() -> set[int]:
    return set(_DUNGEONS.keys())


def unresolved_dungeons() -> list[DungeonData]:
    """Active-season dungeons whose WCL encounter_id hasn't been filled in yet."""
    return list(_UNRESOLVED_DUNGEONS)


def get_avoidable_abilities(encounter_id: int) -> set[int]:
    """Return avoidable ability IDs for a dungeon, merged with universal list."""
    ids: set[int] = {aid for aid, _ in UNIVERSAL_AVOIDABLE}
    dungeon = _DUNGEONS.get(encounter_id)
    if dungeon is not None:
        for ability_id, _ in dungeon.avoidable_abilities:
            ids.add(ability_id)
    return ids


def get_all_avoidable_ability_ids() -> set[int]:
    """Return all avoidable ability IDs across active-season dungeons + universal."""
    ids: set[int] = {aid for aid, _ in UNIVERSAL_AVOIDABLE}
    for dungeon in _DUNGEONS.values():
        for ability_id, _ in dungeon.avoidable_abilities:
            ids.add(ability_id)
    return ids


def get_critical_interrupt_ids(encounter_id: int) -> set[int]:
    """Return spell IDs for kicks that matter most in this dungeon.

    Empty set if dungeon unknown or critical_interrupts hasn't been sourced.
    Unlike avoidable abilities, there is no universal critical-kick list —
    priority kicks are always encounter-specific.
    """
    dungeon = _DUNGEONS.get(encounter_id)
    if dungeon is None:
        return set()
    return {spell_id for spell_id, _ in dungeon.critical_interrupts}
