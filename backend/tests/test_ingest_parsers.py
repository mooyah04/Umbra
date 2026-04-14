"""Lock in the contract between WCL table shapes and our parsers.

The ingest pipeline pulls data out of WCL GraphQL table responses. WCL's
JSON structure is different for each dataType (Interrupts is nested,
DamageTaken is flat-with-abilities, Debuffs uses 'auras', etc.). These
tests use hand-crafted JSON that matches what WCL actually returns, so
if the API shape changes upstream or we mis-parse a table, the test
will catch it before we ingest garbage into the DB.
"""
from app.pipeline.ingest import (
    _count_avoidable_deaths,
    _count_cc_casts,
    _count_cc_casts_from_casts_table,
    _count_critical_interrupts,
    _count_deaths,
    _get_avoidable_damage,
    _get_healing_received,
    _get_nested_stat,
    _get_player_stat,
    _get_total_casts,
)


# ── Interrupts / Dispels (nested table) ─────────────────────────────────────

def test_get_nested_stat_sums_across_interrupted_spells():
    """WCL Interrupts table: entries[interrupted_ability].entries[spell].details[player]."""
    table = {
        "data": {
            "entries": [
                {
                    "guid": 999,  # the ability that got interrupted
                    "entries": [
                        {
                            "details": [
                                {"name": "Mooyuh", "total": 3},
                                {"name": "OtherPlayer", "total": 5},
                            ],
                        },
                    ],
                },
                {
                    "guid": 888,
                    "entries": [
                        {
                            "details": [
                                {"name": "Mooyuh", "total": 2},
                            ],
                        },
                    ],
                },
            ],
        },
    }
    assert _get_nested_stat(table, "Mooyuh") == 5
    assert _get_nested_stat(table, "OtherPlayer") == 5
    assert _get_nested_stat(table, "NotInLog") == 0


def test_get_nested_stat_case_insensitive():
    table = {"data": {"entries": [{"entries": [{"details": [{"name": "MOOYUH", "total": 4}]}]}]}}
    assert _get_nested_stat(table, "mooyuh") == 4


def test_get_nested_stat_empty():
    assert _get_nested_stat({}, "Mooyuh") == 0
    assert _get_nested_stat({"data": {"entries": []}}, "Mooyuh") == 0


# ── Critical interrupts (filters nested table by interrupted ability ID) ────

def test_count_critical_interrupts_only_counts_critical_ids():
    table = {
        "data": {
            "entries": [
                {  # Critical cast
                    "guid": 100,
                    "entries": [{"details": [{"name": "Mooyuh", "total": 2}]}],
                },
                {  # Filler cast — should NOT count
                    "guid": 999,
                    "entries": [{"details": [{"name": "Mooyuh", "total": 10}]}],
                },
            ],
        },
    }
    assert _count_critical_interrupts(table, "Mooyuh", {100}) == 2
    assert _count_critical_interrupts(table, "Mooyuh", {100, 999}) == 12
    assert _count_critical_interrupts(table, "Mooyuh", set()) == 0


# ── Deaths ──────────────────────────────────────────────────────────────────

def test_count_deaths_counts_rows_matching_player():
    table = {
        "data": {
            "entries": [
                {"name": "Mooyuh"},
                {"name": "Mooyuh"},
                {"name": "OtherPlayer"},
                {"name": "mooyuh"},  # case-insensitive
            ],
        },
    }
    assert _count_deaths(table, "Mooyuh") == 3
    assert _count_deaths(table, "OtherPlayer") == 1


def test_count_avoidable_deaths_uses_killing_ability_guid():
    table = {
        "data": {
            "entries": [
                {"name": "Mooyuh", "killingAbility": {"guid": 69021}},  # avoidable
                {"name": "Mooyuh", "killingAbility": {"guid": 11111}},  # not avoidable
                {"name": "Mooyuh", "killingAbility": {"guid": 69024}},  # avoidable
                {"name": "Mooyuh"},                                     # no killing ability
                {"name": "Other",  "killingAbility": {"guid": 69021}},  # wrong player
            ],
        },
    }
    avoidable = {69021, 69024, 70827}
    assert _count_avoidable_deaths(table, "Mooyuh", avoidable) == 2


# ── Damage taken (flat entries with abilities breakdown) ────────────────────

def test_get_avoidable_damage_sums_across_known_abilities():
    table = {
        "data": {
            "entries": [
                {
                    "name": "Mooyuh",
                    "abilities": [
                        {"guid": 69021, "total": 1_000_000},  # avoidable
                        {"guid": 69024, "total":   500_000},  # avoidable
                        {"guid": 11111, "total": 9_000_000},  # not avoidable
                    ],
                },
                {
                    "name": "Other",
                    "abilities": [
                        {"guid": 69021, "total": 7_777_777},
                    ],
                },
            ],
        },
    }
    avoidable = {69021, 69024}
    assert _get_avoidable_damage(table, "Mooyuh", avoidable) == 1_500_000
    assert _get_avoidable_damage(table, "NotInLog", avoidable) == 0
    assert _get_avoidable_damage(table, "Mooyuh", set()) == 0


# ── CC applications (Debuffs table uses 'auras', not 'entries') ─────────────

