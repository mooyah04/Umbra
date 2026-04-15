"""Blizzard Battle.net Game Data API client — character media fetch only.

Uses OAuth client-credentials flow against oauth.battle.net to get an
access token, then queries <region>.api.blizzard.com for character
profile data. Only the character-media endpoint is used right now —
avatar / inset / main-raw URLs for display on player pages.

All errors are swallowed and returned as None. A missing BNET_CLIENT_ID
or BNET_CLIENT_SECRET disables the integration gracefully — callers get
None back, which the frontend handles by falling back to the spec icon.
"""
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BnetClient:
    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # ── OAuth ─────────────────────────────────────────────────────────────

    def _get_token(self) -> str | None:
        """Cache + refresh a client-credentials access token.

        Returns None if credentials are missing or the token request fails.
        """
        if not settings.bnet_client_id or not settings.bnet_client_secret:
            return None
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token
        try:
            with httpx.Client() as client:
                resp = client.post(
                    settings.bnet_token_url,
                    data={"grant_type": "client_credentials"},
                    auth=(settings.bnet_client_id, settings.bnet_client_secret),
                    timeout=10.0,
                )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + float(data.get("expires_in", 3600))
            return self._token
        except Exception as e:
            logger.warning("Bnet token fetch failed: %s", e)
            return None

    # ── Character media ───────────────────────────────────────────────────

    def get_character_media(
        self,
        region: str,
        realm_slug: str,
        character_name: str,
    ) -> dict[str, str] | None:
        """Fetch {avatar, inset, main-raw} URLs for a character.

        region: 'us'/'eu'/'kr'/'tw'/'cn'
        realm_slug: dash-separated lowercase (WoW's standard slug format)
        character_name: lowercased name

        Returns {'avatar': url, 'inset': url, 'render': url} or None. Any
        missing key means that media variant isn't available.
        """
        token = self._get_token()
        if not token:
            return None

        region_lower = region.lower()
        name_lower = character_name.lower()
        # WoW realm slugs use hyphens for spaces, drop apostrophes. The
        # frontend realm field may already be in slug form or display form;
        # callers should pre-slug it.
        url = (
            f"https://{region_lower}.api.blizzard.com/profile/wow/character/"
            f"{realm_slug}/{name_lower}/character-media"
        )
        namespace = "profile-" + region_lower
        try:
            with httpx.Client() as client:
                resp = client.get(
                    url,
                    params={"namespace": namespace, "locale": "en_US"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )
            if resp.status_code == 404:
                logger.info("Bnet: character not found or hidden: %s/%s (%s)",
                            realm_slug, name_lower, region_lower)
                return None
            resp.raise_for_status()
            data = resp.json()
            result: dict[str, str] = {}
            # Newer API: assets: [{key, value}]. Older: an 'avatar_url' field.
            for asset in data.get("assets", []) or []:
                key = asset.get("key")
                val = asset.get("value")
                if not key or not val:
                    continue
                if key == "avatar":
                    result["avatar"] = val
                elif key == "inset":
                    result["inset"] = val
                elif key in ("main-raw", "main"):
                    result["render"] = val
            # Fallback keys some variants return.
            if "avatar" not in result and "avatar_url" in data:
                result["avatar"] = data["avatar_url"]
            return result or None
        except Exception as e:
            logger.warning("Bnet media fetch failed for %s/%s: %s",
                           realm_slug, name_lower, e)
            return None


    # ── Character profile ────────────────────────────────────────────────

    def get_character_profile(
        self,
        region: str,
        realm_slug: str,
        character_name: str,
    ) -> dict | None:
        """Fetch the canonical character profile (class / race / spec).

        Returned dict: {"class_id": int, "class_name": str, "spec_name": str | None}
        or None if the character is hidden, missing, or the request failed.

        Used as the FIRST class-resolution source during ingest, ahead of
        WCL's character() lookup (which returns non-deterministic entities
        for name-colliding realms). Blizzard's class_id is canonical and
        matches the WCL classID mapping 1-13.
        """
        token = self._get_token()
        if not token:
            return None

        region_lower = region.lower()
        name_lower = character_name.lower()
        url = (
            f"https://{region_lower}.api.blizzard.com/profile/wow/character/"
            f"{realm_slug}/{name_lower}"
        )
        namespace = "profile-" + region_lower
        try:
            with httpx.Client() as client:
                resp = client.get(
                    url,
                    params={"namespace": namespace, "locale": "en_US"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )
            if resp.status_code == 404:
                logger.info("Bnet: profile not found / hidden: %s/%s (%s)",
                            realm_slug, name_lower, region_lower)
                return None
            resp.raise_for_status()
            data = resp.json()
            klass = data.get("character_class") or {}
            spec = data.get("active_spec") or {}
            class_id = klass.get("id")
            if not class_id:
                return None
            return {
                "class_id": int(class_id),
                "class_name": klass.get("name") or "",
                "spec_name": spec.get("name") or None,
            }
        except Exception as e:
            logger.warning("Bnet profile fetch failed for %s/%s: %s",
                           realm_slug, name_lower, e)
            return None


bnet_client = BnetClient()
