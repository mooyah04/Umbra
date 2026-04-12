"""Ingestion pipeline: fetch from WCL → score → store in DB."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DungeonRun, Player, PlayerScore, Role
from app.scoring.engine import score_player_runs
from app.scoring.roles import get_role
from app.wcl.client import wcl_client, WCLQueryError

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    player: Player | None
    groupmates: list[dict] = field(default_factory=list)  # [{name, realm, region}, ...]


def _slug_to_realm(slug: str) -> str:
    """Convert a WCL server slug to WoW realm format.

    'tarren-mill' -> 'TarrenMill'
    'altar-of-storms' -> 'AltarofStorms'
    """
    return "".join(word.capitalize() for word in slug.split("-"))


def _find_player_in_details(player_details: dict, character_name: str) -> dict | None:
    """Find a specific player in the playerDetails response."""
    details = player_details.get("data", {}).get("playerDetails", {})
    for role_group in ("dps", "tanks", "healers"):
        for player in details.get(role_group, []):
            if player.get("name", "").lower() == character_name.lower():
                return {**player, "_role_group": role_group}
    return None


def _get_player_stat(table_data: dict, player_name: str) -> float:
    """Get a player's total from a flat table (DamageDone, Healing, DamageTaken)."""
    entries = table_data.get("data", {}).get("entries", [])
    for entry in entries:
        if entry.get("name", "").lower() == player_name.lower():
            return entry.get("total", 0)
    return 0


def _get_nested_stat(table_data: dict, player_name: str) -> int:
    """Get a player's total from a nested table (Interrupts, Dispels).

    Structure: entries[0].entries[spell].details[player].total
    """
    total = 0
    for top_entry in table_data.get("data", {}).get("entries", []):
        for spell_entry in top_entry.get("entries", []):
            for player in spell_entry.get("details", []):
                if player.get("name", "").lower() == player_name.lower():
                    total += player.get("total", 0)
    return total


def _count_deaths(table_data: dict, player_name: str) -> int:
    """Count deaths for a player. Each entry in Deaths table is one death event."""
    entries = table_data.get("data", {}).get("entries", [])
    return sum(1 for e in entries if e.get("name", "").lower() == player_name.lower())


def _is_player_in_fight(player_details: dict, character_name: str) -> bool:
    """Check if a player participated in a fight based on playerDetails."""
    return _find_player_in_details(player_details, character_name) is not None


def _extract_groupmates(player_details: dict, exclude_name: str, region: str) -> list[dict]:
    """Extract all players from a fight's playerDetails, excluding the target player.

    Returns list of {name, realm, region} dicts for each groupmate.
    """
    groupmates = []
    details = player_details.get("data", {}).get("playerDetails", {})
    for role_group in ("dps", "tanks", "healers"):
        for player in details.get(role_group, []):
            pname = player.get("name", "")
            if not pname or pname.lower() == exclude_name.lower():
                continue
            server = player.get("server", "")
            player_region = player.get("region", region)
            if server and pname:
                groupmates.append({
                    "name": pname,
                    "realm": server,
                    "region": player_region.upper() if player_region else region.upper(),
                })
    return groupmates


