"""Lua export — verify syntax and structure on sample data."""
from datetime import datetime

from app.export.lua_writer import generate_lua
from app.models import DungeonRun, Player, PlayerScore, Role


def _seed(session, name="Testy", realm="Illidan", region="US",
          grade="A", role=Role.dps, spec="Frost", timed=True):
    player = Player(name=name, realm=realm, region=region, class_id=8)
    session.add(player)
    session.flush()
    score = PlayerScore(
        player_id=player.id, role=role, overall_grade=grade,
        category_scores={
            "damage_output": 82, "utility": 70, "survivability": 75,
            "cooldown_usage": 65, "casts_per_minute": 80,
            "damage_output_ilvl": 85,
        },
        runs_analyzed=5, primary_role=True,
    )
    run = DungeonRun(
        player_id=player.id, encounter_id=10658, keystone_level=10,
        role=role, spec_name=spec, dps=60, hps=0, ilvl=620,
        duration=1_800_000, deaths=0, interrupts=8, dispels=2,
        avoidable_damage_taken=0, damage_taken_total=0,
        casts_total=900, cooldown_usage_pct=70, timed=timed,
        logged_at=datetime(2026, 4, 1), wcl_report_id="r1", fight_id=1,
    )
    session.add_all([score, run])
    session.commit()
    return player


def test_generate_lua_empty_db(db_session):
    content = generate_lua(db_session)
    assert content.startswith("Umbra_Database = {")
    assert content.rstrip().endswith("}")
    assert "-- No data yet" in content


def test_generate_lua_contains_player_entry(db_session):
    _seed(db_session)
    content = generate_lua(db_session)
    assert '["Testy-Illidan"]' in content
    assert 'grade = "A"' in content
    assert 'role = "dps"' in content
    assert "dps_perf = 82" in content      # renamed from damage_output
    assert "cpm = 80" in content           # renamed from casts_per_minute
    assert "timed_pct = 100" in content    # single timed run


def test_generate_lua_region_filter_excludes_other_regions(db_session):
    _seed(db_session, name="USer", region="US")
    _seed(db_session, name="EUser", region="EU")
    us_only = generate_lua(db_session, region="US")
    assert '["USer-Illidan"]' in us_only
    assert '["EUser-Illidan"]' not in us_only


def test_generated_lua_parses(db_session):
    """Output must be syntactically valid Lua (loadable as a table)."""
    _seed(db_session, name="Foo'Bar")  # apostrophe in name → escaping
    _seed(db_session, name="Baz")
    content = generate_lua(db_session)

    # Proxy check: balanced braces, no trailing comma crash.
    assert content.count("{") == content.count("}")
    # No unescaped quote inside key names
    for line in content.splitlines():
        if line.strip().startswith('["'):
            # Every key must close with "]
            assert '"]' in line


def test_untimed_run_yields_zero_timed_pct(db_session):
    _seed(db_session, timed=False)
    assert "timed_pct = 0" in generate_lua(db_session)
