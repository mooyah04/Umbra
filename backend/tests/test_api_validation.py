"""API-level validation wiring — bad identity should 400, not 500."""
import os


def test_single_char_realm_rejected_by_api(client):
    # A literal slash can't reach the handler (the router treats it as a
    # segment separator), so we test a realm that reaches the validator
    # and fails its length check.
    r = client.get("/api/player/us/A/Mooyuh")
    assert r.status_code == 400
    assert "realm" in r.json()["detail"].lower()


def test_invalid_region_rejected_by_api(client):
    r = client.get("/api/player/usa/TarrenMill/Mooyuh")
    assert r.status_code == 400
    assert "region" in r.json()["detail"].lower()


def test_too_short_name_rejected_by_api(client):
    r = client.get("/api/player/us/TarrenMill/A")
    assert r.status_code == 400
    assert "name" in r.json()["detail"].lower()


def test_ingest_batch_rejects_bad_row(client):
    r = client.post(
        "/api/ingest",
        json={"players": [
            {"name": "Mooyuh", "realm": "Tarren Mill", "region": "EU"},
            {"name": "X", "realm": "Tarren Mill", "region": "EU"},  # too short
        ]},
        headers={"X-API-Key": os.environ["API_KEY"]},
    )
    assert r.status_code == 422  # Pydantic validation error
    # Error should reference the bad row index
    body_text = r.text.lower()
    assert "players[1]" in body_text or "name" in body_text


def test_ingest_batch_enforces_max_size(client):
    too_many = [
        {"name": f"Player{i}", "realm": "Tarren Mill", "region": "EU"}
        for i in range(501)
    ]
    r = client.post(
        "/api/ingest",
        json={"players": too_many},
        headers={"X-API-Key": os.environ["API_KEY"]},
    )
    assert r.status_code == 422


def test_ingest_batch_rejects_empty_players_list(client):
    r = client.post(
        "/api/ingest",
        json={"players": []},
        headers={"X-API-Key": os.environ["API_KEY"]},
    )
    assert r.status_code == 422
