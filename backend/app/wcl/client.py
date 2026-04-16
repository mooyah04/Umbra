import itertools
import logging
import threading
import time

import httpx

from app.config import settings
from app.wcl.auth import WCLCredential, wcl_auth

logger = logging.getLogger(__name__)


# Per-client concurrency cap. Each Platinum client gets its own 18k/hr
# budget, so per-client in-flight matters more than a global ceiling.
# 4 gives headroom for latency variance without walking into the rate
# limit on a single client.
_WCL_MAX_IN_FLIGHT_PER_CLIENT = 4

# Hard cap on Retry-After. WCL has been observed returning huge values
# (e.g. 2800s = 47 min — quota-reset windows). Anything longer than this
# puts the client into cooldown; the router tries the next healthy client
# before raising WCLRateLimitedError.
_RETRY_AFTER_MAX_SECONDS = 20


class _ClientState:
    """Per-credential runtime state: semaphore + cooldown-until timestamp.
    Created lazily the first time a credential is used."""
    __slots__ = ("semaphore", "cooldown_until")

    def __init__(self) -> None:
        self.semaphore = threading.Semaphore(_WCL_MAX_IN_FLIGHT_PER_CLIENT)
        self.cooldown_until = 0.0  # unix ts; 0 = healthy


_state_by_id: dict[str, _ClientState] = {}
_state_lock = threading.Lock()
# Cycle credentials so successive requests hit different clients. Sized
# to the credential pool at first use; reset if the pool changes (tests).
_rotation: itertools.cycle | None = None
_rotation_pool_size: int = 0


def _state_for(cred: WCLCredential) -> _ClientState:
    with _state_lock:
        st = _state_by_id.get(cred.client_id)
        if st is None:
            st = _ClientState()
            _state_by_id[cred.client_id] = st
        return st


def _healthy_first(creds: list[WCLCredential]) -> list[WCLCredential]:
    """Return credentials ordered so healthy ones come first, starting
    the round-robin from a rotating offset. Cooling clients get tried
    last as a fallback before we give up."""
    global _rotation, _rotation_pool_size
    if not creds:
        return []
    with _state_lock:
        if _rotation is None or _rotation_pool_size != len(creds):
            _rotation = itertools.cycle(range(len(creds)))
            _rotation_pool_size = len(creds)
        offset = next(_rotation)
    rotated = creds[offset:] + creds[:offset]
    now = time.time()
    healthy = [c for c in rotated if _state_for(c).cooldown_until <= now]
    cooling = [c for c in rotated if _state_for(c).cooldown_until > now]
    return healthy + cooling


def _min_cooldown_remaining(creds: list[WCLCredential]) -> int:
    now = time.time()
    cds = [
        max(0, _state_for(c).cooldown_until - now)
        for c in creds
    ]
    return int(min(cds)) if cds else 0


def _client_label(cred: WCLCredential) -> str:
    """Short identifier for log lines; we never want to log the full
    client_id or secret."""
    return cred.client_id[:6] + "…" if cred.client_id else "<unset>"


