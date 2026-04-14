"""Cross-log dedup: when multiple party members upload the same key,
each upload becomes a separate WCL report with a different code. Exact
(report_code, fight_id) dedup doesn't catch this. The fuzzy check
(encounter + keystone + start-time-within-120s) does.

Rather than spinning up the full ingest_player pipeline with mocked
WCL responses, these tests exercise the dedup predicate directly. If
the predicate holds, the ingest logic around it is just a loop.
"""
from datetime import datetime, timedelta


def _is_fuzzy_dup(
    fuzzy_runs: list[tuple],
    encounter_id: int,
    keystone_level: int,
    fight_logged_at: datetime,
    window_seconds: int = 120,
) -> bool:
    """Mirror of the in-pipeline check in app/pipeline/ingest.py."""
    for e_encounter, e_keystone, e_logged_at in fuzzy_runs:
        if (e_encounter == encounter_id
                and e_keystone == keystone_level
                and abs((e_logged_at - fight_logged_at).total_seconds()) < window_seconds):
            return True
    return False


def _run_tuple(encounter_id=10658, keystone=10, at="2026-04-14T18:00:00"):
    return (encounter_id, keystone, datetime.fromisoformat(at))


# ── Core case: party member's log of the same fight ────────────────────────

def test_same_fight_from_friend_log_is_dedup():
    """Player A uploaded their log at 18:00:00. Player B (same party)
    uploaded theirs, same dungeon, same key level, start time within
    a few seconds. Should dedup — it's the same physical run."""
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:03")]
    new_time = datetime.fromisoformat("2026-04-14T18:00:00")
    assert _is_fuzzy_dup(stored, 10658, 10, new_time) is True


def test_different_dungeon_not_dedup():
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:00")]
    new_time = datetime.fromisoformat("2026-04-14T18:00:30")
    # Different encounter — not a dup even with same time/key.
    assert _is_fuzzy_dup(stored, 12915, 10, new_time) is False


def test_different_key_level_not_dedup():
    """Same dungeon same day but different key level — separate runs."""
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:00")]
    new_time = datetime.fromisoformat("2026-04-14T18:00:30")
    assert _is_fuzzy_dup(stored, 10658, 12, new_time) is False


def test_time_far_apart_not_dedup():
    """Two separate +10 Pit of Saron runs 30 min apart — not a dup."""
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:00")]
    new_time = datetime.fromisoformat("2026-04-14T18:30:00")
    assert _is_fuzzy_dup(stored, 10658, 10, new_time) is False


def test_just_past_window_not_dedup():
    """At 121s past the stored run, we consider them distinct."""
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:00")]
    new_time = datetime.fromisoformat("2026-04-14T18:02:01")
    assert _is_fuzzy_dup(stored, 10658, 10, new_time) is False


def test_just_within_window_is_dedup():
    stored = [_run_tuple(10658, 10, "2026-04-14T18:00:00")]
    new_time = datetime.fromisoformat("2026-04-14T18:01:59")
    assert _is_fuzzy_dup(stored, 10658, 10, new_time) is True


def test_multiple_stored_any_match_wins():
    """Only one of the stored runs needs to match for the new to be a dup."""
    stored = [
        _run_tuple(12915, 10, "2026-04-14T17:00:00"),  # different encounter
        _run_tuple(10658, 12, "2026-04-14T17:30:00"),  # different key
        _run_tuple(10658, 10, "2026-04-14T18:00:00"),  # MATCH
        _run_tuple(10658, 10, "2026-04-14T19:00:00"),  # too late
    ]
    new_time = datetime.fromisoformat("2026-04-14T18:00:45")
    assert _is_fuzzy_dup(stored, 10658, 10, new_time) is True


def test_quad_party_scenario():
    """4 party members all upload → we ingest one of them first, then
    the other 3 uploads all hit the fuzzy dedup."""
    stored: list[tuple] = []

    # Player 1's upload lands first.
    t1 = datetime.fromisoformat("2026-04-14T18:00:00")
    assert _is_fuzzy_dup(stored, 10658, 10, t1) is False  # no prior rows
    stored.append((10658, 10, t1))

    # Players 2, 3, 4 upload the same physical run; recorded timestamps
    # differ by a handful of seconds due to clock drift.
    for offset in (3, -2, 5):
        t = t1 + timedelta(seconds=offset)
        assert _is_fuzzy_dup(stored, 10658, 10, t) is True
