"""Race-guard for concurrent ingest duplicates.

The app-level dedup in `ingest.py` builds an in-memory set of existing
(wcl_report_id, fight_id) per player, then checks new fights against it.
Two ingest calls for the same player running concurrently can both pass
the check before either commits — producing duplicate rows.

We closed this with:
  1. A unique constraint on (player_id, wcl_report_id, fight_id)
     (migration 014).
  2. A savepoint-per-insert in the ingest loop that catches the
     IntegrityError and moves on.

These tests validate the constraint + race handler without needing to
spin up the full WCL-mocked ingest pipeline.
"""
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, DungeonRun, Player, Role


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def _mk_player(session, *, name="RaceGuard", realm="Tarren Mill", region="EU"):
    p = Player(name=name, realm=realm, region=region, class_id=4)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _mk_run(player_id, *, report="abc123", fight=1, enc=62290, key=10):
    from datetime import datetime
    return DungeonRun(
        player_id=player_id,
        encounter_id=enc,
        keystone_level=key,
        role=Role.dps,
        spec_name="Assassination",
        dps=100000.0, hps=0.0, ilvl=640.0,
        duration=1800000,
        deaths=0, interrupts=5, dispels=0,
        avoidable_damage_taken=0.0, damage_taken_total=1000000.0,
        casts_total=500, cooldown_usage_pct=80.0,
        wcl_report_id=report, fight_id=fight,
        timed=True, logged_at=datetime(2026, 4, 1, 12, 0, 0),
    )


def test_duplicate_insert_raises_integrity_error(engine):
    """DB-level uniqueness: inserting the same (player_id, report, fight)
    twice must fail with IntegrityError. Without this, app-level dedup
    racing itself leaves duplicates."""
    SL = sessionmaker(engine, class_=Session, expire_on_commit=False)
    with SL() as s:
        p = _mk_player(s)
        s.add(_mk_run(p.id, report="ABC", fight=1))
        s.commit()
        s.add(_mk_run(p.id, report="ABC", fight=1))
        with pytest.raises(IntegrityError):
            s.commit()


def test_distinct_players_can_share_report_and_fight(engine):
    """The unique key is *scoped to player_id* — two different players in
    the same party can both have a row pointing at the same report+fight
    (the same physical run stored against each of their profiles)."""
    SL = sessionmaker(engine, class_=Session, expire_on_commit=False)
    with SL() as s:
        p1 = _mk_player(s, name="PlayerOne")
        p2 = _mk_player(s, name="PlayerTwo")
        s.add(_mk_run(p1.id, report="SHARED", fight=1))
        s.add(_mk_run(p2.id, report="SHARED", fight=1))
        s.commit()
        rows = s.execute(select(DungeonRun)).scalars().all()
        assert len(rows) == 2


def test_savepoint_swallows_race_without_tanking_batch(engine):
    """Simulates the in-pipeline race-guard: one of N inserts hits the
    unique constraint, the other inserts must still commit. Without the
    savepoint wrapper, the whole transaction would roll back."""
    SL = sessionmaker(engine, class_=Session, expire_on_commit=False)
    with SL() as s:
        p = _mk_player(s)
        # Pre-existing row simulates the concurrent ingest that beat us.
        s.add(_mk_run(p.id, report="R1", fight=5))
        s.commit()

        # New batch: 3 new fights, one of which collides.
        fights = [
            _mk_run(p.id, report="R1", fight=4),
            _mk_run(p.id, report="R1", fight=5),  # collision
            _mk_run(p.id, report="R1", fight=6),
        ]
        committed = []
        race_skipped = 0
        for run in fights:
            try:
                with s.begin_nested():
                    s.add(run)
                    s.flush()
                committed.append(run)
            except IntegrityError:
                # Savepoint rollback handles instance cleanup.
                race_skipped += 1
        s.commit()

        assert race_skipped == 1
        assert len(committed) == 2
        rows = s.execute(select(DungeonRun)).scalars().all()
        # Pre-existing row + fight 4 + fight 6 = 3, fight 5 still only once.
        assert len(rows) == 3
        fight_ids = sorted(r.fight_id for r in rows)
        assert fight_ids == [4, 5, 6]
