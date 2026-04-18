"""Tests for the user-triggered cold-parse endpoint (POST /api/player/.../parse)
and the updated get_player_profile behavior (no more auto-ingest on cold GET).

Covers:
  - 409 when player is already in DB.
  - 200 success path for a cold parse.
  - 404 when ingest returns result with player=None.
  - 429 when cold-parse cooldown is still active.
  - 429 on WCLRateLimitedError from ingest.
  - 502 on generic ingest failure.
  - Independent cooldown proof: cold-parse and refresh limits are separate.
  - get_player_profile returns not_indexed=True for unknown characters with
    zero ingest calls.

Slowapi per-IP daily cap is not tested here — that infra is exercised by
test_api_auth.py.
"""
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

import app.main as main_module
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


def _fake_ingest_success(player, runs=5):
    """Return a factory that produces a successful ingest result mock."""
    def _inner(name, realm, region):
        result = MagicMock()
        result.player = player
        result.runs_ingested = runs  # not used directly, but present for clarity
        return result
    return _inner


# ---------------------------------------------------------------------------
# 409 — player already in DB
# ---------------------------------------------------------------------------

def test_parse_409_when_already_indexed(client, db_session):
    """Parse endpoint must return 409 with code='already_indexed' when the
    character already exists in our database. Frontend should pivot to Refresh."""
    _make_player(db_session)

    r = client.post("/api/player/EU/TarrenMill/Mooyuh/parse")
    assert r.status_code == 409
    body = r.json()
    assert body["detail"]["code"] == "already_indexed"


# ---------------------------------------------------------------------------
# 200 — success path
# ---------------------------------------------------------------------------

def test_parse_200_success(client, db_session, monkeypatch):
    """Happy path: character not in DB, ingest succeeds and returns a Player row.
    Response must have ok=True and an integer runs_ingested."""

    created_player = None

    def _fake_ingest(name, realm, region):
        nonlocal created_player
        # Simulate ingest creating the player row.
        created_player = _make_player(
            db_session, name=name, realm=realm, region=region,
            last_ingested_at=datetime.utcnow(),
        )
        result = MagicMock()
        result.player = created_player
        return result

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Ghostplayer/parse")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body["runs_ingested"], int)
    assert body["runs_ingested"] >= 0


def test_parse_200_runs_ingested_zero_is_valid(client, db_session, monkeypatch):
    """runs_ingested=0 is a valid success when the character has no M+ logs yet."""

    def _fake_ingest(name, realm, region):
        p = _make_player(db_session, name=name, realm=realm, region=region)
        result = MagicMock()
        result.player = p
        return result

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Newcharacter/parse")
    assert r.status_code == 200, r.text
    assert r.json()["runs_ingested"] == 0


# ---------------------------------------------------------------------------
# 404 — character not found on WCL
# ---------------------------------------------------------------------------

def test_parse_404_when_ingest_returns_no_player(client, monkeypatch):
    """When ingest returns a result with player=None, surface 404 with
    code='not_found' so the frontend can show the ClaimForm fallback."""

    def _fake_ingest(name, realm, region):
        result = MagicMock()
        result.player = None
        result.reason = "wcl_not_found"
        return result

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Doesnotexist/parse")
    assert r.status_code == 404
    body = r.json()
    assert body["detail"]["code"] == "not_found"
    assert body["detail"]["reason"] == "wcl_not_found"


def test_parse_404_when_ingest_returns_none(client, monkeypatch):
    """Edge case: ingest wrapper itself returns None (shouldn't happen, but be
    defensive)."""

    def _fake_ingest(name, realm, region):
        return None

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _fake_ingest)

    r = client.post("/api/player/EU/TarrenMill/Nullplayer/parse")
    assert r.status_code == 404
    body = r.json()
    assert body["detail"]["code"] == "not_found"


# ---------------------------------------------------------------------------
# 429 — per-(IP, character) cold-parse cooldown
# ---------------------------------------------------------------------------

def test_parse_429_when_cooldown_active(client, monkeypatch):
    """When the in-memory TTL dict already has a recent entry for the (IP, char)
    combination, the endpoint must return 429 with code='cold_parse_cooldown_active'."""
    import hashlib
    from app.config import settings

    # Determine the ip_hash the endpoint will compute for the TestClient IP.
    # TestClient uses 127.0.0.1 (or testclient).
    test_ip = "testclient"
    salt = settings.api_key or "umbra-fallback-salt"
    ip_hash = hashlib.sha256(f"{test_ip}:{salt}".encode()).hexdigest()

    # Manually seed the cooldown dict as if a parse just happened.
    key = (ip_hash, "EU", "TarrenMill", "ghostplayer")
    with main_module._cold_parse_lock:
        main_module._cold_parse_attempts[key] = time.time()

    try:
        r = client.post("/api/player/EU/TarrenMill/Ghostplayer/parse")
        assert r.status_code == 429
        body = r.json()
        assert body["detail"]["code"] == "cold_parse_cooldown_active"
        assert "retry_after_seconds" in body["detail"]
        assert body["detail"]["retry_after_seconds"] > 0
    finally:
        # Clean up so other tests aren't affected.
        with main_module._cold_parse_lock:
            main_module._cold_parse_attempts.pop(key, None)


