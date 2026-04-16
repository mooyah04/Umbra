"""OAuth2 client-credentials manager for Warcraft Logs API v2.

Supports a pool of client credentials so requests can be distributed
across multiple 18k-points/hr Platinum buckets. Single-client mode is
preserved for local dev and the simplest production setup.
"""
import threading
import time
from dataclasses import dataclass, field

import httpx

from app.config import settings


@dataclass
class WCLCredential:
    """One client_id/client_secret pair and its cached OAuth token."""
    client_id: str
    client_secret: str
    token: str | None = None
    expires_at: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def get_token(self, token_url: str) -> str:
        # Double-checked refresh: one request refreshes, others piggyback.
        now = time.time()
        if self.token and now < self.expires_at:
            return self.token
        with self._lock:
            now = time.time()
            if self.token and now < self.expires_at:
                return self.token
            with httpx.Client() as client:
                resp = client.post(
                    token_url,
                    data={"grant_type": "client_credentials"},
                    auth=(self.client_id, self.client_secret),
                )
                resp.raise_for_status()
                data = resp.json()
            self.token = data["access_token"]
            # Expire 60s early to avoid edge-case failures.
            self.expires_at = time.time() + data["expires_in"] - 60
            return self.token


def _load_credentials() -> list[WCLCredential]:
    """Resolve credentials from settings. Plural lists win if set."""
    ids_raw = (settings.wcl_client_ids or "").strip()
    secrets_raw = (settings.wcl_client_secrets or "").strip()
    if ids_raw and secrets_raw:
        ids = [s.strip() for s in ids_raw.split(",") if s.strip()]
        secrets = [s.strip() for s in secrets_raw.split(",") if s.strip()]
        if len(ids) != len(secrets):
            raise RuntimeError(
                f"WCL_CLIENT_IDS has {len(ids)} entries but "
                f"WCL_CLIENT_SECRETS has {len(secrets)} — must match."
            )
        return [WCLCredential(i, s) for i, s in zip(ids, secrets)]

    # Single-client fallback. Empty credentials are allowed at import
    # time (so tests can monkeypatch) but queries will fail loudly.
    if settings.wcl_client_id and settings.wcl_client_secret:
        return [WCLCredential(settings.wcl_client_id, settings.wcl_client_secret)]
    return []


class WCLAuth:
    """Holds the credential pool. The WCL client asks for a specific
    credential by index; this class is just a registry + token cache."""

    def __init__(self) -> None:
        self._credentials: list[WCLCredential] = _load_credentials()

    def credentials(self) -> list[WCLCredential]:
        return list(self._credentials)

    def get_token_for(self, cred: WCLCredential) -> str:
        return cred.get_token(settings.wcl_token_url)


wcl_auth = WCLAuth()
