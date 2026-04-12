import time
import logging

import httpx
from app.config import settings
from app.wcl.auth import wcl_auth

logger = logging.getLogger(__name__)


class WCLClient:
    """Sync GraphQL client for Warcraft Logs API v2 with retry on rate limit."""

    def query(self, graphql: str, variables: dict | None = None) -> dict:
        token = wcl_auth.get_token()
        max_retries = 5

        for attempt in range(max_retries):
            with httpx.Client() as client:
                resp = client.post(
                    settings.wcl_api_url,
                    json={"query": graphql, "variables": variables or {}},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

            if resp.status_code == 429:
                wait = 15 * (attempt + 1)  # 15, 30, 45, 60, 75s
                logger.warning("WCL rate limited, waiting %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                raise WCLQueryError(data["errors"])
            return data["data"]

        # Final attempt failed
        resp.raise_for_status()
        return {}

    def get_character_with_reports(
        self, name: str, server_slug: str, server_region: str, limit: int = 10
    ) -> dict | None:
        from app.wcl.queries import CHARACTER_RECENT_REPORTS

        data = self.query(
            CHARACTER_RECENT_REPORTS,
            {
                "name": name,
                "serverSlug": server_slug,
                "serverRegion": server_region,
                "limit": limit,
            },
        )
        return data.get("characterData", {}).get("character")

    def get_report_fights(self, report_code: str) -> list[dict]:
        from app.wcl.queries import REPORT_FIGHTS

        data = self.query(REPORT_FIGHTS, {"code": report_code})
        report = data.get("reportData", {}).get("report")
        if not report:
            return []
        return report.get("fights", [])

    def get_report_player_data(
        self, report_code: str, fight_ids: list[int]
    ) -> dict | None:
        from app.wcl.queries import REPORT_PLAYER_DATA

        data = self.query(
            REPORT_PLAYER_DATA,
            {"code": report_code, "fightIDs": fight_ids},
        )
        return data.get("reportData", {}).get("report")

    def get_player_buffs(
        self, report_code: str, fight_ids: list[int], source_id: int
    ) -> dict:
        from app.wcl.queries import REPORT_PLAYER_BUFFS

        data = self.query(
            REPORT_PLAYER_BUFFS,
            {"code": report_code, "fightIDs": fight_ids, "sourceID": source_id},
        )
        report = data.get("reportData", {}).get("report", {})
        return report.get("buffsTable", {})

    def get_encounter_percentiles(
        self,
        name: str,
        server_slug: str,
        server_region: str,
        encounter_ids: list[int],
        metric: str = "dps",
    ) -> dict[int, list[dict]]:
        """Batch-fetch WCL percentile rankings for multiple encounters.

        Returns a dict mapping encounter_id -> list of rank entries.
        Each rank entry has rankPercent, report.code, report.fightID, spec, etc.
        """
        if not encounter_ids:
            return {}

        # Build aliased query fields for each encounter
        fields = []
        for eid in encounter_ids:
            fields.append(
                f"e{eid}: encounterRankings(encounterID: {eid}, difficulty: 10, metric: {metric})"
            )

        query = (
            "query($name: String!, $serverSlug: String!, $serverRegion: String!) {\n"
            "  characterData {\n"
            "    character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {\n"
            "      " + "\n      ".join(fields) + "\n"
            "    }\n"
            "  }\n"
            "}"
        )

        data = self.query(
            query,
            {
                "name": name,
                "serverSlug": server_slug,
                "serverRegion": server_region,
            },
        )

        char = data.get("characterData", {}).get("character", {})
        result: dict[int, list[dict]] = {}
        for eid in encounter_ids:
            ranking = char.get(f"e{eid}", {})
            result[eid] = ranking.get("ranks", [])

        return result


    def get_zone_rankings(
        self,
        name: str,
        server_slug: str,
        server_region: str,
        zone_id: int = 47,
    ) -> dict:
        """Fetch zoneRankings for a character — both overall and by ilvl bracket.

        Returns dict with 'overall' and 'by_ilvl' keys, each containing
        per-dungeon best percentile and kill counts.
        """
        query = """
        query($name: String!, $serverSlug: String!, $serverRegion: String!) {
          characterData {
            character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
              overall: zoneRankings(zoneID: %d)
              byIlvl: zoneRankings(zoneID: %d, byBracket: true)
            }
          }
        }
        """ % (zone_id, zone_id)

        data = self.query(
            query,
            {
                "name": name,
                "serverSlug": server_slug,
                "serverRegion": server_region,
            },
        )
        char = data.get("characterData", {}).get("character", {})
        return {
            "overall": char.get("overall", {}),
            "by_ilvl": char.get("byIlvl", {}),
        }


class WCLQueryError(Exception):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__(f"WCL GraphQL errors: {'; '.join(messages)}")


wcl_client = WCLClient()
