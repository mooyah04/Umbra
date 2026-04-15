"""Leaderboard endpoint regression tests.

Primary motivation: a previous change referenced `Role` without importing
it at module scope, so `GET /api/players/leaderboard?role=tank` returned
500 in prod. Tests here exercise the filter paths so that class of bug
can't ship silently again.
"""
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.models import Player, PlayerScore, Role


def _seed_players(engine) -> None:
    """Insert three players, one per role, with distinct composite scores
    so ordering is unambiguous."""
    SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)
    with SessionLocal() as s:
        players = [
            Player(
                name="Tankboi", realm="Tarren Mill", region="EU",
                class_id=1,  # Warrior
            ),
            Player(
                name="Healqueen", realm="Tarren Mill", region="EU",
                class_id=10,  # Monk
            ),
            Player(
                name="Dpsguy", realm="Tarren Mill", region="US",
                class_id=8,  # Mage
            ),
        ]
        s.add_all(players)
        s.flush()

        s.add_all([
            PlayerScore(
                player_id=players[0].id, role=Role.tank,
                overall_grade="B+", composite_score=75.0,
                category_scores={}, runs_analyzed=5, primary_role=True,
            ),
            PlayerScore(
                player_id=players[1].id, role=Role.healer,
                overall_grade="A-", composite_score=82.0,
                category_scores={}, runs_analyzed=7, primary_role=True,
            ),
            PlayerScore(
                player_id=players[2].id, role=Role.dps,
                overall_grade="A", composite_score=88.0,
                category_scores={}, runs_analyzed=10, primary_role=True,
            ),
        ])
        s.commit()


def test_leaderboard_no_filter_returns_all_sorted_by_composite(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 3
    # Ordered by composite DESC: 88 > 82 > 75.
    assert [row["name"] for row in rows] == ["Dpsguy", "Healqueen", "Tankboi"]
    # Ranks are assigned post-filter, 1-based.
    assert [row["rank"] for row in rows] == [1, 2, 3]


def test_leaderboard_role_tank(client, db_engine):
    """Regression: previously 500'd because Role was imported at local scope."""
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?role=tank&limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["name"] == "Tankboi"
    assert rows[0]["role"] == "tank"


def test_leaderboard_role_healer(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?role=healer&limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert [row["name"] for row in rows] == ["Healqueen"]


def test_leaderboard_role_dps(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?role=dps&limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert [row["name"] for row in rows] == ["Dpsguy"]


def test_leaderboard_unknown_role_returns_400(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?role=support&limit=10")
    assert r.status_code == 400


def test_leaderboard_region_filter(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?region=EU&limit=10")
    assert r.status_code == 200
    names = {row["name"] for row in r.json()}
    assert names == {"Tankboi", "Healqueen"}  # Dpsguy is US


def test_leaderboard_class_filter(client, db_engine):
    _seed_players(db_engine)
    r = client.get("/api/players/leaderboard?class_id=8&limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert [row["name"] for row in rows] == ["Dpsguy"]  # only the Mage


def test_leaderboard_empty_db(client):
    r = client.get("/api/players/leaderboard?limit=10")
    assert r.status_code == 200
    assert r.json() == []
