"""Tests for the user-triggered refresh endpoint (POST /api/player/.../refresh).

Covers: 404 for unknown player, 429 when within cooldown, and the 200
success path. Slowapi per-IP rate limiting is not tested here — that
infra is exercised by test_api_auth.py.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.models import Player


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_player(session, *, name="Mooyuh", realm="Tarren Mill", region="EU",
                 last_ingested_at=None):
    """Insert a minimal Player row and return it."""
    p = Player(
        name=name,
        realm=realm,
        region=region,
        class_id=8,  # Mage
        last_ingested_at=last_ingested_at,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


# ---------------------------------------------------------------------------
# 404 — player not in DB
# ---------------------------------------------------------------------------

def test_refresh_404_for_unknown_player(client):
    """Endpoint must return 404 with code='not_found' when the player has
    never been ingested. This narrows refresh to players we already track."""
    r = client.post("/api/player/EU/TarrenMill/Ghostplayer/refresh")
    assert r.status_code == 404
    body = r.json()
    assert body["detail"]["code"] == "not_found"


# ---------------------------------------------------------------------------
# 429 — per-player cooldown still active
# ---------------------------------------------------------------------------

def test_refresh_429_when_within_cooldown(client, db_session):
    """Endpoint must return 429 with code='cooldown_active' when the player
    was ingested less than refresh_cooldown_seconds ago."""
    # Stamp last_ingested_at to just now so the full cooldown is in effect.
    _make_player(db_session, last_ingested_at=datetime.utcnow())

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 429
    body = r.json()
    assert body["detail"]["code"] == "cooldown_active"
    assert "retry_after_seconds" in body["detail"]
    assert body["detail"]["retry_after_seconds"] > 0
    assert "last_refreshed_at" in body["detail"]


def test_refresh_429_includes_readable_wait_message(client, db_session):
    """The cooldown message should contain a human-readable minute count so
    the frontend can surface it directly without parsing retry_after_seconds."""
    _make_player(db_session, last_ingested_at=datetime.utcnow())

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 429
    msg = r.json()["detail"]["message"]
    assert "m" in msg or "min" in msg.lower()


# ---------------------------------------------------------------------------
# 200 — success path (ingest mocked to avoid real WCL calls)
# ---------------------------------------------------------------------------

def test_refresh_200_success(client, db_session, monkeypatch):
    """Happy path: player exists, outside cooldown, mock ingest succeeds.

    We patch _ingest_player_inline_wrapper to avoid hitting WCL and set
    last_ingested_at on the Player row (simulating what a real ingest writes)
    so the endpoint can read back a fresh timestamp.
    """
    player = _make_player(
        db_session,
        last_ingested_at=datetime.utcnow() - timedelta(hours=2),
    )

    def _fake_ingest(name, realm, region):
        # Simulate ingest writing a fresh last_ingested_at on the row.
        player.last_ingested_at = datetime.utcnow()
        db_session.commit()
        result = MagicMock()
        result.player = player
        return result

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "refreshed_at" in body
    assert "cooldown_ends_at" in body


def test_refresh_200_returns_future_cooldown_ends_at(client, db_session, monkeypatch):
    """cooldown_ends_at must be strictly after refreshed_at (by cooldown window)."""
    player = _make_player(
        db_session,
        last_ingested_at=datetime.utcnow() - timedelta(hours=2),
    )

    def _fake_ingest(name, realm, region):
        player.last_ingested_at = datetime.utcnow()
        db_session.commit()
        result = MagicMock()
        result.player = player
        return result

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 200
    body = r.json()
    refreshed_at = datetime.fromisoformat(body["refreshed_at"])
    cooldown_ends_at = datetime.fromisoformat(body["cooldown_ends_at"])
    assert cooldown_ends_at > refreshed_at


# ---------------------------------------------------------------------------
# 502 — ingest raises a generic exception
# ---------------------------------------------------------------------------

def test_refresh_502_on_ingest_failure(client, db_session, monkeypatch):
    """When the ingest wrapper raises an unexpected exception the endpoint
    returns 502 with code='ingest_failed' rather than leaking a 500."""
    _make_player(
        db_session,
        last_ingested_at=datetime.utcnow() - timedelta(hours=2),
    )

    def _boom(name, realm, region):
        raise RuntimeError("WCL returned garbage")

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _boom)

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 502
    assert r.json()["detail"]["code"] == "ingest_failed"


# ---------------------------------------------------------------------------
# 429 — WCL rate-limited mid-ingest
# ---------------------------------------------------------------------------

def test_refresh_429_on_wcl_rate_limit(client, db_session, monkeypatch):
    """When WCL rate-limits us during ingest the endpoint returns 429 with
    code='wcl_rate_limited' rather than 502, so the frontend can distinguish
    'our backend failed' from 'upstream is temporarily unavailable'."""
    _make_player(
        db_session,
        last_ingested_at=datetime.utcnow() - timedelta(hours=2),
    )

    from app.wcl.client import WCLRateLimitedError

    def _rate_limited(name, realm, region):
        raise WCLRateLimitedError(retry_after_seconds=120)

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _rate_limited)

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert r.status_code == 429
    assert r.json()["detail"]["code"] == "wcl_rate_limited"


# ---------------------------------------------------------------------------
# Cooldown does NOT fire when last_ingested_at is old enough
# ---------------------------------------------------------------------------

def test_refresh_allows_after_cooldown_expires(client, db_session, monkeypatch):
    """Player ingested more than refresh_cooldown_seconds ago must pass the
    cooldown gate and proceed to the ingest step."""
    _make_player(
        db_session,
        last_ingested_at=datetime.utcnow() - timedelta(hours=2),
    )

    called = []

    def _track_ingest(name, realm, region):
        called.append((name, realm, region))
        # Return something that won't crash the endpoint.
        result = MagicMock()
        result.player = None
        return result

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _track_ingest)

    # We don't assert on the final status code here (it may be 200 or 502
    # depending on whether post-ingest re-read finds a row), but we do assert
    # that the ingest was actually called — meaning cooldown was not blocking.
    client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert len(called) == 1


# ---------------------------------------------------------------------------
# Cooldown does NOT fire when last_ingested_at is NULL (stub player)
# ---------------------------------------------------------------------------

def test_refresh_allows_when_never_ingested(client, db_session, monkeypatch):
    """A stub player with last_ingested_at=NULL has never been fully ingested.
    The cooldown check must not block the refresh in this state."""
    _make_player(db_session, last_ingested_at=None)

    called = []

    def _track_ingest(name, realm, region):
        called.append(True)
        result = MagicMock()
        result.player = None
        return result

    import app.main
    monkeypatch.setattr(app.main, "_ingest_player_inline_wrapper", _track_ingest)

    client.post("/api/player/EU/TarrenMill/Mooyuh/refresh")
    assert len(called) == 1