def test_parse_429_cooldown_message_contains_hours(client, monkeypatch):
    """The cooldown message must include an hours estimate for the frontend."""
    import hashlib
    from app.config import settings

    test_ip = "testclient"
    salt = settings.api_key or "umbra-fallback-salt"
    ip_hash = hashlib.sha256(f"{test_ip}:{salt}".encode()).hexdigest()

    key = (ip_hash, "EU", "TarrenMill", "clockplayer")
    with main_module._cold_parse_lock:
        main_module._cold_parse_attempts[key] = time.time()

    try:
        r = client.post("/api/player/EU/TarrenMill/Clockplayer/parse")
        assert r.status_code == 429
        msg = r.json()["detail"]["message"]
        assert "h" in msg or "hour" in msg.lower()
    finally:
        with main_module._cold_parse_lock:
            main_module._cold_parse_attempts.pop(key, None)


# ---------------------------------------------------------------------------
# 429 — WCL rate-limited mid-ingest
# ---------------------------------------------------------------------------

def test_parse_429_on_wcl_rate_limit(client, monkeypatch):
    """When WCL rate-limits us during ingest the endpoint returns 429 with
    code='wcl_rate_limited' rather than 502."""
    from app.wcl.client import WCLRateLimitedError

    def _rate_limited(name, realm, region):
        raise WCLRateLimitedError(retry_after_seconds=120)

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _rate_limited)

    r = client.post("/api/player/EU/TarrenMill/Rateplayer/parse")
    assert r.status_code == 429
    assert r.json()["detail"]["code"] == "wcl_rate_limited"


# ---------------------------------------------------------------------------
# 502 — generic ingest failure
# ---------------------------------------------------------------------------

def test_parse_502_on_ingest_failure(client, monkeypatch):
    """When the ingest wrapper raises an unexpected exception the endpoint
    returns 502 with code='ingest_failed' rather than leaking a 500."""

    def _boom(name, realm, region):
        raise RuntimeError("Something exploded")

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _boom)

    r = client.post("/api/player/EU/TarrenMill/Boomchar/parse")
    assert r.status_code == 502
    assert r.json()["detail"]["code"] == "ingest_failed"


# ---------------------------------------------------------------------------
# Independent cooldown proof
# ---------------------------------------------------------------------------

def test_parse_and_refresh_cooldowns_are_independent(client, db_session, monkeypatch):
    """Seeding the refresh cooldown on an existing player must NOT prevent a
    different uncached character from being cold-parsed from the same IP.
    The two endpoints have separate rate-limit mechanisms.
    """
    # Put an existing player in refresh cooldown (stamped just now).
    _make_player(db_session, name="Existingplayer", last_ingested_at=datetime.utcnow())

    # Verify refresh is blocked for the existing player.
    r_refresh = client.post("/api/player/EU/TarrenMill/Existingplayer/refresh")
    assert r_refresh.status_code == 429
    assert r_refresh.json()["detail"]["code"] == "cooldown_active"

    # Cold-parse a DIFFERENT uncached character — should not be blocked.
    parse_called = []

    def _fake_ingest(name, realm, region):
        parse_called.append((name, realm, region))
        p = _make_player(db_session, name=name, realm=realm, region=region)
        result = MagicMock()
        result.player = p
        return result

    monkeypatch.setattr(main_module, "_ingest_player_inline_wrapper", _fake_ingest)

    r_parse = client.post("/api/player/EU/TarrenMill/Freshcharacter/parse")
    # Ingest must have been called (cold-parse cooldown not blocking).
    assert len(parse_called) == 1
    # Status is 200 (ingest succeeded).
    assert r_parse.status_code == 200, r_parse.text


# ---------------------------------------------------------------------------
# get_player_profile — not_indexed=True path (no auto-ingest)
# ---------------------------------------------------------------------------

def test_get_player_profile_returns_not_indexed_for_unknown(client, monkeypatch):
    """GET /all for an unknown character must return 200 with not_indexed=True
    and must NOT call _ingest_player_inline_wrapper."""
    ingest_calls = []

    def _should_not_be_called(name, realm, region):
        ingest_calls.append((name, realm, region))
        result = MagicMock()
        result.player = None
        return result

    monkeypatch.setattr(
        main_module, "_ingest_player_inline_wrapper", _should_not_be_called
    )

    r = client.get("/api/player/EU/TarrenMill/Completestranger/all")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["not_indexed"] is True
    assert body["scores"] == []
    assert body["recent_runs"] == []
    assert body["total_runs"] == 0
    assert len(ingest_calls) == 0, "Auto-ingest must NOT fire on cold GET"


def test_get_player_profile_not_indexed_preserves_identity(client, monkeypatch):
    """The not_indexed response must echo back the canonicalized identity so
    the frontend can render the character name/realm/region correctly."""
    monkeypatch.setattr(
        main_module,
        "_ingest_player_inline_wrapper",
        lambda *a: MagicMock(player=None),
    )

    r = client.get("/api/player/eu/tarrenmill/someplayer/all")
    assert r.status_code == 200
    body = r.json()
    assert body["not_indexed"] is True
    assert body["name"] == "Someplayer"
    assert body["realm"] == "tarrenmill"
    assert body["region"] == "EU"


def test_get_player_profile_cached_player_not_not_indexed(client, db_session):
    """A player that IS in the DB must NOT have not_indexed=True."""
    _make_player(db_session)

    r = client.get("/api/player/EU/TarrenMill/Mooyuh/all")
    assert r.status_code == 200
    body = r.json()
    assert body.get("not_indexed", False) is False
    assert body["name"] == "Mooyuh"