class WCLClient:
    """Sync GraphQL client for Warcraft Logs API v2.

    When multiple client credentials are configured, queries rotate
    across them so the 18k-points/hr Platinum budget scales linearly
    with the number of clients. Per-client 429s put just that client
    into cooldown — other clients keep serving.
    """

    def query(self, graphql: str, variables: dict | None = None) -> dict:
        creds = wcl_auth.credentials()
        if not creds:
            raise RuntimeError(
                "WCL credentials not configured. Set WCL_CLIENT_ID + "
                "WCL_CLIENT_SECRET (single) or WCL_CLIENT_IDS + "
                "WCL_CLIENT_SECRETS (multi)."
            )

        max_retries_per_client = 2
        attempts_remaining = max_retries_per_client * len(creds)
        last_resp: httpx.Response | None = None
        ordered = _healthy_first(creds)

        while attempts_remaining > 0:
            attempts_remaining -= 1
            # Pick the first healthy client (or the coolest one as a
            # last resort). Ordering is recomputed each attempt so a
            # freshly-cooled client becomes visible to later retries.
            now = time.time()
            cred = next(
                (c for c in ordered if _state_for(c).cooldown_until <= now),
                None,
            )
            if cred is None:
                # All clients cooling. Don't block the request thread;
                # raise with the shortest remaining cooldown so user-
                # facing callers can surface it immediately.
                raise WCLRateLimitedError(_min_cooldown_remaining(creds))

            state = _state_for(cred)
            token = wcl_auth.get_token_for(cred)

            with state.semaphore:
                with httpx.Client() as client:
                    last_resp = client.post(
                        settings.wcl_api_url,
                        json={"query": graphql, "variables": variables or {}},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30.0,
                    )

            if last_resp.status_code == 429:
                retry_after_header = last_resp.headers.get("Retry-After")
                try:
                    advised = int(retry_after_header) if retry_after_header else None
                except ValueError:
                    advised = None

                if advised is not None and advised > _RETRY_AFTER_MAX_SECONDS:
                    # Park this client; try the next one (if any).
                    state.cooldown_until = time.time() + advised
                    logger.warning(
                        "WCL 429 on client %s, Retry-After=%ds — "
                        "cooling down, trying next client (remaining=%d)",
                        _client_label(cred), advised, attempts_remaining,
                    )
                    # Refresh ordering so the newly-cooling client drops
                    # out of the healthy pool for subsequent attempts.
                    ordered = _healthy_first(creds)
                    continue

                # Short backoff — a few seconds, same client is fine.
                wait = advised if advised is not None else 5
                logger.warning(
                    "WCL 429 on client %s, waiting %ds (remaining=%d)",
                    _client_label(cred), wait, attempts_remaining,
                )
                time.sleep(wait)
                continue

            last_resp.raise_for_status()
            data = last_resp.json()
            if "errors" in data:
                raise WCLQueryError(data["errors"])
            return data["data"]

        # Exhausted retries across clients. If the last response was a
        # 429, surface it as WCLRateLimitedError so user endpoints can
        # distinguish from generic HTTP errors.
        if last_resp is not None and last_resp.status_code == 429:
            raise WCLRateLimitedError(_min_cooldown_remaining(creds))
        if last_resp is not None:
            last_resp.raise_for_status()
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

    def get_report_header_and_fights(self, report_code: str) -> dict:
        """Return {'startTime': int, 'fights': list[dict]} in one query.

        Callers needing wall-clock timestamps for fights should use this
        — report.startTime is the absolute ms epoch, fight.startTime is
        the offset within the report.
        """
        from app.wcl.queries import REPORT_FIGHTS

        data = self.query(REPORT_FIGHTS, {"code": report_code})
        report = data.get("reportData", {}).get("report") or {}
        return {
            "startTime": report.get("startTime", 0),
            "fights": report.get("fights", []),
        }

    def get_report_player_data(
        self, report_code: str, fight_ids: list[int]
    ) -> dict | None:
        from app.wcl.queries import REPORT_PLAYER_DATA

        data = self.query(
            REPORT_PLAYER_DATA,
            {"code": report_code, "fightIDs": fight_ids},
        )
        return data.get("reportData", {}).get("report")

    def get_player_cast_counts(
        self,
        report_code: str,
        fight_ids: list[int],
        source_id: int,
        ability_ids: set[int],
    ) -> int:
        """Count cast events for a set of abilities the player made in a fight.

        WCL's Casts table only surfaces the player's top-5 abilities by
        frequency, so rare-but-important casts (Leg Sweep, Paralysis,
        Capacitor Totem, etc.) are invisible in the table. Events API
        returns every cast, so this works for CC tracking regardless of
        frequency. Pagination handled internally.
        """
        if not ability_ids or not fight_ids:
            return 0
        query = """
        query($code: String!, $fightIDs: [Int!]!, $sourceID: Int!,
              $startTime: Float!, $endTime: Float) {
          reportData {
            report(code: $code) {
              events(fightIDs: $fightIDs, dataType: Casts,
                     sourceID: $sourceID, startTime: $startTime,
                     endTime: $endTime, limit: 10000) {
                data
                nextPageTimestamp
              }
            }
          }
        }
        """
        total = 0
        start = 0.0
        seen_pages = 0
        while True:
            vars = {
                "code": report_code,
                "fightIDs": fight_ids,
                "sourceID": source_id,
                "startTime": start,
                "endTime": None,
            }
            data = self.query(query, vars)
            events = data.get("reportData", {}).get("report", {}).get("events", {})
            batch = events.get("data") or []
            if isinstance(batch, str):
                # Some WCL responses return events as a JSON-encoded string.
                import json as _json
                try:
                    batch = _json.loads(batch)
                except Exception:
                    batch = []
            for ev in batch:
                if ev.get("type") != "cast":
                    continue
                if ev.get("abilityGameID") in ability_ids:
                    total += 1
            nxt = events.get("nextPageTimestamp")
            seen_pages += 1
            if not nxt or seen_pages > 20:
                break
            start = nxt
        return total

    def get_player_auras(
        self, report_code: str, fight_ids: list[int], source_id: int
    ) -> dict:
        """Fetch buffs (on self) and debuffs (applied to enemies) for a player.

        Returns dict with 'buffsTable' and 'debuffsOnEnemies' keys.
        """
        from app.wcl.queries import REPORT_PLAYER_AURAS

        data = self.query(
            REPORT_PLAYER_AURAS,
            {"code": report_code, "fightIDs": fight_ids, "sourceID": source_id},
        )
        report = data.get("reportData", {}).get("report", {})
        return {
            "buffsTable": report.get("buffsTable", {}),
            "debuffsOnEnemies": report.get("debuffsOnEnemies", {}),
        }

    # Backwards-compatible alias
    def get_player_buffs(
        self, report_code: str, fight_ids: list[int], source_id: int
    ) -> dict:
        return self.get_player_auras(report_code, fight_ids, source_id).get("buffsTable", {})

    def get_player_events(
        self,
        report_code: str,
        fight_ids: list[int],
        data_type: str,
        source_id: int | None = None,
        target_id: int | None = None,
    ) -> list[dict]:
        """Paginated events-API fetch for a single player, narrowed by
        WCL's first-class sourceID / targetID query parameters (not the
        fragile filterExpression string). Caller filters by ability ID
        Python-side.

        Used by the per-run event-timeline ingest (Level B). Typical
        shapes we call this with:
          - DamageTaken + target_id=<actor> — damage received by player
          - Interrupts + source_id=<actor> — kicks performed by player
          - Deaths + target_id=<actor> — death events for player

        Narrowing by ID at the query level drops event volume from
        tens-of-thousands per fight to tens-to-hundreds, so the paginate
        loop usually exits after one page. We still cap at 5 pages to
        avoid burning rate limit on a pathological fight.
        """
        if not fight_ids:
            return []
        # Build the optional argument fragments. WCL rejects the query
        # if we pass null for these, so we include them only when set.
        extra_args = []
        extra_vars = []
        if source_id is not None:
            extra_args.append("sourceID: $sourceID")
            extra_vars.append("$sourceID: Int!")
        if target_id is not None:
            extra_args.append("targetID: $targetID")
            extra_vars.append("$targetID: Int!")
        args_csv = ", ".join(extra_args)
        vars_csv = ", ".join(extra_vars)
        query = """
        query($code: String!, $fightIDs: [Int!]!, $startTime: Float!, $dataType: EventDataType!%s) {
          reportData {
            report(code: $code) {
              events(dataType: $dataType, fightIDs: $fightIDs,
                     startTime: $startTime, limit: 10000%s) {
                data
                nextPageTimestamp
              }
            }
          }
        }
        """ % (
            (", " + vars_csv) if vars_csv else "",
            (", " + args_csv) if args_csv else "",
        )

        events: list[dict] = []
        start = 0.0
        seen_pages = 0
        while True:
            variables: dict = {
                "code": report_code,
                "fightIDs": fight_ids,
                "startTime": start,
                "dataType": data_type,
            }
            if source_id is not None:
                variables["sourceID"] = source_id
            if target_id is not None:
                variables["targetID"] = target_id
            data = self.query(query, variables)
            events_blob = (
                data.get("reportData", {}).get("report", {}).get("events", {}) or {}
            )
            batch = events_blob.get("data") or []
            if isinstance(batch, str):
                import json as _json
                try:
                    batch = _json.loads(batch)
                except Exception:
                    batch = []
            events.extend(batch)
            nxt = events_blob.get("nextPageTimestamp")
            seen_pages += 1
            if not nxt or seen_pages >= 5:
                break
            start = nxt
        return events

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
        zone_id: int = 47,  # Midnight Season 1
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


    def get_fight_dungeon_pulls(
        self, report_code: str, fight_id: int
    ) -> list[dict]:
        """Return WCL's authoritative pull breakdown for a single M+ fight.

        WCL pre-computes pull boundaries for every M+ fight, including
        the most-notable enemy's name, the time range, a kill flag, and
        the list of enemy NPCs with their instance ranges. This is the
        source of truth for Level B v2's pull breakdown — far better
        than clustering death events ourselves.

        Returns [] for non-M+ fights or on query failure.
        """
        query = """
        query($code: String!, $fightIDs: [Int!]!) {
          reportData {
            report(code: $code) {
              fights(fightIDs: $fightIDs) {
                dungeonPulls {
                  id
                  name
                  startTime
                  endTime
                  kill
                  enemyNPCs { id gameID minimumInstanceID maximumInstanceID }
                }
              }
            }
          }
        }
        """
        try:
            data = self.query(query, {"code": report_code, "fightIDs": [fight_id]})
        except Exception as e:
            logger.warning("get_fight_dungeon_pulls failed for %s/%d: %s",
                           report_code, fight_id, e)
            return []
        fights = (
            data.get("reportData", {}).get("report", {}).get("fights") or []
        )
        if not fights:
            return []
        return fights[0].get("dungeonPulls") or []

    def get_report_master_data(self, report_code: str) -> dict:
        """Return the report's masterData with actors + abilities.

        Actors: {id, name, type, subType} — type distinguishes Player /
        NPC / Boss / Pet, needed to filter damage events to only those
        caused by enemies.

        Abilities: {gameID, name} — used by Level B timeline + damage
        sampler to resolve `abilityGameID` on event payloads back to
        human-readable names. Adding abilities to this query is free
        (same GraphQL round-trip) and callers ignore what they don't use.
        """
        query = """
        query($code: String!) {
          reportData {
            report(code: $code) {
              masterData {
                actors { id name type subType }
                abilities { gameID name }
              }
            }
          }
        }
        """
        data = self.query(query, {"code": report_code})
        report = data.get("reportData", {}).get("report") or {}
        master = report.get("masterData") or {}
        return master

    def get_damage_taken_from_npcs(
        self, report_code: str, fight_ids: list[int]
    ) -> dict[int, dict]:
        """Return per-ability damage taken by the party FROM NPCs/Bosses
        only, aggregated across the given fights. Excludes Player and
        Pet sources, which removes Aug Evoker buff noise / party AoE
        pollution that the simpler `table(viewBy: Ability)` query
        couldn't filter out.

        Returns {ability_id: {name, total}}. Caller can sort/threshold.
        """
        if not fight_ids:
            return {}
        master = self.get_report_master_data(report_code)
        actors = master.get("actors") or []
        # Only NPC + Boss are real enemy sources. Pet damage usually
        # belongs to the player who owns the pet (would re-introduce
        # noise). Player sources are obviously what we're filtering out.
        npc_ids = {
            a["id"] for a in actors
            if a.get("type") in ("NPC", "Boss") and isinstance(a.get("id"), int)
        }
        if not npc_ids:
            return {}

        # Paginate through events. WCL caps at ~10k events per page;
        # M+ fights can have 30k-100k damage events, so 3-10 pages
        # typical per fight.
        query = """
        query($code: String!, $fightIDs: [Int!]!, $startTime: Float!) {
          reportData {
            report(code: $code) {
              events(dataType: DamageTaken, fightIDs: $fightIDs,
                     startTime: $startTime, limit: 10000) {
                data
                nextPageTimestamp
              }
            }
          }
        }
        """
        per_ability: dict[int, dict] = {}
        # Resolve ability names from the same masterData payload's
        # ability list — but masterData query only returned actors, so
        # we'll harvest names from event payloads (each event includes
        # ability info or ability ID we resolve later).
        start = 0.0
        seen_pages = 0
        while True:
            data = self.query(
                query,
                {"code": report_code, "fightIDs": fight_ids, "startTime": start},
            )
            events_blob = (
                data.get("reportData", {}).get("report", {}).get("events", {}) or {}
            )
            batch = events_blob.get("data") or []
            if isinstance(batch, str):
                import json as _json
                try:
                    batch = _json.loads(batch)
                except Exception:
                    batch = []
            for ev in batch:
                if ev.get("type") not in ("damage", "calculateddamage"):
                    continue
                src = ev.get("sourceID")
                if src not in npc_ids:
                    continue
                aid = ev.get("abilityGameID")
                if not isinstance(aid, int):
                    continue
                amount = int(ev.get("amount") or 0) + int(ev.get("absorbed") or 0)
                slot = per_ability.setdefault(aid, {"name": None, "total": 0})
                slot["total"] += amount
            nxt = events_blob.get("nextPageTimestamp")
            seen_pages += 1
            if not nxt or seen_pages > 20:
                break
            start = nxt

        # Resolve ability names with one extra masterData-style query.
        # WCL exposes abilities via the report's masterData abilities[]
        # — refetch with that field included.
        if per_ability:
            try:
                names_query = """
                query($code: String!) {
                  reportData {
                    report(code: $code) {
                      masterData { abilities { gameID name } }
                    }
                  }
                }
                """
                data = self.query(names_query, {"code": report_code})
                ab_list = (
                    data.get("reportData", {}).get("report", {}).get("masterData", {}).get("abilities") or []
                )
                name_by_id = {a.get("gameID"): a.get("name") for a in ab_list if a.get("gameID")}
                for aid, slot in per_ability.items():
                    slot["name"] = name_by_id.get(aid) or "?"
            except Exception:
                pass

        return per_ability

    def get_top_logs_for_encounter(
        self,
        encounter_id: int,
        metric: str = "speed",
        limit: int = 10,
    ) -> list[dict]:
        """Return up to `limit` log entries for an encounter, sampled
        evenly across the top 100 ranked logs.

        Returning the strict top N has a flaw: top N is all the same
        meta comp, so the cross-log "consensus mechanic" filter sees
        Augmentation Evoker / Brewmaster abilities in 100% of logs and
        can't distinguish them from real boss mechanics. Sampling every
        Nth log across the top-100 page diversifies the comp mix —
        ranks 1-20 are meta, but ranks 50-100 bring different
        specs/strategies, so player-ability noise drops below
        consensus while real boss mechanics survive.

        Each entry: {report_code, fight_id, start_time, amount,
        duration, keystone_level}. Used for sampling damage-taken
        across many high-quality but DIVERSE runs of the same dungeon.
        """
        if limit <= 0:
            return []
        query = """
        query($encId: Int!) {
          worldData {
            encounter(id: $encId) {
              fightRankings(metric: %s, page: 1)
            }
          }
        }
        """ % metric
        data = self.query(query, {"encId": encounter_id})
        ranking = data.get("worldData", {}).get("encounter", {}).get("fightRankings") or {}
        rankings = ranking.get("rankings") or []
        if not rankings:
            return []

        # Even-stride sampling: pick `limit` entries spread across the
        # full ranking page. e.g. limit=20 from 100 entries → take
        # ranks 1, 6, 11, ..., 96. Falls back to the natural ordering
        # if there aren't enough entries to stride over.
        if len(rankings) <= limit:
            picks = rankings
        else:
            stride = len(rankings) / limit
            picks = [rankings[int(i * stride)] for i in range(limit)]

        out: list[dict] = []
        for r in picks:
            report = r.get("report") or {}
            out.append({
                "report_code": report.get("code"),
                "fight_id": report.get("fightID"),
                "start_time": report.get("startTime"),
                "amount": r.get("amount"),
                "duration": r.get("duration"),
                "keystone_level": r.get("bracketData"),
            })
        return [o for o in out if o["report_code"] and o["fight_id"]]

    def get_top_characters_for_spec(
        self,
        encounter_id: int,
        class_name: str,
        spec_name: str,
        metric: str = "dps",
        limit: int = 10,
    ) -> list[dict]:
        """Return the top N character rankings for a (class, spec) on an
        encounter. Each entry: {name, server_slug, server_region,
        report_code, fight_id, amount, spec, class}. Used for sampling
        which buffs the actual top performers of a spec consistently
        have — anything in 80%+ of top players is a real major CD.
        """
        if limit <= 0:
            return []
        query = """
        query($encId: Int!, $klass: String!, $spec: String!) {
          worldData {
            encounter(id: $encId) {
              characterRankings(metric: %s, className: $klass, specName: $spec, page: 1)
            }
          }
        }
        """ % metric
        data = self.query(query, {"encId": encounter_id, "klass": class_name, "spec": spec_name})
        ranking = data.get("worldData", {}).get("encounter", {}).get("characterRankings") or {}
        rankings = ranking.get("rankings") or []
        out: list[dict] = []
        for r in rankings[:limit]:
            server = r.get("server") or {}
            region = (server.get("region") or {}).get("slug") if isinstance(server.get("region"), dict) else server.get("region")
            report = r.get("report") or {}
            out.append({
                "name": r.get("name"),
                "server_slug": server.get("slug"),
                "server_region": region,
                "report_code": report.get("code"),
                "fight_id": report.get("fightID"),
                "amount": r.get("amount"),
                "spec": r.get("spec"),
                "class": r.get("class"),
            })
        return [o for o in out if o["report_code"] and o["fight_id"] and o["name"]]

    def get_damage_taken_table(
        self, report_code: str, fight_ids: list[int]
    ) -> list[dict]:
        """Return the damage-taken table aggregated across the given fights.

        Used for dungeon-data research: which ability IDs account for the
        bulk of avoidable damage on an encounter. Returns the 'entries'
        list (one per ability) with 'name', 'guid', 'total'.
        """
        if not fight_ids:
            return []
        # NOTE: do NOT pass `hostilityType: Enemies` here. For dataType
        # DamageTaken, WCL's hostilityType filters by the entity that
        # TAKES the damage — Enemies returns damage to mobs (your
        # outgoing damage), Friendlies (the default) returns damage to
        # your party (boss/enemy outgoing damage), which is what we
        # actually want for avoidable-mechanic sampling.
        query = """
        query($code: String!, $fightIDs: [Int!]!) {
          reportData {
            report(code: $code) {
              table(dataType: DamageTaken, fightIDs: $fightIDs,
                    viewBy: Ability)
            }
          }
        }
        """
        data = self.query(query, {"code": report_code, "fightIDs": fight_ids})
        table = (
            data.get("reportData", {}).get("report", {}).get("table", {}) or {}
        )
        tdata = table.get("data") or {}
        entries = tdata.get("entries") or []
        return entries


class WCLQueryError(Exception):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__(f"WCL GraphQL errors: {'; '.join(messages)}")


class WCLRateLimitedError(Exception):
    """Raised when WCL returns 429 with a Retry-After longer than
    `_RETRY_AFTER_MAX_SECONDS`. Callers decide whether to fail the
    user request, reschedule, or back off the whole worker pool."""
    def __init__(self, retry_after_seconds: int):
        self.retry_after = retry_after_seconds
        super().__init__(
            f"WCL rate limit; retry after {retry_after_seconds}s"
        )


wcl_client = WCLClient()
