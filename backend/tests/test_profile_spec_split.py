"""Profile endpoint's per-spec sub-score split.

Validates that `RoleScore.specs` is populated only when a role spans
multiple specs with enough runs. This is what powers the tab strip on
the profile breakdown card — an over-eager split would clutter the UI
with 1-run vanity tabs; a too-strict one would hide legitimate Sin+Sub
or Ret+Holy-alt splits.
"""
from datetime import datetime, timedelta

from app.models import DungeonRun, Player, PlayerScore, Role


def _mk_player(session, *, class_id=4):
    """Rogue (class 4) by default so tests can exercise multi-DPS-spec splits."""
    p = Player(
        name="SpecSplit",
        realm="Tarren Mill",
        region="EU",
        class_id=class_id,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _mk_score(session, player, role=Role.dps, primary=True):
    """Minimal PlayerScore so the profile endpoint emits a RoleScore."""
    s = PlayerScore(
        player_id=player.id,
        role=role,
        overall_grade="B",
        composite_score=70.0,
        category_scores={"damage_output": 75.0, "utility": 65.0},
        runs_analyzed=10,
        primary_role=primary,
    )
    session.add(s)
    session.commit()


def _mk_runs(session, player, *, spec_name, count, role=Role.dps, encounter_id=62290,
             keystone_level=10):
    """Crank out `count` minimal-but-valid DungeonRuns under one spec."""
    base = datetime.utcnow() - timedelta(days=30)
    for i in range(count):
        run = DungeonRun(
            player_id=player.id,
            encounter_id=encounter_id,
            keystone_level=keystone_level,
            role=role,
            spec_name=spec_name,
            dps=100000.0,
            hps=0.0,
            ilvl=640.0,
            duration=1800000,  # 30min in ms
            deaths=0,
            interrupts=5,
            dispels=0,
            avoidable_damage_taken=0.0,
            damage_taken_total=1000000.0,
            casts_total=500,
            cooldown_usage_pct=80.0,
            wcl_report_id=f"test_{spec_name}_{i}",
            fight_id=i + 1,
            timed=True,
            logged_at=base + timedelta(hours=i),
        )
        session.add(run)
    session.commit()


def test_single_spec_role_emits_empty_specs_list(client, db_session):
    """Rogue with 20 runs all in Assassination — no tabs needed, specs=[]."""
    p = _mk_player(db_session)
    _mk_score(db_session, p)
    _mk_runs(db_session, p, spec_name="Assassination", count=20)

    r = client.get("/api/player/EU/TarrenMill/SpecSplit/all")
    assert r.status_code == 200
    scores = r.json()["scores"]
    assert len(scores) == 1
    assert scores[0]["specs"] == []


def test_multi_spec_role_emits_specs_sorted_by_runs(client, db_session):
    """Rogue with 5 Sin + 3 Outlaw + 2 Sub runs gets 3 specs, top-played first."""
    p = _mk_player(db_session)
    _mk_score(db_session, p)
    _mk_runs(db_session, p, spec_name="Assassination", count=5)
    _mk_runs(db_session, p, spec_name="Outlaw", count=3)
    _mk_runs(db_session, p, spec_name="Subtlety", count=2)

    r = client.get("/api/player/EU/TarrenMill/SpecSplit/all")
    body = r.json()
    specs = body["scores"][0]["specs"]
    assert [s["spec_name"] for s in specs] == [
        "Assassination", "Outlaw", "Subtlety"
    ]
    assert [s["runs_analyzed"] for s in specs] == [5, 3, 2]
    # All three specs clear min_runs_for_grade=3... except Subtlety with 2.
    # Subtlety should have grade=None since runs_analyzed < 3.
    sub = next(s for s in specs if s["spec_name"] == "Subtlety")
    assert sub["grade"] is None
    assert sub["composite_score"] is not None
    sin = next(s for s in specs if s["spec_name"] == "Assassination")
    assert sin["grade"] is not None


def test_one_spec_with_under_threshold_runs_is_excluded(client, db_session):
    """4 Sin + 1 Outlaw run: Outlaw is filtered (below min 2), leaving only
    Sin qualifying. One qualifying spec collapses specs=[] — the tab strip
    would be silly with a single tab."""
    p = _mk_player(db_session)
    _mk_score(db_session, p)
    _mk_runs(db_session, p, spec_name="Assassination", count=4)
    _mk_runs(db_session, p, spec_name="Outlaw", count=1)

    r = client.get("/api/player/EU/TarrenMill/SpecSplit/all")
    assert r.json()["scores"][0]["specs"] == []


def test_spec_category_scores_differ_from_aggregate(client, db_session):
    """Sub-score category breakdown must come from re-scoring the subset,
    not from slicing the aggregate. Use a one-sided load: 5 Sin runs with
    high interrupts + 3 Outlaw runs with zero. The per-spec utility scores
    should differ, which is only possible if each spec was scored alone."""
    p = _mk_player(db_session)
    _mk_score(db_session, p)

    # High-interrupt Sin runs
    _mk_runs(db_session, p, spec_name="Assassination", count=5)
    # Zero-interrupt Outlaw runs — override interrupts on the rows we just created
    # for the Outlaw subset
    from sqlalchemy import select as _sel
    db_session.execute(_sel(DungeonRun))
    outlaw_runs = [
        DungeonRun(
            player_id=p.id, encounter_id=62290, keystone_level=10, role=Role.dps,
            spec_name="Outlaw", dps=100000.0, hps=0.0, ilvl=640.0,
            duration=1800000, deaths=0,
            interrupts=0, dispels=0,  # the knob we're twisting
            avoidable_damage_taken=0.0, damage_taken_total=1000000.0,
            casts_total=500, cooldown_usage_pct=80.0,
            wcl_report_id=f"outlaw_zero_{i}", fight_id=1000 + i, timed=True,
            logged_at=datetime.utcnow() - timedelta(days=1, hours=i),
        )
        for i in range(3)
    ]
    for run in outlaw_runs:
        db_session.add(run)
    db_session.commit()

    r = client.get("/api/player/EU/TarrenMill/SpecSplit/all")
    specs = r.json()["scores"][0]["specs"]
    sin = next(s for s in specs if s["spec_name"] == "Assassination")
    outlaw = next(s for s in specs if s["spec_name"] == "Outlaw")

    # Sin had 5 kicks per run; Outlaw had 0. Utility category for Rogues
    # (no dispel capability) leans on kicks + CC — zero kicks must hurt.
    assert sin["category_scores"]["utility"] > outlaw["category_scores"]["utility"]