def ingest_player(
    session: Session,
    name: str,
    realm: str,
    region: str,
) -> IngestResult:
    """Fetch a player's M+ data from WCL, score it, and store results.

    Returns an IngestResult containing the Player and any discovered groupmates.
    """
    server_slug = realm.lower().replace("'", "").replace(" ", "-")

    # 1. Fetch character + recent reports
    char_data = wcl_client.get_character_with_reports(
        name=name,
        server_slug=server_slug,
        server_region=region.lower(),
        limit=settings.max_reports_to_fetch,
    )
    if not char_data:
        logger.warning("Character not found on WCL: %s-%s (%s)", name, realm, region)
        return IngestResult(player=None)

    class_id = char_data["classID"]
    wcl_id = char_data["id"]
    wow_realm = _slug_to_realm(char_data.get("server", {}).get("slug", server_slug))

    # 2. Upsert player record
    stmt = select(Player).where(Player.wcl_id == wcl_id)
    result = session.execute(stmt)
    player = result.scalar_one_or_none()

    if player is None:
        player = Player(
            name=name, realm=wow_realm, region=region.upper(),
            class_id=class_id, wcl_id=wcl_id,
        )
        session.add(player)
        session.flush()
    else:
        player.name = name
        player.realm = wow_realm
        player.region = region.upper()

    # 3. Process each report — extract per-fight data (rolling window of last N runs)
    reports = char_data.get("recentReports", {}).get("data", [])
    # Sort newest first to ensure rolling window uses most recent runs
    reports.sort(key=lambda r: r.get("startTime", 0), reverse=True)

    # Build set of existing runs to avoid duplicates (keep historical data)
    existing_stmt = select(DungeonRun).where(DungeonRun.player_id == player.id)
    existing_runs = {
        (r.wcl_report_id, r.fight_id)
        for r in session.execute(existing_stmt).scalars()
    }

    runs: list[DungeonRun] = []
    discovered_groupmates: list[dict] = []
    seen_groupmates: set[str] = set()

    for report in reports:
        report_code = report["code"]
        zone = report.get("zone", {})
        zone_name = zone.get("name", "")

        if "mythic+" not in zone_name.lower():
            continue

        # Get M+ fights from this report
        try:
            fights = wcl_client.get_report_fights(report_code)
        except WCLQueryError as e:
            logger.debug("Skipping report %s: %s", report_code, e)
            continue
        if not fights:
            continue

        # Process each fight individually
        for fight in fights:
            fight_id = fight["id"]

            try:
                report_data = wcl_client.get_report_player_data(report_code, [fight_id])
            except WCLQueryError as e:
                logger.debug("Skipping fight %s/%d: %s", report_code, fight_id, e)
                continue
            if not report_data:
                continue

            player_details = report_data.get("playerDetails", {})

            # Only process fights where our player participated
            player_info = _find_player_in_details(player_details, name)
            if not player_info:
                continue

            # Discover groupmates from this fight
            for gm in _extract_groupmates(player_details, name, region):
                gm_key = f"{gm['name']}-{gm['realm']}".lower()
                if gm_key not in seen_groupmates:
                    seen_groupmates.add(gm_key)
                    discovered_groupmates.append(gm)

            # Determine role from WCL's grouping
            role_group = player_info.get("_role_group", "dps")
            if role_group == "tanks":
                role = Role.tank
            elif role_group == "healers":
                role = Role.healer
            else:
                role = Role.dps

            specs = player_info.get("specs", [])
            spec_name = specs[0]["spec"] if specs else "Unknown"
            ilvl = player_info.get("maxItemLevel", 0)

            # Extract per-fight stats
            damage_table = report_data.get("damageTable", {})
            healing_table = report_data.get("healingTable", {})
            damage_taken_table = report_data.get("damageTakenTable", {})
            interrupt_table = report_data.get("interruptTable", {})
            dispel_table = report_data.get("dispelTable", {})
            death_table = report_data.get("deathTable", {})

            dps_total = _get_player_stat(damage_table, name)
            hps_total = _get_player_stat(healing_table, name)
            damage_taken = _get_player_stat(damage_taken_table, name)
            interrupts = _get_nested_stat(interrupt_table, name)
            dispels = _get_nested_stat(dispel_table, name)
            deaths = _count_deaths(death_table, name)

            duration_ms = fight.get("endTime", 0) - fight.get("startTime", 0)

            # Skip if we already have this run (preserve historical data)
            if (report_code, fight_id) in existing_runs:
                continue

            run = DungeonRun(
                player_id=player.id,
                encounter_id=fight.get("encounterID", 0),
                keystone_level=fight.get("keystoneLevel", 0),
                role=role,
                spec_name=spec_name,
                dps=dps_total,
                hps=hps_total,
                ilvl=ilvl,
                duration=duration_ms,
                deaths=deaths,
                interrupts=interrupts,
                dispels=dispels,
                avoidable_damage_taken=0,  # Not available from WCL directly
                damage_taken_total=damage_taken,
                wcl_report_id=report_code,
                fight_id=fight_id,
                timed=fight.get("kill", False),
                logged_at=datetime.fromtimestamp(
                    report.get("startTime", 0) / 1000
                ),
            )
            session.add(run)
            runs.append(run)

        # Stop if we have enough runs
        if len(runs) >= settings.max_runs_to_analyze:
            break

    # 4. Fetch zone rankings for DPS percentile (available even for archived reports)
    #    This gives best-parse percentile per dungeon across the full season
    zone_dps_percentile = None
    zone_total_kills = 0
    try:
        zone_rankings = wcl_client.get_zone_rankings(
            name=name,
            server_slug=server_slug,
            server_region=region.lower(),
            zone_id=47,  # Current M+ season
        )

        # Collect best percentile per dungeon and total kills
        dungeon_percentiles = []
        for dungeon in zone_rankings.get("rankings", []):
            best_pct = dungeon.get("rankPercent")
            kills = dungeon.get("totalKills", 0)
            zone_total_kills += kills
            if best_pct is not None and kills > 0:
                dungeon_percentiles.append(best_pct)

        if dungeon_percentiles:
            zone_dps_percentile = sum(dungeon_percentiles) / len(dungeon_percentiles)
            logger.info(
                "Zone rankings: %.1f%% avg across %d dungeons (%d total kills)",
                zone_dps_percentile, len(dungeon_percentiles), zone_total_kills,
            )
    except WCLQueryError as e:
        logger.warning("Failed to fetch zone rankings: %s", e)

    # Also attach per-fight percentiles to runs where available
    encounter_ids = list({r.encounter_id for r in runs})
    if encounter_ids:
        try:
            percentiles = wcl_client.get_encounter_percentiles(
                name=name,
                server_slug=server_slug,
                server_region=region.lower(),
                encounter_ids=encounter_ids,
                metric="dps",
            )

            pct_lookup: dict[tuple[str, int], float] = {}
            for eid, ranks in percentiles.items():
                for rank in ranks:
                    report_code_r = rank.get("report", {}).get("code", "")
                    fight_id_r = rank.get("report", {}).get("fightID", 0)
                    pct_lookup[(report_code_r, fight_id_r)] = rank.get("rankPercent", 0)

            for run in runs:
                pct = pct_lookup.get((run.wcl_report_id, run.fight_id))
                if pct is not None:
                    run.dps = pct

            # HPS percentiles for healers
            healer_runs = [r for r in runs if r.role == Role.healer]
            if healer_runs:
                hps_percentiles = wcl_client.get_encounter_percentiles(
                    name=name,
                    server_slug=server_slug,
                    server_region=region.lower(),
                    encounter_ids=list({r.encounter_id for r in healer_runs}),
                    metric="hps",
                )
                hps_lookup: dict[tuple[str, int], float] = {}
                for eid, ranks in hps_percentiles.items():
                    for rank in ranks:
                        report_code_r = rank.get("report", {}).get("code", "")
                        fight_id_r = rank.get("report", {}).get("fightID", 0)
                        hps_lookup[(report_code_r, fight_id_r)] = rank.get("rankPercent", 0)

                for run in healer_runs:
                    pct = hps_lookup.get((run.wcl_report_id, run.fight_id))
                    if pct is not None:
                        run.hps = pct
        except WCLQueryError as e:
            logger.warning("Failed to fetch encounter percentiles: %s", e)

    # 5. Score using rolling window of most recent runs from ALL stored history
    all_runs_stmt = (
        select(DungeonRun)
        .where(DungeonRun.player_id == player.id)
        .order_by(DungeonRun.logged_at.desc())
    )
    all_runs = list(session.execute(all_runs_stmt).scalars())

    # Take the most recent N runs for scoring (rolling window)
    recent_runs = all_runs[:settings.max_runs_to_analyze]

    runs_by_role: dict[Role, list[DungeonRun]] = defaultdict(list)
    for run in recent_runs:
        runs_by_role[run.role].append(run)

    primary_role = max(runs_by_role, key=lambda r: len(runs_by_role[r])) if runs_by_role else Role.dps

    # Clear old scores
    old_scores_stmt = select(PlayerScore).where(PlayerScore.player_id == player.id)
    for old_score in session.execute(old_scores_stmt).scalars():
        session.delete(old_score)

    for role, role_runs in runs_by_role.items():
        if len(role_runs) < settings.min_runs_for_grade:
            continue

        result = score_player_runs(role_runs, role, zone_dps_percentile)

        # Total runs = all stored history (for the website), not just the scoring window
        total_runs = max(len(all_runs), zone_total_kills)

        score = PlayerScore(
            player_id=player.id,
            role=role,
            overall_grade=result.overall_grade,
            category_scores=result.category_scores,
            runs_analyzed=total_runs,
            primary_role=(role == primary_role),
        )
        session.add(score)

    session.commit()
    logger.info(
        "Ingested %s-%s: %d new runs, %d total stored, scored on %d most recent, %d role(s), %d groupmates discovered",
        name, realm, len(runs), len(all_runs), len(recent_runs), len(runs_by_role), len(discovered_groupmates),
    )
    return IngestResult(player=player, groupmates=discovered_groupmates)


def ingest_batch(
    session: Session,
    players: list[dict],
) -> list[IngestResult]:
    """Ingest a batch of players sequentially."""
    results: list[IngestResult] = []
    for p in players:
        result = ingest_player(session, p["name"], p["realm"], p["region"])
        if result.player:
            results.append(result)
    return results
