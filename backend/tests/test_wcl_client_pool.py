"""Multi-client pool behavior for the WCL HTTP client.

Scope: verify that when one credential hits a long 429 cooldown the
router falls over to another credential instead of either sleeping or
raising immediately. We don't hit the real WCL API — httpx.Client.post
is monkeypatched per-test.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from app.wcl.auth import WCLCredential, wcl_auth
from app.wcl.client import (
    WCLRateLimitedError,
    _state_by_id,
    _state_for,
    wcl_client,
)


def _fake_response(status: int, *, json_body: dict | None = None,
                   retry_after: int | None = None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    resp.json = MagicMock(return_value=json_body or {})
    # raise_for_status is a no-op for <400; mirrors httpx behavior close
    # enough for the paths we care about.
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"status={status}")
    return resp


@pytest.fixture
def two_clients(monkeypatch):
    """Swap wcl_auth's pool for two fake credentials and stub token refresh
    so the test never hits the real OAuth endpoint."""
    creds = [
        WCLCredential(client_id="id_A", client_secret="s_A",
                      token="tok_A", expires_at=time.time() + 3600),
        WCLCredential(client_id="id_B", client_secret="s_B",
                      token="tok_B", expires_at=time.time() + 3600),
    ]
    monkeypatch.setattr(wcl_auth, "_credentials", creds)
    # Reset per-client runtime state from other tests.
    _state_by_id.clear()
    return creds


def test_long_retry_after_on_client_a_falls_over_to_client_b(two_clients):
    """If client A returns 429 with Retry-After > cap, the router should
    cool down A and reissue against B rather than sleeping or raising."""
    calls: list[str] = []

    def fake_post(url, **kwargs):
        token = kwargs["headers"]["Authorization"]
        if "tok_A" in token:
            calls.append("A")
            return _fake_response(429, retry_after=3000)
        calls.append("B")
        return _fake_response(200, json_body={"data": {"ok": True}})

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = fake_post
        result = wcl_client.query("query { ok }")

    assert result == {"ok": True}
    assert "A" in calls and "B" in calls, calls
    # Client A should now be cooling.
    assert _state_for(two_clients[0]).cooldown_until > time.time()
    assert _state_for(two_clients[1]).cooldown_until <= time.time()


def test_all_clients_cooling_raises_rate_limited(two_clients):
    """When every client is in a long cooldown, we don't sleep — we raise
    WCLRateLimitedError with the shortest remaining cooldown."""
    now = time.time()
    _state_for(two_clients[0]).cooldown_until = now + 1800
    _state_for(two_clients[1]).cooldown_until = now + 900

    with patch("httpx.Client") as mock_client:
        # Should never actually POST.
        mock_client.return_value.__enter__.return_value.post.side_effect = \
            AssertionError("no request should be made")
        with pytest.raises(WCLRateLimitedError) as excinfo:
            wcl_client.query("query { ok }")

    # Shortest remaining cooldown is ~900s.
    assert 890 <= excinfo.value.retry_after <= 900
