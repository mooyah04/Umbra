"""One-off: dump all WoW realms per region to frontend/public/realms.json.

Run once (or whenever Blizzard adds/renames a realm — basically never).
Output is committed to the repo so the SearchBar's region -> server
dropdown has zero runtime dependency on Blizzard's API.

Usage:
    railway run python -m scripts.dump_realms       # uses Railway env
    python -m scripts.dump_realms                   # uses backend/.env

Output shape: {"us": [{"slug": "area-52", "name": "Area 52"}, ...], ...}
Realms sorted alphabetically by display name per region.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

REGIONS = ["us", "eu", "kr", "tw"]

# Blizzard's /data/wow/realm/index includes internal instance-server realms
# and data-build realms nobody plays on. Exclude them by name pattern so the
# frontend's server dropdown only shows realms players can actually create
# characters on.
_INSTANCE_RE = re.compile(r"-INST(?:-[A-Z]+)?$")
_RDB_RE = re.compile(r"^RDB[\s-]")
# Matches internal BG/Auxiliary/etc realms like "EU7A-BG-RU".
_INTERNAL_CODE_RE = re.compile(r"^(?:US|EU|KR|TW|CN)\d+[A-Z]-")

# Substrings that appear only in Blizzard's internal / non-player realms.
# Case-insensitive. Anchored-ish (case-sensitive 'Account Realm' etc helps
# avoid false positives on realms that just happen to contain the word).
_INTERNAL_MARKERS = (
    "Account Realm",
    "Auxiliary",
    "Arena Pass",
    "GMSupport",
)


def _is_player_realm(name: str) -> bool:
    if _INSTANCE_RE.search(name):
        return False
    if _RDB_RE.match(name):
        return False
    if _INTERNAL_CODE_RE.match(name):
        return False
    for marker in _INTERNAL_MARKERS:
        if marker in name:
            return False
    return True

# Repo-root relative. This script lives at backend/scripts/, so output is
# at ../../frontend/public/realms.json.
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "realms.json"


def _get_token(client: httpx.Client) -> str:
    resp = client.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(settings.bnet_client_id, settings.bnet_client_secret),
        timeout=15.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _fetch_realms(client: httpx.Client, token: str, region: str) -> list[dict]:
    host = f"https://{region}.api.blizzard.com"
    resp = client.get(
        f"{host}/data/wow/realm/index",
        params={"namespace": f"dynamic-{region}", "locale": "en_US"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15.0,
    )
    resp.raise_for_status()
    realms = resp.json().get("realms", [])
    # Keep just the name + slug; ids/links aren't needed for the dropdown.
    entries = [
        {"slug": r["slug"], "name": r["name"]}
        for r in realms
        if r.get("slug") and r.get("name") and _is_player_realm(r["name"])
    ]
    entries.sort(key=lambda r: r["name"].casefold())
    return entries


def main() -> int:
    if not settings.bnet_client_id or not settings.bnet_client_secret:
        logger.error("BNET_CLIENT_ID / BNET_CLIENT_SECRET not set")
        return 1

    result: dict[str, list[dict]] = {}
    with httpx.Client() as client:
        token = _get_token(client)
        logger.info("got bnet token")
        for region in REGIONS:
            realms = _fetch_realms(client, token, region)
            logger.info("region=%s realms=%d", region, len(realms))
            result[region] = realms

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("wrote %s (%d regions, %d realms total)",
                OUTPUT_PATH, len(result), sum(len(v) for v in result.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
