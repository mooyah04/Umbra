"""Lock in the client-IP resolution logic used by the rate limiter.

get_client_ip has to resist a specific attack: an attacker who learns
the Railway origin hostname bypasses Cloudflare, sets CF-Connecting-IP
themselves to a random address, and rotates the spoofed value to get
unlimited traffic past the per-IP rate limit. These tests pin the
verification path (Cloudflare IP must appear in X-Forwarded-For before
CF-Connecting-IP is trusted) so that regression never ships silently.
"""
import ipaddress
from unittest.mock import MagicMock

from app import security
from app.security import get_client_ip


class _CaseInsensitiveHeaders:
    """Minimal stand-in for starlette's Headers (case-insensitive .get)."""

    def __init__(self, headers: dict[str, str]):
        self._h = {k.lower(): v for k, v in headers.items()}

    def get(self, key: str, default=None):
        return self._h.get(key.lower(), default)


def _mk_request(headers: dict[str, str], client_host: str | None = None):
    req = MagicMock()
    req.headers = _CaseInsensitiveHeaders(headers)
    if client_host is None:
        req.client = None
    else:
        req.client = MagicMock()
        req.client.host = client_host
    return req


def _with_cloudflare_ranges(monkeypatch, ranges: list[str]):
    monkeypatch.setattr(
        security,
        "_CLOUDFLARE_NETWORKS",
        [ipaddress.ip_network(r) for r in ranges],
    )


def test_cf_connecting_ip_trusted_when_cloudflare_in_chain(monkeypatch):
    _with_cloudflare_ranges(monkeypatch, ["173.245.48.0/20"])
    req = _mk_request(
        headers={
            "CF-Connecting-IP": "203.0.113.42",
            "X-Forwarded-For": "203.0.113.42, 173.245.48.1, 10.0.0.5",
        },
        client_host="10.0.0.5",
    )
    assert get_client_ip(req) == "203.0.113.42"


def test_cf_connecting_ip_ignored_when_no_cloudflare_in_chain(monkeypatch):
    # Attacker direct-to-origin: sets the header themselves, no CF hop.
    _with_cloudflare_ranges(monkeypatch, ["173.245.48.0/20"])
    req = _mk_request(
        headers={
            "CF-Connecting-IP": "203.0.113.42",  # spoofed
            "X-Forwarded-For": "1.2.3.4",  # no cloudflare ip
        },
        client_host="1.2.3.4",
    )
    # Should fall through to XFF's first entry, not trust the spoof.
    assert get_client_ip(req) == "1.2.3.4"


def test_cf_connecting_ip_ignored_when_range_list_unloaded(monkeypatch):
    # Fail-safe: if the Cloudflare range fetch failed at startup, we
    # MUST NOT trust the header blindly — otherwise an attacker wins on
    # startup fetch failure.
    _with_cloudflare_ranges(monkeypatch, [])
    req = _mk_request(
        headers={
            "CF-Connecting-IP": "203.0.113.42",
            "X-Forwarded-For": "203.0.113.42, 173.245.48.1",
        },
        client_host="10.0.0.5",
    )
    assert get_client_ip(req) == "203.0.113.42"  # comes from XFF[0], not CF header trust
    # Importantly the source here was the XFF path, not the CF-trusted
    # path — if we flip the XFF order the result changes. Nail that:
    req2 = _mk_request(
        headers={
            "CF-Connecting-IP": "8.8.8.8",  # different from XFF[0]
            "X-Forwarded-For": "1.2.3.4, 173.245.48.1",
        },
        client_host="10.0.0.5",
    )
    # Without trusted CF ranges, we use XFF[0] = 1.2.3.4 NOT the CF header value.
    assert get_client_ip(req2) == "1.2.3.4"


def test_falls_back_to_xff_first_when_no_cf_header(monkeypatch):
    _with_cloudflare_ranges(monkeypatch, ["173.245.48.0/20"])
    req = _mk_request(
        headers={"X-Forwarded-For": "198.51.100.7, 10.0.0.5"},
        client_host="10.0.0.5",
    )
    assert get_client_ip(req) == "198.51.100.7"


def test_falls_back_to_socket_when_no_proxy_headers(monkeypatch):
    _with_cloudflare_ranges(monkeypatch, ["173.245.48.0/20"])
    req = _mk_request(headers={}, client_host="192.0.2.55")
    assert get_client_ip(req) == "192.0.2.55"


def test_handles_missing_client_object(monkeypatch):
    _with_cloudflare_ranges(monkeypatch, ["173.245.48.0/20"])
    req = _mk_request(headers={}, client_host=None)
    # Last-resort loopback so the limiter always has SOME key.
    assert get_client_ip(req) == "127.0.0.1"
