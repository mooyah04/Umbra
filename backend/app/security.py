"""API auth + rate limiting.

- `require_api_key` dependency gates admin-only operations (bulk ingest,
  force-refresh). Key comes from the X-API-Key header and is compared against
  settings.api_key using constant-time comparison.

- `limiter` is a slowapi Limiter keyed by real client IP. When the request
  arrives via Cloudflare we read CF-Connecting-IP, verified by checking the
  X-Forwarded-For chain for a known Cloudflare edge IP — otherwise a
  direct-to-origin attacker who set the header themselves would unkeyed
  rate limits. When Cloudflare isn't in the path we fall through to
  standard XFF / socket logic so local dev and tests still work.
"""
import ipaddress
import logging
import secrets
import urllib.request

from fastapi import Header, HTTPException, Request, status
from slowapi import Limiter

from app.config import settings


logger = logging.getLogger(__name__)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject the request unless the X-API-Key header matches settings.api_key.

    If no API key is configured on the server, the endpoint is locked entirely
    (503) — safer than silently allowing unauthenticated writes.
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoint not configured: set UMBRA_API_KEY on the server.",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


# ── Cloudflare IP-range cache ───────────────────────────────────────────────

# Populated at app startup via `refresh_cloudflare_ips()`. When empty (failed
# fetch) we fail SAFE: treat CF-Connecting-IP as untrusted so rate limits
# still key on the observable IP, even if that's a proxy's IP.
_CLOUDFLARE_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

_CLOUDFLARE_V4_URL = "https://www.cloudflare.com/ips-v4"
_CLOUDFLARE_V6_URL = "https://www.cloudflare.com/ips-v6"


def refresh_cloudflare_ips() -> int:
    """Fetch Cloudflare's published edge IP ranges. Called once at app
    startup. Returns the number of ranges loaded; 0 on failure."""
    global _CLOUDFLARE_NETWORKS
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for url in (_CLOUDFLARE_V4_URL, _CLOUDFLARE_V6_URL):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = resp.read().decode("utf-8")
        except Exception as e:
            logger.warning("Failed to fetch Cloudflare IP list %s: %s", url, e)
            continue
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                networks.append(ipaddress.ip_network(line))
            except ValueError as e:
                logger.debug("Skipping invalid Cloudflare CIDR %r: %s", line, e)

    if networks:
        _CLOUDFLARE_NETWORKS = networks
        logger.info("Loaded %d Cloudflare edge IP ranges", len(networks))
    else:
        # Leave whatever was previously cached; empty on first failure.
        logger.warning(
            "Cloudflare IP list empty after refresh; requests claiming "
            "CF-Connecting-IP will be treated as untrusted until the next "
            "successful refresh."
        )
    return len(networks)


def _ip_in_cloudflare_range(ip_str: str) -> bool:
    """True if the given IP is inside any known Cloudflare edge range.

    Returns False when the range list is empty (failed fetch) so we
    never accidentally trust a spoofed CF-Connecting-IP from an attacker
    that bypassed Cloudflare.
    """
    if not _CLOUDFLARE_NETWORKS:
        return False
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(ip in net for net in _CLOUDFLARE_NETWORKS)


# ── Client IP resolution ────────────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """Determine the real client IP for rate limiting.

    Order of preference:
      1. CF-Connecting-IP, IFF the request traversed a Cloudflare edge
         (verified by finding a known Cloudflare IP in the X-Forwarded-For
         chain — the real user's IP is at position 0 and Cloudflare's
         edge IP appears later in the chain).
      2. First IP in X-Forwarded-For (standard proxy convention).
      3. request.client.host (direct socket connection).

    Without step (1)'s verification, an attacker who discovers the
    Railway origin hostname could set CF-Connecting-IP to any value and
    sidestep per-IP rate limits entirely. With verification, spoofing
    requires bouncing through Cloudflare — which is exactly where the
    WAF / bot detection sits.
    """
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        xff = request.headers.get("x-forwarded-for", "")
        chain = [ip.strip() for ip in xff.split(",") if ip.strip()]
        # Also consider the direct socket — some proxies don't append
        # themselves to XFF (Railway's edge does, but defensive).
        if request.client and request.client.host:
            chain.append(request.client.host)
        if any(_ip_in_cloudflare_range(ip) for ip in chain):
            return cf_ip
        # Header present but no Cloudflare IP in chain = spoofed; fall
        # through to the standard logic so the spoofer is still keyed
        # on something they can't trivially change.

    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Leftmost is the origin client per RFC 7239 convention.
        return xff.split(",")[0].strip()

    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=get_client_ip)
