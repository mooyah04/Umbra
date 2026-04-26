"""Simulate the byBracket=true scoring impact for Elonmunk.

Pulls his current run data from prod API, fetches per-fight bracketed
percentiles fresh from WCL, runs the scoring engine on both versions,
and prints the before/after grade.

Read-only — does not write to any DB.
"""

import asyncio
from copy import deepcopy
from dataclasses import dataclass
import httpx

from app.models import Role
from app.scoring.engine import score_player_runs
from app.wcl.client import WCLClient

PROD_API = "https://api.wowumbra.gg"
NAME, REALM, REGION = "Elonmunk", "tarrenmill", "eu"
SERVER_SLUG, SERVER_REGION = "tarren-mill", "eu"


# Minimal stand-in for DungeonRun that the scorer reads from. The
# scorer accesses attributes by name, not by ORM lookups, so a plain
# object with the same field names is enough — avoids needing a live
# DB. Add fields here if the scorer ever reaches for new ones.
@dataclass
class FakeRun:
    encounter_id: int
    keystone_level: int
    role: Role
    spec_name: str
    dps: float
    hps: float
    deaths: int
    interrupts: int
    dispels: int
    avoidable_damage_taken: float
    damage_taken_total: float
    casts_total: int
    cooldown_usage_pct: float
    timed: bool
    duration: int
    avoidable_deaths: int | None = None
    cc_casts: int | None = None
    critical_interrupts: int | None = None
    healing_received: float | None = None
    aug_uplift_damage: float | None = None
    wcl_report_id: str = ""
    fight_id: int = 0


async def main():
    async with httpx.AsyncClient(timeout=30) as http:
        runs_resp = await http.get(f"{PROD_API}/api/player/{REGION}/{REALM}/{NAME}/runs?limit=100")
        runs_resp.raise_for_status()
        run_summaries = runs_resp.json().get("runs", [])

        # The /runs list endpoint doesn't include all fields the scorer
        # needs (avoidable_damage_taken, etc), so fetch each run detail.
        # Slow but it's only ~17 calls.
        full_runs = []
        for s in run_summaries:
            r = await http.get(f"{PROD_API}/api/player/{REGION}/{REALM}/{NAME}/runs/{s['id']}")
            r.raise_for_status()
            full_runs.append(r.json())

    role = Role.tank
    fake_global = []
    for r in full_runs:
        fake_global.append(
            FakeRun(
                encounter_id=r["encounter_id"],
                keystone_level=r["keystone_level"],
                role=role,
                spec_name=r["spec_name"],
                dps=r["dps"],
                hps=r["hps"],
                deaths=r["deaths"],
                interrupts=r["interrupts"],
                dispels=r["dispels"],
                avoidable_damage_taken=r["avoidable_damage_taken"],
                damage_taken_total=r["damage_taken_total"],
                casts_total=r["casts_total"],
                cooldown_usage_pct=r["cooldown_usage_pct"],
                timed=r["timed"],
                duration=r["duration"],
                avoidable_deaths=r.get("avoidable_deaths"),
                cc_casts=r.get("cc_casts"),
                critical_interrupts=r.get("critical_interrupts"),
                healing_received=r.get("healing_received"),
                wcl_report_id=r["wcl_report_id"],
                fight_id=r["fight_id"],
            )
        )

    # Fetch bracketed percentiles
    client = WCLClient()
    encounter_ids = list({r.encounter_id for r in fake_global})
    percentiles = client.get_encounter_percentiles(
        name=NAME, server_slug=SERVER_SLUG, server_region=SERVER_REGION,
        encounter_ids=encounter_ids, metric="dps",
    )
    bb_lookup: dict[tuple[str, int], float] = {}
    for eid, ranks in percentiles.items():
        for rank in ranks:
            key = (rank["report"]["code"], rank["report"]["fightID"])
            bb_lookup[key] = rank.get("rankPercent", 0)

    # Apply bracketed values to a copy
    fake_bracket = [deepcopy(r) for r in fake_global]
    swapped = 0
    for r in fake_bracket:
        new = bb_lookup.get((r.wcl_report_id, r.fight_id))
        if new is not None:
            r.dps = new
            swapped += 1

    print(f"Swapped {swapped}/{len(fake_bracket)} runs to bracketed percentiles\n")

    # Per-run scoring is what shows on the /run/{id} page. The role-level
    # composite uses zone_dps_percentile (a separate WCL endpoint we
    # didn't change in phase 1), so per-run movement is what's visible
    # to users post-deploy.
    print(f"{'Run id':<8} {'Report':<10} {'Key':<4} {'D.O. before':<12} {'D.O. after':<11} {'Δ':<7} {'Run grade'}")
    print("-" * 72)
    for g, b in zip(fake_global, fake_bracket):
        before_r = score_player_runs([g], role, zone_dps_percentile=None, class_id=10)
        after_r  = score_player_runs([b], role, zone_dps_percentile=None, class_id=10)
        bd = before_r.category_scores.get("damage_output", 0)
        ad = after_r.category_scores.get("damage_output", 0)
        bg = before_r.overall_grade
        ag = after_r.overall_grade
        marker = " <- big move" if abs(ad - bd) >= 30 else ""
        print(f"f{g.fight_id:<7} {g.wcl_report_id[:8]:<10} +{g.keystone_level:<3} {bd:<12.1f} {ad:<11.1f} {ad-bd:>+6.1f} {bg} -> {ag}{marker}")


if __name__ == "__main__":
    asyncio.run(main())
