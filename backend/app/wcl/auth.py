import time
import httpx
from app.config import settings


class WCLAuth:
    """Handles OAuth2 client_credentials flow for Warcraft Logs API v2."""

    def __init__(self):
        self._token: str | None = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        if self._token and time.time() < self._expires_at:
            return self._token

        with httpx.Client() as client:
            resp = client.post(
                settings.wcl_token_url,
                data={"grant_type": "client_credentials"},
                auth=(settings.wcl_client_id, settings.wcl_client_secret),
            )
            resp.raise_for_status()
            data = resp.json()

        self._token = data["access_token"]
        # Expire 60s early to avoid edge-case failures
        self._expires_at = time.time() + data["expires_in"] - 60
        return self._token


wcl_auth = WCLAuth()
