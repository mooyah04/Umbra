"""API auth + rate limiting.

- `require_api_key` dependency gates admin-only operations (bulk ingest,
  force-refresh). Key comes from the X-API-Key header and is compared against
  settings.api_key using constant-time comparison.

- `limiter` is a slowapi Limiter instance keyed by client IP. Applied to public
  endpoints to prevent scraping and cost attacks against WCL-triggering paths.
"""
import secrets

from fastapi import Header, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


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


limiter = Limiter(key_func=get_remote_address)
