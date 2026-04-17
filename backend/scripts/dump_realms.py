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
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

REGIONS = ["us", "eu", "kr", "tw"]
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
        if r.get("slug") and r.get("name")
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
