"""Ingestion pipeline: fetch from WCL → score → store in DB."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DungeonRun, Player, PlayerScore, Role
from app.scoring.avoidable import get_avoidable_abilities
from app.scoring.cc_abilities import get_cc_ability_ids
from app.scoring.cooldowns import get_cooldowns_for_spec
from app.scoring.engine import score_player_runs
from app.scoring.interrupts import get_critical_interrupt_ids
from app.scoring.roles import get_role
from app.scoring.spec_to_class import class_id_from_name, resolve_class_id
from app.bnet.client import bnet_client
from app.wcl.client import wcl_client, WCLQueryError

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    player: Player | None
    groupmates: list[dict] = field(default_factory=list)  # [{name, realm, region}, ...]
    # Reason populated when player is None, for caller-side diagnostics.
    # Known values: "wcl_not_found", "no_reports", "no_fights".
    reason: str | None = None


def _maybe_fetch_bnet_media(player, server_slug: str, character_name: str) -> None:
    """Populate player.avatar_url / inset_url / render_url from Blizzard API.

    No-op when:
      - BNET creds aren't configured (bnet_client.get_character_media returns None)
      - Media was fetched within the last 7 days
      - Blizzard returns 404 (hidden character) — the row just keeps nulls
    """
    from datetime import timedelta
    if player.media_fetched_at is not None:
        age = datetime.utcnow() - player.media_fetched_at
        if age < timedelta(days=7):
            return
    media = bnet_client.get_character_media(
        region=player.region,
        realm_slug=server_slug,
        character_name=character_name,
    )
    # Always update the timestamp so we don't hammer Bnet on every
    # ingest for characters with hidden profiles.
    player.media_fetched_at = datetime.utcnow()
    if not media:
        return
    if "avatar" in media:
        player.avatar_url = media["avatar"]
    if "inset" in media:
        player.inset_url = media["inset"]
    if "render" in media:
        player.render_url = media["render"]


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


def _get_healing_received(healing_table: dict, player_name: str) -> float:
    """Sum healing received by a player across all healers.

    The Healing table entries are grouped by source (healer). Each entry
    may have a targets[] sub-array. If targets exist, sum those matching
    our player. Otherwise fall back to the healingReceivedTable (viewBy: Target).
    """
    total = 0.0
    entries = healing_table.get("data", {}).get("entries", [])
    for healer_entry in entries:
        targets = healer_entry.get("targets", [])
        if targets:
            for target in targets:
                if target.get("name", "").lower() == player_name.lower():
                    total += target.get("total", 0)
        elif healer_entry.get("name", "").lower() == player_name.lower():
            # Fallback: if this is a target-grouped table, entries ARE players
            total += healer_entry.get("total", 0)
    return total


def _count_avoidable_deaths(
    death_table: dict, player_name: str, avoidable_ids: set[int]
) -> int:
    """Count deaths caused by avoidable abilities.

    The Deaths table returns killingAbility.guid per death event.
    Cross-reference against known avoidable ability IDs.
    """
    entries = death_table.get("data", {}).get("entries", [])
    count = 0
    for e in entries:
        if e.get("name", "").lower() != player_name.lower():
            continue
        killing = e.get("damage", {}).get("entries", [{}])
        # Check if the killing blow was from an avoidable ability
        killing_ability = e.get("killingAbility", {})
        if killing_ability and killing_ability.get("guid", 0) in avoidable_ids:
            count += 1
    return count


def _count_critical_interrupts(
    interrupt_table: dict, player_name: str, critical_ids: set[int]
) -> int:
    """Count interrupts of high-priority spells.

    Actual WCL Interrupts table shape (verified 2026-04-16 against a live
    Magister's Terrace log): the top-level entries[] contains ONE wrapper
    with no guid of its own; the kicked-ability rows are inside
    wrapper.entries[]. Each ability row has `guid` (the spell that was
    kicked) and `details[]` (one per player who kicked it, with `total`).

    Previous implementation read `guid` from the wrapper and always got 0,
    so critical_interrupts silently returned 0 regardless of input. Fixed
    to descend one level.
    """
    if not critical_ids:
        return 0
    total = 0
    for wrapper in interrupt_table.get("data", {}).get("entries", []):
        for ability_entry in wrapper.get("entries", []):
            interrupted_id = ability_entry.get("guid", 0)
            if interrupted_id not in critical_ids:
                continue
            for player in ability_entry.get("details", []):
                if player.get("name", "").lower() == player_name.lower():
                    total += player.get("total", 0)
    return total


def _count_cc_casts(debuffs_table: dict, cc_ids: set[int]) -> int:
    """Count CC applications to enemies from the Debuffs table.

    NOTE: Kept for backwards compat. Pet/totem-sourced CCs (Capacitor Totem,
    Water Elemental Freeze, Hunter traps) are sourced from pet actors, not
    the player, so the sourceID-filtered debuffs table misses them. Prefer
    _count_cc_casts_from_casts_table for accurate cross-class counting.
    """
    total = 0
    for aura in debuffs_table.get("data", {}).get("auras", []):
        if aura.get("guid", 0) in cc_ids:
            total += aura.get("totalUses", 0)
    return total


def _count_cc_casts_from_casts_table(
    casts_table: dict, player_name: str, cc_cast_ids: set[int]
) -> int:
    """Count CC spells the player actually cast, regardless of whether the
    resulting debuff is sourced from the player or a pet/totem.

    WCL's Casts table returns entries[player] with an abilities[] breakdown
    keyed by cast guid. Counting casts of known CC triggers (Capacitor Totem
    summon, Freezing Trap placement, Paralysis, etc.) captures player intent
    without needing to cross-reference pet actor IDs.
    """
    if not cc_cast_ids:
        return 0
    total = 0
    for entry in casts_table.get("data", {}).get("entries", []):
        if entry.get("name", "").lower() != player_name.lower():
            continue
        for ability in entry.get("abilities", []):
            if ability.get("guid", 0) in cc_cast_ids:
                total += ability.get("total", 0)
        return total
    return 0


def _get_total_casts(table_data: dict, player_name: str) -> int:
    """Get total number of casts for a player from the Casts table."""
    entries = table_data.get("data", {}).get("entries", [])
    for entry in entries:
        if entry.get("name", "").lower() == player_name.lower():
            return entry.get("total", 0)
    return 0


def _get_cooldown_usage(
    buffs_table: dict,
    cooldowns: list[tuple[int, str, float]],
    duration_ms: int,
) -> float:
    """Score cooldown usage based on frequency, not just presence.

    Each cooldown has an expected_uptime_pct (from cooldowns.py). We estimate
    how many uses to expect from the fight duration, then score actual vs expected.

    For example, Combustion (12% expected uptime, ~2min CD) in a 30-min key:
    expected_uses = (30 * 0.12) / (12/100 * 2) ≈ 15 uses. Using it once = 7%.

    Simplified: expected_uses = max(1, duration_min * expected_uptime_pct / 100)
    This works because uptime_pct roughly equals (buff_duration / cd_total_cycle).

    Returns 0-100.

    WCL buffs table structure (when filtered by sourceID):
      data.auras[] -> [{guid, name, totalUses, totalUptime, bands}, ...]
    """
    if not cooldowns:
        return 100  # No cooldowns expected = full marks

    duration_min = max(1, duration_ms / 60000)
    auras = buffs_table.get("data", {}).get("auras", [])

    # Build lookup: buff_id -> totalUses
    aura_uses: dict[int, int] = {}
    for aura in auras:
        aura_id = aura.get("guid", 0)
        aura_uses[aura_id] = aura.get("totalUses", 0)

    cd_scores: list[float] = []
    for buff_id, _name, expected_uptime_pct in cooldowns:
        actual_uses = aura_uses.get(buff_id, 0)

        # Expected uses = max of:
        #   a) duration_min * uptime_pct / 100 — the uptime-based formula
        #      (works well for high-uptime CDs like Shield Block)
        #   b) duration_min / 5 — a "1 press per 5 min of fight" floor
        #      so a single Tranquility use in a 20-min key doesn't score
        #      100%. Prior `max(1, ...)` floor made long fights trivial
        #      to satisfy — Dobbermon's cooldown_usage was flat 100.0
        #      across every run because each 3-min-CD major was hitting
        #      expected=1 and any single use saturated it.
        baseline = duration_min * expected_uptime_pct / 100
        floor = max(1.0, duration_min / 5.0)
        expected_uses = max(baseline, floor)

        # Score this CD: cap at 100% (using it more than expected is fine)
        cd_scores.append(min(100, (actual_uses / expected_uses) * 100))

    return sum(cd_scores) / len(cd_scores) if cd_scores else 100


# Minimum keystone level at which we build a per-run pull breakdown.
# Below this, ingest cost isn't worth it — +5 keys aren't interesting
# and the breakdown wouldn't be actionable.
_BREAKDOWN_MIN_KEYSTONE = 8


def _build_pulls(
    *,
    actor_id: int | None,
    report_code: str,
    fight_id: int,
    fight_start_ms: int,
    avoidable_ids: set[int],
    critical_interrupt_ids: set[int],
    keystone_level: int,
) -> list[dict] | None:
    """Build the Level B v2 pull-by-pull breakdown for one run.

    Uses WCL's authoritative `fight.dungeonPulls` as the source of truth
    for pull boundaries + names, then attaches per-player events
    (damage taken, critical interrupts, deaths) to whichever pull's
    time range contains each event. Per-pull verdict (clean / took_hits
    / wipe) derived from the attached events.

    Returns None for sub-threshold keys or when actor_id isn't resolvable.
    WCL fetch failures degrade gracefully — returning [] rather than
    tanking the whole ingest.
    """
    if keystone_level < _BREAKDOWN_MIN_KEYSTONE:
        return None
    if actor_id is None:
        return None

    # ── masterData for ability-name lookup on events ────────────────────
    ability_name_by_id: dict[int, str] = {}
    try:
        md = wcl_client.get_report_master_data(report_code) or {}
        for ab in (md.get("abilities") or []):
            gid = ab.get("gameID")
            if isinstance(gid, int):
                ability_name_by_id[gid] = ab.get("name") or "Unknown"
    except Exception as e:
        logger.debug("Pulls: masterData lookup failed for %s: %s",
                     report_code, e)

    # ── WCL's authoritative pull data ───────────────────────────────────
    # Each entry: {id, name, startTime, endTime, kill, enemyNPCs[]}
    # startTime/endTime are absolute log timestamps (ms).
    wcl_pulls = wcl_client.get_fight_dungeon_pulls(report_code, fight_id)
    if not wcl_pulls:
        return []

    pulls: list[dict] = []
    for i, wp in enumerate(wcl_pulls, start=1):
        start_ts = wp.get("startTime")
        end_ts = wp.get("endTime")
        if not isinstance(start_ts, (int, float)) or not isinstance(end_ts, (int, float)):
            continue
        start_t = (start_ts - fight_start_ms) / 1000.0
        end_t = (end_ts - fight_start_ms) / 1000.0
        # Mob count from enemyNPCs[].{min,max}InstanceID ranges.
        total_mobs = 0
        for npc in (wp.get("enemyNPCs") or []):
            lo = npc.get("minimumInstanceID") or 0
            hi = npc.get("maximumInstanceID") or 0
            total_mobs += max(0, hi - lo + 1)
        # Label: kill=True marks a boss pull. Use WCL's name directly
        # (it's the notable enemy's name, e.g. "Arcanotron Custos").
        # Non-boss pulls read as generic "Trash (N mobs)" per our
        # editorial choice, even though WCL supplies a name for them.
        if wp.get("kill"):
            label = wp.get("name") or "Boss"
        else:
            label = f"Trash ({total_mobs} mobs)" if total_mobs > 0 else "Trash"
        pulls.append({
            "i": i,
            "start_t": round(start_t, 1),
            "end_t": round(end_t, 1),
            "label": label,
            "verdict": "clean",
            "events": [],
        })

    if not pulls:
        return []

    # Player deaths still come from the Deaths events API (for timestamps).
    player_deaths: list[dict] = []
    try:
        death_events = wcl_client.get_player_events(
            report_code, [fight_id], data_type="Deaths",
        )
    except Exception as e:
        logger.debug("Pulls: death events failed for %s/%d: %s",
                     report_code, fight_id, e)
        death_events = []
    for ev in death_events:
        ts = ev.get("timestamp")
        target_id = ev.get("targetID")
        if not isinstance(ts, (int, float)) or target_id != actor_id:
            continue
        aid = ev.get("killingAbilityGameID") or ev.get("abilityGameID") or 0
        t_sec = (ts - fight_start_ms) / 1000.0
        player_deaths.append({
            "t": round(t_sec, 1),
            "ability_id": int(aid),
            "amount": int(ev.get("amount") or 0) or None,
        })

    def _assign_to_pull(t_sec: float) -> dict | None:
        for p in pulls:
            if p["start_t"] <= t_sec <= p["end_t"]:
                return p
        return None

    # ── Avoidable damage events (all of them, not top-N) ────────────────
    if avoidable_ids:
        try:
            raw = wcl_client.get_player_events(
                report_code, [fight_id], data_type="DamageTaken",
            )
        except Exception as e:
            logger.debug("Pulls: damage events failed for %s/%d: %s",
                         report_code, fight_id, e)
            raw = []
        for ev in raw:
            if ev.get("type") not in ("damage", "calculateddamage"):
                continue
            if ev.get("targetID") != actor_id:
                continue
            aid = ev.get("abilityGameID")
            if not isinstance(aid, int) or aid not in avoidable_ids:
                continue
            ts = ev.get("timestamp")
            if not isinstance(ts, (int, float)):
                continue
            t_sec = (ts - fight_start_ms) / 1000.0
            pull = _assign_to_pull(t_sec)
            if pull is None:
                continue
            amt = int(ev.get("amount") or 0) + int(ev.get("absorbed") or 0)
            pull["events"].append({
                "t": round(t_sec, 1),
                "type": "avoidable_damage",
                "ability_id": aid,
                "ability_name": ability_name_by_id.get(aid, "Unknown"),
                "amount": amt,
            })

    # ── Critical interrupts by this player ──────────────────────────────
    if critical_interrupt_ids:
        try:
            raw = wcl_client.get_player_events(
                report_code, [fight_id],
                data_type="Interrupts",
                source_id=actor_id,
            )
        except Exception as e:
            logger.debug("Pulls: interrupt events failed for %s/%d: %s",
                         report_code, fight_id, e)
            raw = []
        for ev in raw:
            kicked = ev.get("extraAbilityGameID")
            if not isinstance(kicked, int) or kicked not in critical_interrupt_ids:
                continue
            ts = ev.get("timestamp")
            if not isinstance(ts, (int, float)):
                continue
            t_sec = (ts - fight_start_ms) / 1000.0
            pull = _assign_to_pull(t_sec)
            if pull is None:
                continue
            pull["events"].append({
                "t": round(t_sec, 1),
                "type": "critical_interrupt",
                "ability_id": kicked,
                "ability_name": ability_name_by_id.get(kicked, "Unknown"),
                "amount": None,
            })

    # ── Player deaths → their containing pull ──────────────────────────
    for d in player_deaths:
        pull = _assign_to_pull(d["t"])
        if pull is None:
            continue
        pull["events"].append({
            "t": d["t"],
            "type": "death",
            "ability_id": d["ability_id"],
            "ability_name": ability_name_by_id.get(d["ability_id"], "Unknown"),
            "amount": d["amount"],
        })

    # ── Sort events per pull + compute verdict ──────────────────────────
    for p in pulls:
        p["events"].sort(key=lambda e: e["t"])
        has_death = any(e["type"] == "death" for e in p["events"])
        has_dmg = any(e["type"] == "avoidable_damage" for e in p["events"])
        if has_death:
            p["verdict"] = "wipe"
        elif has_dmg:
            p["verdict"] = "took_hits"
        # else stays "clean" from initialization

    return pulls


def _get_avoidable_damage(damage_taken_table: dict, player_name: str, avoidable_ids: set[int]) -> float:
    """Calculate total avoidable damage taken by a player.

    Cross-references the damage taken table with known avoidable ability IDs.
    """
    if not avoidable_ids:
        return 0

    entries = damage_taken_table.get("data", {}).get("entries", [])
    for entry in entries:
        if entry.get("name", "").lower() != player_name.lower():
            continue

        avoidable_total = 0
        for ability in entry.get("abilities", []):
            ability_id = ability.get("guid", 0)
            if ability_id in avoidable_ids:
                avoidable_total += ability.get("total", 0)
        return avoidable_total

    return 0


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


def _extract_party_comp(player_details: dict) -> list[dict]:
    """Snapshot all 5 party members for this fight.

    Returns [{name, realm, class, role, spec}, ...] ordered
    tank → healer → dps so the frontend renders them in that
    canonical layout without resorting. 'class' is WCL's type
    string; the frontend maps it to class_id for icon lookup.
    """
    party: list[dict] = []
    details = player_details.get("data", {}).get("playerDetails", {})
    role_label = {"tanks": "tank", "healers": "healer", "dps": "dps"}
    for role_group in ("tanks", "healers", "dps"):
        for player in details.get(role_group, []):
            name = player.get("name") or ""
            if not name:
                continue
            specs = player.get("specs") or []
            spec = None
            if specs and isinstance(specs[0], dict):
                spec = specs[0].get("spec")
            party.append({
                "name": name,
                "realm": player.get("server") or "",
                "class": player.get("type") or "",
                "role": role_label[role_group],
                "spec": spec,
            })
    return party


def ingest_player(
    session: Session,
    name: str,
    realm: str,
    region: str,
    class_hint: int | None = None,
    report_codes: list[str] | None = None,
) -> IngestResult:
    """Fetch a player's M+ data from WCL, score it, and store results.

    Two paths:

    1. Character-lookup mode (default). Call WCL's character(name, server,
       region) query, use whatever reports it returns. Works when WCL has
       a clean match for the name.

    2. Report-code mode (when report_codes is supplied). Skip the broken
       character lookup entirely and ingest directly from the given report
       codes. Required when WCL is matching the wrong character entity for
       common names — the only reliable way to score those players.
       class_hint is required in this mode.

    class_hint, when provided, overrides WCL's character.classID or provides
    class info for report-code mode. Caller supplies the authoritative class.

    Returns an IngestResult containing the Player and any discovered groupmates.
    """
    server_slug = realm.lower().replace("'", "").replace(" ", "-")

    # `effective_hint` = caller's hint, or (in char-lookup mode) the class_id
    # we resolved via Blizzard's character-profile API. Declared here so both
    # branches (report-code vs char-lookup) can share the downstream
    # "stamp player.class_id" logic.
    effective_hint = class_hint

    if report_codes:
        # Report-code mode: bypass the broken character() lookup.
        if class_hint is None:
            logger.warning(
                "Report-code mode for %s-%s requires class_hint; rejecting",
                name, realm,
            )
            return IngestResult(player=None, reason="class_hint_required")

        # Synthesize a reports list matching the shape of char_data.recentReports.
        # Use None for wcl_id — the character entity WCL has is wrong for
        # this player, so we can't key the Player row by it.
        # Fetch each report's startTime so fight timestamps are real
        # wall-clock values (not epoch+fight-offset). Cross-log dedup
        # depends on this.
        wcl_id = None
        class_id = class_hint
        wow_realm = _slug_to_realm(server_slug)
        reports = []
        for code in report_codes:
            try:
                header = wcl_client.get_report_header_and_fights(code)
                start_time = header.get("startTime", 0)
            except WCLQueryError as e:
                logger.warning("Could not fetch header for report %s: %s", code, e)
                start_time = 0
            reports.append({
                "code": code,
                "startTime": start_time,
                "zone": {"name": "Mythic+ Season 1"},
            })
        logger.info(
            "Ingesting %s-%s via %d report code(s), class_id=%d (hint)",
            name, realm, len(report_codes), class_id,
        )
        char_data = None  # sentinel; rest of function handles this case
    else:
        # Character-lookup mode.
        # FIRST, ask Blizzard for the canonical class. WCL's character()
        # returns a non-deterministic entity for name-colliding realms so
        # its classID is unreliable. Bnet is authoritative per (region,
        # realm, name) — if we can get a class_id there, promote it to
        # class_hint so the rest of the pipeline treats it as truth.
        # No-ops cleanly when Bnet creds aren't set or the profile is hidden.
        if effective_hint is None:
            from app.bnet.client import bnet_client
            profile = bnet_client.get_character_profile(
                region=region,
                realm_slug=server_slug,
                character_name=name,
            )
            if profile and profile.get("class_id"):
                effective_hint = profile["class_id"]
                logger.info(
                    "Bnet class-hint for %s-%s: class_id=%d (%s)",
                    name, realm, effective_hint, profile.get("class_name") or "?",
                )

        char_data = wcl_client.get_character_with_reports(
            name=name,
            server_slug=server_slug,
            server_region=region.lower(),
            limit=settings.max_reports_to_fetch,
        )
        if not char_data:
            logger.warning("Character not found on WCL: %s-%s (%s)", name, realm, region)
            return IngestResult(player=None, reason="wcl_not_found")

        wcl_class_id = char_data["classID"]
        class_id = effective_hint if effective_hint is not None else wcl_class_id
        if effective_hint is not None and effective_hint != wcl_class_id:
            logger.info(
                "Using class hint for %s-%s: hint said %d, WCL said %d",
                name, realm, effective_hint, wcl_class_id,
            )
        wcl_id = char_data["id"]
        wow_realm = _slug_to_realm(char_data.get("server", {}).get("slug", server_slug))
        reports = char_data.get("recentReports", {}).get("data", [])

    # 2. Upsert player record. The natural key for a character is
    # (name, realm_key, region) — wcl_id is a tracked attribute that can
    # legitimately change (WCL renames, collisions resolving differently
    # on later queries, etc). Matching on wcl_id first historically caused
    # duplicate rows: a later sweep that returned a different wcl_id
    # couldn't find the original row and created a new one.
    target_realm_key = "".join(c.lower() for c in wow_realm if c.isalnum())
    candidates = list(session.execute(
        select(Player).where(
            Player.name.ilike(name),
            Player.region.ilike(region),
        )
    ).scalars())
    matches = [
        c for c in candidates
        if "".join(ch.lower() for ch in c.realm if ch.isalnum()) == target_realm_key
    ]

    if len(matches) > 1:
        # Pre-existing duplicates: pick the row with the most runs as the
        # survivor. Don't merge inline — keeps this function's blast radius
        # small. Admin endpoint /api/admin/merge-all-duplicates handles it.
        matches.sort(
            key=lambda p: (len(p.runs), len(p.scores), -p.id),
            reverse=True,
        )
        logger.warning(
            "Duplicate Player rows for %s-%s-%s (ids=%s). Using id=%d; "
            "run /api/admin/merge-all-duplicates to reconcile.",
            name, realm, region, [p.id for p in matches], matches[0].id,
        )
    player = matches[0] if matches else None

    if player is None:
        player = Player(
            name=name, realm=wow_realm, region=region.upper(),
            class_id=class_id, wcl_id=wcl_id,
        )
        session.add(player)
        session.flush()
    else:
        # Track the latest wcl_id we saw for this identity, but only if
        # it wouldn't collide with a different row's wcl_id (unique
        # constraint). On collision, log and leave wcl_id alone — the
        # merge endpoint will reconcile when it runs.
        if wcl_id is not None and player.wcl_id != wcl_id:
            conflicting = session.execute(
                select(Player).where(
                    Player.wcl_id == wcl_id,
                    Player.id != player.id,
                )
            ).scalar_one_or_none()
            if conflicting is None:
                player.wcl_id = wcl_id
            else:
                logger.warning(
                    "wcl_id=%d already held by player_id=%d; not overwriting "
                    "player_id=%d (duplicate — will merge separately).",
                    wcl_id, conflicting.id, player.id,
                )
        player.name = name
        player.realm = wow_realm
        player.region = region.upper()
        # Keep an existing Player row's class_id in sync with our best
        # resolution (caller hint > Bnet > WCL). Subsequent fight-data
        # correction can still override this below when observed
        # playerDetails.type disagrees.
        if effective_hint is not None and player.class_id != effective_hint:
            player.class_id = effective_hint

    # 2b. Fetch Blizzard character media (avatar / inset / render) lazily.
    # Skip if we already pulled it recently (>7 days) or if creds aren't
    # set. Any failure is swallowed — media is a nice-to-have, not critical.
    _maybe_fetch_bnet_media(player, server_slug, name)

    # 3. Process each report — extract per-fight data (rolling window of last N runs)
    # `reports` was set above (either from char_data or report_codes).
    # Sort newest first to ensure rolling window uses most recent runs.
    reports.sort(key=lambda r: r.get("startTime", 0), reverse=True)

    # Build two dedup sets:
    #   - exact_runs: (report_code, fight_id) for re-ingest idempotence.
    #   - fuzzy_runs: (encounter_id, keystone_level, logged_at_datetime) for
    #     cross-log dedup. When multiple party members upload their own
    #     combat logs of the same key, WCL stores them as separate reports
    #     with different codes. The exact check doesn't catch those, so we
    #     also match on "same encounter + same key level + start within 2
    #     minutes of an already-stored run".
    existing_stmt = select(DungeonRun).where(DungeonRun.player_id == player.id)
    _existing = list(session.execute(existing_stmt).scalars())
    exact_runs = {(r.wcl_report_id, r.fight_id) for r in _existing}
    fuzzy_runs = [(r.encounter_id, r.keystone_level, r.logged_at) for r in _existing]

    runs: list[DungeonRun] = []
    discovered_groupmates: list[dict] = []
    seen_groupmates: set[str] = set()
    # Class names observed across fights — WCL's character endpoint sometimes
    # matches the wrong entity; the per-fight 'type' is authoritative.
    observed_class_names: list[str] = []

    logger.info("Processing %d reports for %s-%s", len(reports), name, realm)
    for report in reports:
        report_code = report["code"]
        zone = report.get("zone", {})
        zone_name = zone.get("name", "")

        if "mythic+" not in zone_name.lower():
            logger.debug("Report %s zone='%s' — skipped (not M+)", report_code, zone_name)
            continue

        # Get M+ fights from this report
        try:
            fights = wcl_client.get_report_fights(report_code)
        except WCLQueryError as e:
            logger.warning("Report %s fights query errored: %s", report_code, e)
            continue
        logger.info("Report %s: %d M+ fights", report_code, len(fights))
        if not fights:
            continue

        # Process each fight individually
        for fight in fights:
            fight_id = fight["id"]

            try:
                report_data = wcl_client.get_report_player_data(report_code, [fight_id])
            except WCLQueryError as e:
                logger.warning("Fight %s/%d data query errored: %s", report_code, fight_id, e)
                continue
            if not report_data:
                logger.warning("Fight %s/%d: no report_data returned", report_code, fight_id)
                continue

            player_details = report_data.get("playerDetails", {})

            # Only process fights where our player participated
            player_info = _find_player_in_details(player_details, name)
            if not player_info:
                all_names = []
                pd_inner = player_details.get("data", {}).get("playerDetails", {})
                for rg in ("dps", "tanks", "healers"):
                    for p in pd_inner.get(rg, []):
                        all_names.append(p.get("name", ""))
                logger.warning(
                    "Fight %s/%d: player %r not found in playerDetails. Names present: %s",
                    report_code, fight_id, name, all_names,
                )
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
            actor_id = player_info.get("id", 0)  # WCL actor ID for this fight

            # Record the per-fight class name (WCL playerDetails 'type' field).
            # This disambiguates same-spec-name-different-class cases that
            # spec-based inference can't handle (Resto Shaman vs Resto Druid).
            fight_class_name = player_info.get("type") or player_info.get("class")
            if fight_class_name:
                observed_class_names.append(fight_class_name)
            elif not observed_class_names:
                # One-shot diagnostic: log the available keys so we can see
                # what WCL actually returned. Prevents spamming per-fight.
                logger.info(
                    "No class name in playerDetails for %s: keys=%s sample=%s",
                    name,
                    sorted(player_info.keys()),
                    {k: v for k, v in player_info.items() if k in
                     ("type", "class", "subtype", "icon", "specs")},
                )

            # Extract per-fight stats
            damage_table = report_data.get("damageTable", {})
            healing_table = report_data.get("healingTable", {})
            damage_taken_table = report_data.get("damageTakenTable", {})
            interrupt_table = report_data.get("interruptTable", {})
            dispel_table = report_data.get("dispelTable", {})
            death_table = report_data.get("deathTable", {})
            casts_table = report_data.get("castsTable", {})
            healing_received_table = report_data.get("healingReceivedTable", {})

            # Fetch buffs + debuffs filtered by this player's actor ID
            buffs_table = {}
            debuffs_on_enemies = {}
            if actor_id:
                try:
                    aura_data = wcl_client.get_player_auras(report_code, [fight_id], actor_id)
                    buffs_table = aura_data.get("buffsTable", {})
                    debuffs_on_enemies = aura_data.get("debuffsOnEnemies", {})
                except WCLQueryError as e:
                    logger.debug("Failed to get auras for %s: %s", name, e)

            dps_total = _get_player_stat(damage_table, name)
            hps_total = _get_player_stat(healing_table, name)
            damage_taken = _get_player_stat(damage_taken_table, name)
            interrupts = _get_nested_stat(interrupt_table, name)
            dispels = _get_nested_stat(dispel_table, name)
            deaths = _count_deaths(death_table, name)
            total_casts = _get_total_casts(casts_table, name)

            # Healing received by this player (from healingReceivedTable or healing_table targets)
            healing_received = _get_healing_received(
                healing_received_table or healing_table, name
            )

            # Cooldown usage: score frequency relative to expected uses
            encounter_id = fight.get("encounterID", 0)
            spec_cds = get_cooldowns_for_spec(class_id, spec_name)
            fight_duration_ms = fight.get("endTime", 0) - fight.get("startTime", 0)
            cd_usage = _get_cooldown_usage(buffs_table, spec_cds, fight_duration_ms)

            # Avoidable damage and avoidable deaths
            avoidable_ids = get_avoidable_abilities(encounter_id)
            avoidable_dmg = _get_avoidable_damage(damage_taken_table, name, avoidable_ids)
            avoidable_death_count = _count_avoidable_deaths(death_table, name, avoidable_ids)

            # Critical interrupts (high-priority spells)
            critical_interrupt_ids = get_critical_interrupt_ids(encounter_id)
            crit_interrupts = _count_critical_interrupts(interrupt_table, name, critical_interrupt_ids)

            # CC casts — use the events API (not the Casts table) because
            # WCL's Casts summary only surfaces top-5 abilities per player.
            # CC spells are usually low-frequency and get truncated out.
            # Events returns every cast.
            fight_class_id = class_id_from_name(fight_class_name) or class_id
            cc_ability_ids = get_cc_ability_ids(fight_class_id)
            cc_count = 0
            if actor_id and cc_ability_ids:
                try:
                    cc_count = wcl_client.get_player_cast_counts(
                        report_code, [fight_id], actor_id, cc_ability_ids,
                    )
                except WCLQueryError as e:
                    logger.debug("CC events query failed for %s/%d: %s", report_code, fight_id, e)

            duration_ms = fight.get("endTime", 0) - fight.get("startTime", 0)

            # Timed = completed AND within the dungeon's par time
            # keystoneTime is the par timer in ms; kill means the key was completed
            key_completed = fight.get("kill", False)
            keystone_time = fight.get("keystoneTime", 0)
            key_timed = key_completed and keystone_time > 0 and duration_ms <= keystone_time

            # Fight's absolute wall-clock start time. report.startTime is
            # when the log began; fight.startTime is the ms offset within
            # the log. Adding them gives a timestamp comparable across
            # different logs of the same key.
            fight_abs_start_ms = report.get("startTime", 0) + fight.get("startTime", 0)
            fight_logged_at = datetime.fromtimestamp(fight_abs_start_ms / 1000)
            fight_keystone = fight.get("keystoneLevel", 0)

            # Exact dedup — same (report_code, fight_id). Hit when we
            # re-ingest the same player's own upload.
            if (report_code, fight_id) in exact_runs:
                continue

            # Fuzzy dedup — same encounter + keystone level + start time
            # within 2 minutes. Catches the case where 2+ party members
            # uploaded their own logs of the same key; WCL exposes all of
            # them to each participant via recentReports.
            is_fuzzy_dup = False
            for e_encounter, e_keystone, e_logged_at in fuzzy_runs:
                if (e_encounter == encounter_id
                        and e_keystone == fight_keystone
                        and abs((e_logged_at - fight_logged_at).total_seconds()) < 120):
                    is_fuzzy_dup = True
                    break
            if is_fuzzy_dup:
                logger.debug(
                    "Skipping cross-log duplicate for %s: encounter=%d +%d at %s",
                    name, encounter_id, fight_keystone, fight_logged_at,
                )
                continue

            # Track this new run so later fights in the same batch see it.
            fuzzy_runs.append((encounter_id, fight_keystone, fight_logged_at))

            # Level B v2 — pull-by-pull breakdown. Only built for ≥+8
            # keys (see _BREAKDOWN_MIN_KEYSTONE). The helper does four
            # narrowed events-API calls (deaths, damage-taken, interrupts,
            # plus one masterData fetch) and returns a list of pull
            # objects, each with events sorted inside. Degrades to None
            # if actor_id isn't resolvable or all fetches error.
            pulls = _build_pulls(
                actor_id=actor_id,
                report_code=report_code,
                fight_id=fight_id,
                fight_start_ms=fight.get("startTime", 0),
                avoidable_ids=avoidable_ids,
                critical_interrupt_ids=critical_interrupt_ids,
                keystone_level=fight_keystone,
            )

            run = DungeonRun(
                player_id=player.id,
                encounter_id=encounter_id,
                keystone_level=fight_keystone,
                role=role,
                spec_name=spec_name,
                dps=dps_total,
                hps=hps_total,
                ilvl=ilvl,
                duration=duration_ms,
                deaths=deaths,
                interrupts=interrupts,
                dispels=dispels,
                avoidable_damage_taken=avoidable_dmg,
                damage_taken_total=damage_taken,
                casts_total=total_casts,
                cooldown_usage_pct=cd_usage,
                wcl_report_id=report_code,
                fight_id=fight_id,
                timed=key_timed,
                logged_at=fight_logged_at,
                # Enrichment fields
                rating=fight.get("rating"),
                average_item_level=fight.get("averageItemLevel"),
                keystone_affixes=fight.get("keystoneAffixes"),
                healing_received=healing_received,
                cc_casts=cc_count,
                critical_interrupts=crit_interrupts,
                avoidable_deaths=avoidable_death_count,
                party_comp=_extract_party_comp(player_details) or None,
                pulls=pulls,
            )
            session.add(run)
            runs.append(run)

        # Stop if we have enough runs
        if len(runs) >= settings.max_runs_to_analyze:
            break

    # 4. Fetch zone rankings for DPS percentile (available even for archived reports)
    #    Two comparisons: overall (vs all of spec) and by ilvl bracket
    zone_dps_percentile = None
    zone_dps_ilvl_percentile = None
    zone_total_kills = 0
    try:
        zone_data = wcl_client.get_zone_rankings(
            name=name,
            server_slug=server_slug,
            server_region=region.lower(),
            zone_id=settings.wcl_mplus_zone_id,
        )

        # Overall percentiles (vs all players of same spec)
        overall_pcts = []
        for dungeon in zone_data.get("overall", {}).get("rankings", []):
            best_pct = dungeon.get("rankPercent")
            kills = dungeon.get("totalKills", 0)
            zone_total_kills += kills
            if best_pct is not None and kills > 0:
                overall_pcts.append(best_pct)

        if overall_pcts:
            zone_dps_percentile = sum(overall_pcts) / len(overall_pcts)

        # By ilvl bracket percentiles (vs same spec at similar gear level)
        ilvl_pcts = []
        for dungeon in zone_data.get("by_ilvl", {}).get("rankings", []):
            best_pct = dungeon.get("rankPercent")
            kills = dungeon.get("totalKills", 0)
            if best_pct is not None and kills > 0:
                ilvl_pcts.append(best_pct)

        if ilvl_pcts:
            zone_dps_ilvl_percentile = sum(ilvl_pcts) / len(ilvl_pcts)

        logger.info(
            "Zone rankings: overall=%.1f%%, by_ilvl=%.1f%%, %d dungeons, %d total kills",
            zone_dps_percentile or 0, zone_dps_ilvl_percentile or 0,
            len(overall_pcts), zone_total_kills,
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

            # Overwrite raw DPS with rankPercent when WCL has a ranking
            # for this fight. Runs without a match keep their raw DPS —
            # the scorer in engine.py guards against out-of-range values
            # and skips them, so storing raw here is intentional and
            # safe. No separate "percentile available?" flag needed.
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

    # Correct class_id if the WCL character endpoint returned the wrong
    # character entity (name collisions on a realm). Preference order:
    #   0. Caller-supplied class_hint (handled up top — trusted absolutely).
    #   1. Most common per-fight class name from playerDetails.type
    #      (handles Resto Shaman vs Resto Druid — spec alone can't tell).
    #   2. Spec-based inference for unambiguous specs (Brewmaster → Monk).
    #   3. Whatever WCL's character endpoint returned.
    #
    # Bnet-resolved `effective_hint` is intentionally NOT treated as absolute
    # here: if Bnet says Mage but all fights in recent reports are Rogue,
    # WCL is almost certainly serving a different player's logs under this
    # name. We surface that collision below as a loud warning so we can
    # decide whether to act on it (reject ingest, ask user to claim, etc).
    if class_hint is None:
        from collections import Counter

        resolved_class_id: int | None = None
        if observed_class_names:
            name_counts = Counter(observed_class_names)
            most_common_name, _ = name_counts.most_common(1)[0]
            resolved_class_id = class_id_from_name(most_common_name)

        if resolved_class_id is None and recent_runs:
            spec_counts = Counter(r.spec_name for r in recent_runs)
            most_common_spec, _ = spec_counts.most_common(1)[0]
            resolved_class_id = resolve_class_id(most_common_spec, class_id)

        if resolved_class_id is not None and resolved_class_id != class_id:
            logger.info(
                "Overriding class_id for %s-%s: WCL character said %d, fight data implies %d",
                name, realm, class_id, resolved_class_id,
            )
            class_id = resolved_class_id
            player.class_id = resolved_class_id

        # Bnet-vs-fight-data collision check: fires when Bnet told us the
        # character is class X but every recent fight shows class Y. The
        # logs are almost certainly a different player's — surface this
        # clearly so future ops can reject / quarantine these ingests.
        if (
            effective_hint is not None
            and resolved_class_id is not None
            and effective_hint != resolved_class_id
        ):
            logger.warning(
                "COLLISION SUSPECT %s-%s-%s: Bnet class_id=%d, but fights imply %d. "
                "WCL may be serving a different character's logs under this name.",
                name, realm, region, effective_hint, resolved_class_id,
            )

    # Clear old scores
    old_scores_stmt = select(PlayerScore).where(PlayerScore.player_id == player.id)
    for old_score in session.execute(old_scores_stmt).scalars():
        session.delete(old_score)

    for role, role_runs in runs_by_role.items():
        if len(role_runs) < settings.min_runs_for_grade:
            continue

        result = score_player_runs(role_runs, role, zone_dps_percentile, zone_dps_ilvl_percentile, class_id=class_id)

        # Total runs = all stored history (for the website), not just the scoring window
        total_runs = max(len(all_runs), zone_total_kills)

        score = PlayerScore(
            player_id=player.id,
            role=role,
            overall_grade=result.overall_grade,
            composite_score=result.composite_score,
            category_scores=result.category_scores,
            runs_analyzed=total_runs,
            primary_role=(role == primary_role),
        )
        session.add(score)

    player.last_ingested_at = datetime.utcnow()
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
    """Ingest a batch of players sequentially.

    Each player dict supports the optional hint keys 'class_id' (int 1-13)
    or 'class_name' (e.g. 'Mage') to override WCL's unreliable character
    endpoint. 'class_id' wins if both are supplied.
    """
    results: list[IngestResult] = []
    for p in players:
        hint = _resolve_class_hint(p.get("class_id"), p.get("class_name"))
        result = ingest_player(
            session, p["name"], p["realm"], p["region"],
            class_hint=hint,
            report_codes=p.get("report_codes") or None,
        )
        if result.player:
            results.append(result)
    return results


def _resolve_class_hint(class_id_hint, class_name_hint) -> int | None:
    """Turn caller-supplied class_id/class_name into a valid class_id 1-13."""
    if class_id_hint is not None:
        try:
            cid = int(class_id_hint)
            if 1 <= cid <= 13:
                return cid
        except (TypeError, ValueError):
            pass
    if class_name_hint:
        cid = class_id_from_name(str(class_name_hint))
        if cid is not None:
            return cid
    return None
