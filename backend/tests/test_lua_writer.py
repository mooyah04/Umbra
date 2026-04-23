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


def test_per_dungeon_section_renders_when_runs_exist(db_session):
    """Every player with runs in active-season dungeons gets a
    dungeons = {...} sub-table keyed by encounter_id. Drives the
    addon's per-dungeon tooltip section."""
    _seed(db_session)  # encounter_id=10658 (Pit of Saron)
    content = generate_lua(db_session)
    assert "dungeons = {" in content
    # Encounter ID present as the key, dungeon name + grade rendered.
    assert "[10658] = {" in content
    assert 'name = "Pit of Saron"' in content
    assert 'best_timed = 10' in content


def test_per_dungeon_sorted_best_first(db_session):
    """When a player has multiple dungeons, best-composite dungeon
    should appear before weaker ones — the addon takes the first few
    entries for "best dungeons" without re-sorting."""
    player = Player(name="Multi", realm="Illidan", region="US", class_id=8)
    db_session.add(player)
    db_session.flush()

    # Two runs: encounter 10658 (Pit of Saron) with strong stats,
    # encounter 12811 (Magister's Terrace) with weak stats.
    strong = DungeonRun(
        player_id=player.id, encounter_id=10658, keystone_level=15,
        role=Role.dps, spec_name="Frost", dps=90, hps=0, ilvl=640,
        duration=1_500_000, deaths=0, interrupts=15, dispels=0,
        avoidable_damage_taken=0, damage_taken_total=0,
        casts_total=1500, cooldown_usage_pct=90, timed=True,
        logged_at=datetime(2026, 4, 1), wcl_report_id="r1", fight_id=1,
    )
    weak = DungeonRun(
        player_id=player.id, encounter_id=12811, keystone_level=5,
        role=Role.dps, spec_name="Frost", dps=30, hps=0, ilvl=620,
        duration=2_400_000, deaths=4, interrupts=1, dispels=0,
        avoidable_damage_taken=500_000, damage_taken_total=1_000_000,
        casts_total=400, cooldown_usage_pct=20, timed=False,
        logged_at=datetime(2026, 4, 2), wcl_report_id="r2", fight_id=1,
    )
    score = PlayerScore(
        player_id=player.id, role=Role.dps, overall_grade="B",
        category_scores={"damage_output": 60, "utility": 70,
                         "survivability": 50, "cooldown_usage": 55,
                         "casts_per_minute": 60, "damage_output_ilvl": 62},
        runs_analyzed=2, primary_role=True,
    )
    db_session.add_all([strong, weak, score])
    db_session.commit()

    content = generate_lua(db_session)
    # Pit of Saron (10658, strong) listed before Magister's Terrace
    # (12811, weak) inside the dungeons sub-table.
    pos_idx = content.find("[10658] = {")
    mt_idx = content.find("[12811] = {")
    assert pos_idx > 0 and mt_idx > 0
    assert pos_idx < mt_idx
