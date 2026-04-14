"""Dungeon registry — verify season manifest, resolved/unresolved split, lookups."""
from app.scoring.dungeons import (
    active_encounter_ids,
    get_avoidable_abilities,
    get_dungeon,
)
from app.scoring.dungeons.registry import (
    UNIVERSAL_AVOIDABLE,
    unresolved_dungeons,
)
from app.scoring.dungeons.seasons import ACTIVE_SEASON


def test_active_season_is_midnight_s1():
    assert ACTIVE_SEASON.key == "midnight_s1"
    assert ACTIVE_SEASON.wcl_zone_id == 47
    assert len(ACTIVE_SEASON.dungeon_modules) == 8, "Midnight S1 has 8 dungeons"


def test_all_eight_dungeons_loaded():
    """Resolved + unresolved must account for every module in the manifest."""
    total = len(active_encounter_ids()) + len(unresolved_dungeons())
    assert total == len(ACTIVE_SEASON.dungeon_modules)


def test_unresolved_dungeons_have_no_encounter_id():
    for d in unresolved_dungeons():
        assert d.encounter_id == 0


def test_verified_dungeons_have_abilities_and_date():
    for eid in active_encounter_ids():
        d = get_dungeon(eid)
        if d.verified:
            assert d.avoidable_abilities, f"{d.name}: verified=True but no abilities"
            assert d.last_reviewed, f"{d.name}: verified=True but no last_reviewed"


def test_universal_avoidable_always_in_lookup():
    """Every dungeon's avoidable list must include the universal (affix) abilities."""
    for eid in active_encounter_ids():
        ids = get_avoidable_abilities(eid)
        for universal_id, _ in UNIVERSAL_AVOIDABLE:
            assert universal_id in ids


def test_unknown_encounter_still_gets_universal_ids():
    ids = get_avoidable_abilities(99999)
    assert {aid for aid, _ in UNIVERSAL_AVOIDABLE}.issubset(ids)
