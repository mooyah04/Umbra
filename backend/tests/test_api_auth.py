"""API auth + rate-limiting smoke tests.

Focus: the contract of the security layer, not full endpoint behavior.
"""
import os


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_requires_api_key(client):
    r = client.post("/api/ingest", json={"players": []})
    assert r.status_code == 401


def test_ingest_rejects_wrong_api_key(client):
    r = client.post("/api/ingest", json={"players": []}, headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_ingest_accepts_correct_api_key(client, monkeypatch):
    # Patch the pipeline call so we don't hit real WCL — this test is about
    # the auth contract, not ingestion behavior.
    import app.main
    monkeypatch.setattr(app.main, "ingest_batch", lambda session, players: [])
    r = client.post(
        "/api/ingest",
        json={"players": [{"name": "Mooyuh", "realm": "Tarren Mill", "region": "EU"}]},
        headers={"X-API-Key": os.environ["API_KEY"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body == {"ingested": 0, "failed": 1}


def test_player_refresh_requires_api_key(client):
    r = client.get("/api/player/us/illidan/nobody?refresh=true")
    assert r.status_code == 401


def test_player_lookup_without_refresh_no_auth_needed(client):
    # Player doesn't exist + ingestion skipped (refresh=False + no cache)
    # The endpoint will attempt WCL on miss; with no WCL creds it 404s or 500s,
    # but it MUST NOT 401. That's the contract we're testing.
    r = client.get("/api/player/us/illidan/nobody")
    assert r.status_code != 401


def test_rate_limit_exceeded_returns_429(db_engine, monkeypatch):
    """Tight rate limit to confirm 429 wiring, independent of happy-path tests."""
    monkeypatch.setenv("RATE_LIMIT_PUBLIC", "2/minute")

    # Rebuild the app so slowapi picks up the new limit.
    # (Limits are baked at decorator time, so we need a fresh import.)
    import importlib
    import app.config as config_mod
    import app.security as security_mod
    import app.main as main_mod
    importlib.reload(config_mod)
    importlib.reload(security_mod)
    importlib.reload(main_mod)

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session, sessionmaker

    SessionLocal = sessionmaker(db_engine, class_=Session, expire_on_commit=False)

    def _override():
        with SessionLocal() as s:
            yield s

    main_mod.app.dependency_overrides[main_mod.get_session] = _override
    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        codes = [c.get("/api/players/search?q=abc").status_code for _ in range(5)]

    assert 429 in codes, f"rate limiter never fired: {codes}"
    # First two should not be 429 (they may be 200 or 500 depending on DB state).
    assert codes[0] != 429 and codes[1] != 429

    main_mod.app.dependency_overrides.clear()
    # Reset env for other tests
    monkeypatch.setenv("RATE_LIMIT_PUBLIC", "1000/minute")
    importlib.reload(config_mod)
    importlib.reload(security_mod)
    importlib.reload(main_mod)
