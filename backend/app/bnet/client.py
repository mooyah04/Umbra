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


    # ── Game Data: mythic keystone leaderboard discovery ────────────────
    #
    # Used by the cold-start player-discovery pipeline. Blizzard publishes
    # per-connected-realm / per-dungeon / per-period top-500 leaderboards
    # and every ranked group's 5 members are named + spec'd in the payload.
    # Polling these lets us ingest players who never search themselves on
    # the site — the only requirement for appearing is running the key.

    def _game_data_get(self, region: str, path: str) -> dict | None:
        """GET a Game Data API path under `https://<region>.api.blizzard.com`
        with the dynamic-<region> namespace. Returns parsed JSON or None
        on any error. 404 is a valid "no such resource" outcome and also
        returns None (caller decides whether that's expected).
        """
        token = self._get_token()
        if not token:
            return None
        region_lower = region.lower()
        url = f"https://{region_lower}.api.blizzard.com{path}"
        namespace = "dynamic-" + region_lower
        try:
            with httpx.Client() as client:
                resp = client.get(
                    url,
                    params={"namespace": namespace, "locale": "en_US"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15.0,
                )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning("Bnet game-data GET %s failed: %s", path, e)
            return None

    def get_connected_realms_index(self, region: str) -> list[int]:
        """Return every connected-realm id for a region.

        The index only gives us hrefs like
        `.../connected-realm/509?namespace=dynamic-eu` — extract the id
        from the path so callers can iterate without a second round-trip.
        """
        data = self._game_data_get(region, "/data/wow/connected-realm/index")
        if not data:
            return []
        ids: list[int] = []
        for entry in data.get("connected_realms") or []:
            href = entry.get("href") or ""
            # `.../connected-realm/509?namespace=...`
            try:
                tail = href.split("/connected-realm/", 1)[1]
                rid_str = tail.split("?", 1)[0]
                ids.append(int(rid_str))
            except (IndexError, ValueError):
                continue
        return ids

    def get_connected_realm_slugs(self, region: str, realm_id: int) -> list[str]:
        """Return the realm slugs under a connected-realm id.

        A single connected realm may host several display realms sharing
        the same population pool (e.g. EU 509 hosts Tarren Mill +
        Dead-Wind Pass + ...). We keep them all so matching is tolerant
        to which display realm a player's name lives on.
        """
        data = self._game_data_get(
            region, f"/data/wow/connected-realm/{realm_id}"
        )
        if not data:
            return []
        slugs: list[str] = []
        for r in data.get("realms") or []:
            slug = r.get("slug")
            if slug:
                slugs.append(slug)
        return slugs

    def get_keystone_dungeon_index(self, region: str) -> list[dict]:
        """List every mythic-keystone dungeon known to Blizzard right now.

        We match our WCL encounter ids to Blizzard keystone dungeon ids by
        dungeon NAME (Blizzard's id doesn't overlap with WCL's encounterID
        namespace). Since our season dungeon modules also carry a `name`
        field, this mapping is done once per boot and cached.

        Returns a list of {"id": int, "name": str}.
        """
        data = self._game_data_get(region, "/data/wow/mythic-keystone/dungeon/index")
        if not data:
            return []
        out: list[dict] = []
        for d in data.get("dungeons") or []:
            did = d.get("id")
            name = d.get("name")
            if isinstance(did, int) and name:
                out.append({"id": did, "name": name})
        return out

    def get_current_mythic_period(self, region: str) -> int | None:
        """Return the currently-active mythic-keystone period id.

        Periods tick weekly (Tuesday reset in US, Wednesday in EU/KR).
        Leaderboards are keyed on period id, so we always fetch the
        current value rather than hardcoding.
        """
        data = self._game_data_get(region, "/data/wow/mythic-keystone/period/index")
        if not data:
            return None
        current = data.get("current_period") or {}
        pid = current.get("id")
        return int(pid) if isinstance(pid, int) else None

    def get_mythic_leaderboard(
        self,
        region: str,
        connected_realm_id: int,
        dungeon_id: int,
        period_id: int,
    ) -> dict | None:
        """Fetch the top leaderboard for one (realm, dungeon, period).

        Response shape (trimmed, actual fields pulled in caller):
            {
              "leading_groups": [
                {
                  "ranking": 1,
                  "keystone_level": 22,
                  "duration": 1_200_000,
                  "completed_timestamp": ...,
                  "members": [
                    { "profile": {"name", "id", "realm": {"slug", ...}},
                      "specialization": {"id", "name"} },
                    ... (x5)
                  ]
                },
                ... (up to 500)
              ]
            }
        """
        path = (
            f"/data/wow/connected-realm/{connected_realm_id}"
            f"/mythic-leaderboard/{dungeon_id}/period/{period_id}"
        )
        return self._game_data_get(region, path)


bnet_client = BnetClient()