def test_count_cc_casts_reads_from_auras_list():
    table = {
        "data": {
            "auras": [
                {"guid": 115078, "totalUses": 3},  # Paralysis (Monk CC)
                {"guid": 119381, "totalUses": 2},  # Leg Sweep (Monk CC)
                {"guid": 999999, "totalUses": 20}, # Not a CC — don't count
            ],
        },
    }
    cc_ids = {115078, 119381, 116844}
    assert _count_cc_casts(table, cc_ids) == 5


def test_count_cc_casts_empty_cc_set_is_zero():
    table = {"data": {"auras": [{"guid": 115078, "totalUses": 10}]}}
    assert _count_cc_casts(table, set()) == 0


def test_count_cc_casts_missing_auras_key():
    assert _count_cc_casts({}, {1, 2}) == 0
    assert _count_cc_casts({"data": {}}, {1, 2}) == 0


# ── CC casts from Casts table (the Shaman/pet/totem-friendly approach) ──────

def _casts_table_fixture() -> dict:
    """WCL-shaped Casts table: entries per player, with abilities[] breakdown."""
    return {
        "data": {
            "entries": [
                {
                    "name": "Dobbermon",
                    "total": 1357,
                    "abilities": [
                        {"guid": 973, "name": "Healing Wave", "total": 45},
                        {"guid": 192058, "name": "Capacitor Totem", "total": 4},
                        {"guid": 51514, "name": "Hex", "total": 2},
                        {"guid": 197214, "name": "Sundering", "total": 0},
                    ],
                },
                {
                    "name": "OtherPlayer",
                    "abilities": [
                        {"guid": 192058, "total": 99},  # not our player
                    ],
                },
            ],
        },
    }


def test_cc_from_casts_table_counts_by_player_ability():
    """The real Dobbermon fix: Capacitor Totem casts (192058) now populate
    cc_count via the Casts table, not the debuff table (which misses
    totem-sourced debuffs)."""
    cc_ids = {192058, 51514, 197214}
    assert _count_cc_casts_from_casts_table(
        _casts_table_fixture(), "Dobbermon", cc_ids
    ) == 6  # 4 Capacitor + 2 Hex


def test_cc_from_casts_table_ignores_other_players():
    cc_ids = {192058}
    # Only Dobbermon's 4 Capacitor casts should count, not OtherPlayer's 99.
    assert _count_cc_casts_from_casts_table(
        _casts_table_fixture(), "Dobbermon", cc_ids
    ) == 4


def test_cc_from_casts_table_case_insensitive_name():
    cc_ids = {192058}
    assert _count_cc_casts_from_casts_table(
        _casts_table_fixture(), "DOBBERMON", cc_ids
    ) == 4


def test_cc_from_casts_table_missing_player():
    cc_ids = {192058}
    assert _count_cc_casts_from_casts_table(
        _casts_table_fixture(), "NotInLog", cc_ids
    ) == 0


def test_cc_from_casts_table_empty_ids():
    assert _count_cc_casts_from_casts_table(
        _casts_table_fixture(), "Dobbermon", set()
    ) == 0


def test_cc_from_casts_table_missing_abilities():
    """Player with no abilities[] list (edge: fight had no recorded casts)."""
    table = {"data": {"entries": [{"name": "Dobbermon"}]}}
    assert _count_cc_casts_from_casts_table(table, "Dobbermon", {1}) == 0


# ── Casts total (flat table) ────────────────────────────────────────────────

def test_get_total_casts():
    table = {
        "data": {
            "entries": [
                {"name": "Mooyuh", "total": 1197},
                {"name": "Other", "total": 450},
            ],
        },
    }
    assert _get_total_casts(table, "Mooyuh") == 1197
    assert _get_total_casts(table, "NotInLog") == 0


# ── Player stat (DPS / HPS / damage taken — flat per-player total) ──────────

def test_get_player_stat():
    table = {
        "data": {
            "entries": [
                {"name": "Mooyuh", "total": 12345},
                {"name": "Other", "total": 99999},
            ],
        },
    }
    assert _get_player_stat(table, "Mooyuh") == 12345
    assert _get_player_stat(table, "missing") == 0


# ── Healing received — handles both healer-grouped and target-grouped ───────

def test_get_healing_received_source_grouped_with_targets():
    """When table is source-grouped (viewBy=Source, default), each healer entry
    has a targets[] list. Sum the ones matching our player."""
    table = {
        "data": {
            "entries": [
                {
                    "name": "HealerA",
                    "targets": [
                        {"name": "Mooyuh", "total": 5_000_000},
                        {"name": "Other", "total": 3_000_000},
                    ],
                },
                {
                    "name": "HealerB",
                    "targets": [
                        {"name": "Mooyuh", "total": 2_000_000},
                    ],
                },
            ],
        },
    }
    assert _get_healing_received(table, "Mooyuh") == 7_000_000


def test_get_healing_received_target_grouped_fallback():
    """When table is target-grouped (viewBy=Target), each entry IS a player and
    targets[] is absent. Fall back to entry.total."""
    table = {
        "data": {
            "entries": [
                {"name": "Mooyuh", "total": 8_000_000},
                {"name": "Other", "total": 2_000_000},
            ],
        },
    }
    assert _get_healing_received(table, "Mooyuh") == 8_000_000


def test_get_healing_received_missing_player():
    table = {"data": {"entries": []}}
    assert _get_healing_received(table, "Mooyuh") == 0
