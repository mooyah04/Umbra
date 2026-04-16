"""Umbra Backend — FastAPI application."""

import logging
from datetime import datetime, timedelta

import hashlib

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import Float, Integer, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import engine, get_session
from app.export.lua_writer import generate_lua
from app.models import AddonDownload, Base, DungeonRun, Player, PlayerScore, Role
from app.pipeline.ingest import ingest_batch, ingest_player
from app.security import limiter, require_api_key
from app.validators import ValidationError, validate_player_identity
from app.schemas import (
    ClaimRequest,
    ClaimResponse,
    HistoryPoint,
    HistoryResponse,
    IngestRequest,
    IngestResponse,
    PlayerProfileResponse,
    PlayerScoreResponse,
    PlayerSearchResult,
    RoleScore,
    RunListResponse,
    RunResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    Base.metadata.create_all(engine)
    from app import scheduler
    scheduler.start()
    yield
    scheduler.stop()
    engine.dispose()


app = FastAPI(title="Umbra Score Engine", version="0.2.0", lifespan=lifespan)

# ── Rate limiting ───────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return PlainTextResponse(
        f"Rate limit exceeded: {exc.detail}",
        status_code=429,
        headers={"Retry-After": "60"},
    )


# ── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://wowumbra.gg",
        "https://www.wowumbra.gg",
    ],
    # Vercel assigns the bare mooyah04.vercel.app for this project plus
    # per-branch/PR preview hostnames like <something>-mooyah04.vercel.app
    # and umbra-git-<branch>-mooyah04.vercel.app. Match all three shapes.
    allow_origin_regex=r"https://([a-z0-9-]+-)?mooyah04\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _canonical_identity(name: str, realm: str, region: str) -> tuple[str, str, str]:
    """Validate + normalize identity tuple, or raise HTTP 400."""
    try:
        return validate_player_identity(name, realm, region)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _realm_key(realm: str) -> str:
    """Normalize a realm name for equality comparison.

    The codebase mixes three realm storage/display conventions:
      - WoW display:  'Tarren Mill'
      - WCL slug:     'tarren-mill'
      - Raider.IO:    'TarrenMill'
    Stripping to alphanumeric + lowercase collapses all three to 'tarrenmill'
    so any inbound format finds the row regardless of how it was stored.
    """
    return "".join(c.lower() for c in realm if c.isalnum())


def _find_player(session: Session, region: str, realm: str, name: str) -> Player | None:
    """Find a player by name + region, filter realm in Python on the normalized key.

    Filtering realm client-side keeps the lookup independent of which storage
    convention ingest used. Scale fine for preview-level data; if the player
    count grows large, add an indexed realm_key column to avoid the full scan.
    """
    target = _realm_key(realm)
    stmt = (
        select(Player)
        .where(
            Player.name.ilike(name),
            Player.region.ilike(region),
        )
        .options(selectinload(Player.scores), selectinload(Player.runs))
    )
    for p in session.execute(stmt).scalars():
        if _realm_key(p.realm) == target:
            return p
    return None


def _run_to_response(run: DungeonRun) -> RunResponse:
    return RunResponse(
        id=run.id,
        encounter_id=run.encounter_id,
        keystone_level=run.keystone_level,
        role=run.role.value,
        spec_name=run.spec_name,
        dps=run.dps,
        hps=run.hps,
        ilvl=run.ilvl,
        duration=run.duration,
        deaths=run.deaths,
        interrupts=run.interrupts,
        dispels=run.dispels,
        avoidable_damage_taken=run.avoidable_damage_taken,
        damage_taken_total=run.damage_taken_total,
        casts_total=run.casts_total,
        cooldown_usage_pct=run.cooldown_usage_pct,
        timed=run.timed,
        logged_at=run.logged_at,
        rating=run.rating,
        average_item_level=run.average_item_level,
        keystone_affixes=run.keystone_affixes,
        healing_received=run.healing_received,
        cc_casts=run.cc_casts,
        critical_interrupts=run.critical_interrupts,
        avoidable_deaths=run.avoidable_deaths,
        party_comp=run.party_comp,
    )


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "umbra-score-engine"}


_DOWNLOAD_TARGET_URL = "https://wowumbra.gg/Umbra.zip"


@app.get("/api/addon/download")
@limiter.limit(settings.rate_limit_public)
def download_addon(request: Request, session: Session = Depends(get_session)):
    """Log an addon-download attempt, then 302 to the static zip on Vercel.

    The 302 lets the CDN serve the actual bytes. We just record one row per
    request. IP is salted-hashed so we can dedup uniques in stats without
    storing raw PII; the salt is the configured API key (already a secret).
    """
    ip = request.client.host if request.client else None
    ip_hash: str | None = None
    if ip:
        salt = settings.api_key or "umbra-fallback-salt"
        ip_hash = hashlib.sha256(f"{ip}:{salt}".encode()).hexdigest()
    ua = (request.headers.get("user-agent") or "")[:500]
    try:
        session.add(AddonDownload(ip_hash=ip_hash, user_agent=ua))
        session.commit()
    except Exception as e:
        logger.warning("Failed to log addon download: %s", e)
        session.rollback()
    return RedirectResponse(_DOWNLOAD_TARGET_URL, status_code=302)


@app.get("/api/admin/download-stats", dependencies=[Depends(require_api_key)])
def download_stats(session: Session = Depends(get_session)):
    """Aggregate download counts: total, 24h / 7d / 30d windows, and a
    day-bucketed series for the last 30 days. `unique_ips_last_30d`
    counts distinct ip_hash values in the window, giving a sanity check
    against bots reloading the endpoint."""
    now = datetime.utcnow()
    h24 = now - timedelta(hours=24)
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    def _count(since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(AddonDownload)
        if since:
            stmt = stmt.where(AddonDownload.downloaded_at >= since)
        return int(session.execute(stmt).scalar() or 0)

    unique_30d = int(session.execute(
        select(func.count(func.distinct(AddonDownload.ip_hash)))
        .where(AddonDownload.downloaded_at >= d30)
        .where(AddonDownload.ip_hash.is_not(None))
    ).scalar() or 0)

    daily_rows = session.execute(
        select(
            func.date_trunc("day", AddonDownload.downloaded_at).label("day"),
            func.count().label("n"),
        )
        .where(AddonDownload.downloaded_at >= d30)
        .group_by("day")
        .order_by("day")
    ).all()

    return {
        "total": _count(),
        "last_24h": _count(h24),
        "last_7d": _count(d7),
        "last_30d": _count(d30),
        "unique_ips_last_30d": unique_30d,
        "daily_series": [
            {"day": d.date().isoformat() if hasattr(d, "date") else str(d),
             "count": int(n)}
            for d, n in daily_rows
        ],
    }


@app.get("/api/player/{region}/{realm}/{name}", response_model=PlayerScoreResponse)
@limiter.limit(settings.rate_limit_player_lookup)
def get_player_score(
    request: Request,
    region: str,
    realm: str,
    name: str,
    refresh: bool = False,
    x_api_key: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    """Look up a player's Umbra score. Triggers ingestion if not cached.

    `refresh=true` forces a re-ingest from WCL and requires an admin API key.
    """
    if refresh:
        # Force-refresh is admin-only to prevent WCL quota abuse.
        require_api_key(x_api_key)

    name, realm, region = _canonical_identity(name, realm, region)

    if not refresh:
        player = _find_player(session, region, realm, name)
        if player and player.scores:
            primary = next((s for s in player.scores if s.primary_role), player.scores[0])
            return PlayerScoreResponse(
                name=player.name,
                realm=player.realm,
                region=player.region,
                role=primary.role.value,
                grade=primary.overall_grade,
                category_scores=primary.category_scores,
                runs_analyzed=primary.runs_analyzed,
            )

    # Not cached or refresh requested — ingest from WCL
    ingest_result = ingest_player(session, name, realm, region)
    if not ingest_result.player:
        raise HTTPException(status_code=404, detail="Character not found on Warcraft Logs")

    player = ingest_result.player
    stmt = (
        select(Player)
        .where(Player.id == player.id)
        .options(selectinload(Player.scores))
    )
    player = session.execute(stmt).scalar_one()

    if not player.scores:
        raise HTTPException(
            status_code=404,
            detail="Not enough M+ runs to grade (minimum 3 required)",
        )

    primary = next((s for s in player.scores if s.primary_role), player.scores[0])
    return PlayerScoreResponse(
        name=player.name,
        realm=player.realm,
        region=player.region,
        role=primary.role.value,
        grade=primary.overall_grade,
        category_scores=primary.category_scores,
        runs_analyzed=primary.runs_analyzed,
    )


@app.post(
    "/api/ingest",
    response_model=IngestResponse,
    dependencies=[Depends(require_api_key)],
)
def bulk_ingest(
    request: IngestRequest,
    session: Session = Depends(get_session),
):
    """Bulk ingest a list of players from WCL. Admin-only (requires X-API-Key)."""
    player_dicts = [p.model_dump() for p in request.players]
    results = ingest_batch(session, player_dicts)
    return IngestResponse(
        ingested=len(results),
        failed=len(player_dicts) - len(results),
    )


_WCL_REPORT_URL_RE = __import__("re").compile(r"/reports/(?:a:)?([A-Za-z0-9]{16})")
_WCL_BARE_CODE_RE = __import__("re").compile(r"^[A-Za-z0-9]{16}$")


def _extract_report_code(raw: str) -> str | None:
    """Accept either a full WCL URL (any of the report path shapes) or a
    bare 16-char report code. Return the code, or None if we can't find one."""
    s = raw.strip()
    m = _WCL_REPORT_URL_RE.search(s)
    if m:
        return m.group(1)
    if _WCL_BARE_CODE_RE.match(s):
        return s
    return None


@app.post("/api/player/claim", response_model=ClaimResponse)
@limiter.limit(settings.rate_limit_player_lookup)
def claim_player(
    request: Request,
    body: ClaimRequest,
    session: Session = Depends(get_session),
):
    """Visitor-facing 'this is me' flow. When WCL's character() lookup returns
    the wrong entity for a common name, the user pastes a report URL from one
    of their actual logs. We identify their character within that report's
    playerDetails (authoritative: class comes from per-fight 'type') and
    ingest via report_codes mode, which bypasses the broken character lookup.

    Public (rate-limited) — no API key required. The caller can't pollute
    data since we still only store players that appear in a real WCL log.
    """
    from app.scoring.spec_to_class import class_id_from_name
    from app.wcl.client import wcl_client

    name, realm, region = _canonical_identity(body.name, body.realm, body.region)
    code = _extract_report_code(body.report_url_or_code)
    if not code:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "bad_report_url",
                "message": "Could not find a WCL report code in that input. "
                           "Paste the full log URL (e.g. warcraftlogs.com/reports/ABC123…) "
                           "or just the 16-character code.",
            },
        )

    fights = wcl_client.get_report_fights(code)
    if not fights:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "no_mplus_fights",
                "message": "That report exists but has no M+ fights — "
                           "pick a log from a Mythic+ run that includes your character.",
            },
        )

    fight_ids = [f["id"] for f in fights]
    rd = wcl_client.get_report_player_data(code, fight_ids)
    pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {}) if rd else {}

    matched_name: str | None = None
    matched_class: str | None = None
    target_lower = name.lower()
    for role_key in ("tanks", "healers", "dps"):
        for p in pd.get(role_key, []) or []:
            if (p.get("name") or "").lower() == target_lower:
                matched_name = p.get("name")
                matched_class = p.get("type") or p.get("icon")
                break
        if matched_name:
            break

    if not matched_name:
        players_in_log = sorted({
            p.get("name")
            for role_key in ("tanks", "healers", "dps")
            for p in pd.get(role_key, []) or []
            if p.get("name")
        })
        raise HTTPException(
            status_code=404,
            detail={
                "code": "name_not_in_report",
                "message": f"No character named '{name}' in that report. "
                           f"Pick a log where your character is in the group.",
                "players_in_log": list(players_in_log),
            },
        )

    class_id = class_id_from_name(matched_class)
    result = ingest_player(
        session, name, realm, region,
        class_hint=class_id,
        report_codes=[code],
    )
    if not result.player:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ingest_failed",
                "reason": result.reason,
                "message": "Found your character in that report, but WCL "
                           "didn't return fight data we could score. Try another log.",
            },
        )

    runs_count = len(result.player.runs) if result.player.runs else 0
    return ClaimResponse(
        ok=True,
        report_code=code,
        class_name=matched_class,
        class_id=class_id,
        runs_ingested=runs_count,
    )


@app.get("/api/debug/wcl-character", dependencies=[Depends(require_api_key)])
def debug_wcl_character(
    region: str,
    realm: str,
    name: str,
):
    """Admin diagnostic. Returns the raw WCL character(name, serverSlug,
    serverRegion) response so we can see which entity WCL is matching
    (classID, internal id, recent reports). Useful when the user's actual
    character class on WCL disagrees with what our ingest stores —
    confirms whether WCL is returning a different actor than the one
    the user thinks they're looking up."""
    from app.wcl.client import wcl_client

    name_c, realm_c, region_c = validate_player_identity(name, realm, region)
    server_slug = realm_c.lower().replace("'", "").replace(" ", "-")
    char = wcl_client.get_character_with_reports(
        name=name_c,
        server_slug=server_slug,
        server_region=region_c.lower(),
        limit=10,
    )
    if not char:
        return {"found": False, "name": name_c, "realm": realm_c, "region": region_c}
    reports = char.get("recentReports", {}).get("data", [])
    return {
        "found": True,
        "wcl_id": char.get("id"),
        "name": char.get("name"),
        "classID": char.get("classID"),
        "server_slug": char.get("server", {}).get("slug"),
        "server_region": char.get("server", {}).get("region", {}).get("slug"),
        "recent_reports_count": len(reports),
        "recent_reports": [
            {
                "code": r.get("code"),
                "title": r.get("title"),
                "zone_name": r.get("zone", {}).get("name"),
                "startTime": r.get("startTime"),
            }
            for r in reports
        ],
    }


@app.post("/api/admin/delete-player-runs", dependencies=[Depends(require_api_key)])
def delete_player_runs(
    region: str, realm: str, name: str,
    report_code: str | None = None,
    session: Session = Depends(get_session),
):
    """Delete stored DungeonRuns for a player so a re-ingest re-parses
    them fresh. Use when our parsing logic changed and we need to pick
    up the new values on existing logs.

    If report_code is given, only delete runs from that report. Otherwise
    delete all runs for the player. Also clears PlayerScore rows (they'll
    be regenerated on next ingest once min_runs_for_grade is hit again).
    """
    name_c, realm_c, region_c = validate_player_identity(name, realm, region)
    player = _find_player(session, region_c, realm_c, name_c)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    run_query = select(DungeonRun).where(DungeonRun.player_id == player.id)
    if report_code:
        run_query = run_query.where(DungeonRun.wcl_report_id == report_code)
    runs = list(session.execute(run_query).scalars())
    for r in runs:
        session.delete(r)

    scores = list(session.execute(
        select(PlayerScore).where(PlayerScore.player_id == player.id)
    ).scalars())
    for s in scores:
        session.delete(s)

    session.commit()
    return {
        "player_id": player.id,
        "runs_deleted": len(runs),
        "scores_deleted": len(scores),
        "report_code_filter": report_code,
    }


@app.post("/api/admin/merge-duplicates", dependencies=[Depends(require_api_key)])
def merge_duplicate_players(
    region: str, realm: str, name: str,
    session: Session = Depends(get_session),
):
    """For a (region, realm, name) tuple, collapse multiple Player rows into
    the one that has the most DungeonRuns. All runs + scores from the losers
    get re-pointed at the winner; losers are deleted. Idempotent.

    Needed for cleanup when earlier bugs created duplicate rows (e.g.
    report-code mode before the wcl_id-agnostic lookup fix).
    """
    name_c, realm_c, region_c = validate_player_identity(name, realm, region)
    target_key = "".join(c.lower() for c in realm_c if c.isalnum())

    candidates = list(session.execute(
        select(Player).where(
            Player.name.ilike(name_c),
            Player.region.ilike(region_c),
        )
    ).scalars())
    # Filter to same-realm (alphanumeric key match).
    matching = [
        p for p in candidates
        if "".join(c.lower() for c in p.realm if c.isalnum()) == target_key
    ]
    if len(matching) <= 1:
        return {"merged": 0, "kept_id": matching[0].id if matching else None}

    # Winner = player with the most runs; tie-break on most scores, then lowest id.
    def _score(p: Player):
        return (len(p.runs), len(p.scores), -p.id)
    matching.sort(key=_score, reverse=True)
    winner, losers = matching[0], matching[1:]

    for loser in losers:
        for run in list(loser.runs):
            run.player_id = winner.id
        for score in list(loser.scores):
            score.player_id = winner.id
    session.flush()
    for loser in losers:
        session.delete(loser)
    session.commit()

    return {
        "merged": len(losers),
        "kept_id": winner.id,
        "kept_runs": len(winner.runs),
        "deleted_ids": [l.id for l in losers],
    }


@app.post("/api/admin/merge-all-duplicates", dependencies=[Depends(require_api_key)])
def merge_all_duplicate_players(session: Session = Depends(get_session)):
    """Scan every Player row, group by (name_lower, realm_key, region_upper),
    and merge each group into its most-run-heavy survivor. Returns per-group
    stats. Idempotent — safe to re-run.

    Intended as a one-shot cleanup after fixing the upsert bug that was
    creating duplicates; can also run on a schedule if new bugs creep in.
    """
    from sqlalchemy import update

    # Load every Player eager-loading runs + scores so the sort keys
    # (len(p.runs), len(p.scores)) don't trigger lazy-load queries mid-loop.
    players = list(session.execute(
        select(Player).options(
            selectinload(Player.runs),
            selectinload(Player.scores),
        )
    ).scalars())

    # Group by identity. Key: (name.lower(), realm_key, region.upper()).
    groups: dict[tuple[str, str, str], list[Player]] = {}
    for p in players:
        key = (
            (p.name or "").lower(),
            "".join(c.lower() for c in (p.realm or "") if c.isalnum()),
            (p.region or "").upper(),
        )
        groups.setdefault(key, []).append(p)

    reports: list[dict] = []
    total_merged = 0
    errors: list[dict] = []

    def _score(p: Player):
        return (len(p.runs), len(p.scores), -p.id)

    for key, matching in groups.items():
        if len(matching) <= 1:
            continue
        matching.sort(key=_score, reverse=True)
        winner, losers = matching[0], matching[1:]
        loser_ids = [l.id for l in losers]

        # Re-point child rows via bulk UPDATE statements so we don't depend
        # on the relationship collection being complete. Commit per group
        # so one bad group doesn't kill the whole operation.
        try:
            session.execute(
                update(DungeonRun)
                .where(DungeonRun.player_id.in_(loser_ids))
                .values(player_id=winner.id)
            )
            session.execute(
                update(PlayerScore)
                .where(PlayerScore.player_id.in_(loser_ids))
                .values(player_id=winner.id)
            )
            # Force SA to forget its cached `loser.runs` / `loser.scores`
            # collections. Without this, session.delete(loser) tries to
            # cascade-nullify the rows we just re-pointed to the winner
            # (which fails the NOT NULL constraint on player_id).
            for loser in losers:
                session.expire(loser)
            for loser in losers:
                session.delete(loser)
            session.commit()
            total_merged += len(losers)
            reports.append({
                "name": winner.name,
                "realm": winner.realm,
                "region": winner.region,
                "kept_id": winner.id,
                "deleted_ids": loser_ids,
            })
        except Exception as e:
            session.rollback()
            errors.append({
                "name": winner.name,
                "realm": winner.realm,
                "region": winner.region,
                "error": str(e),
            })

    return {
        "groups_scanned": len(groups),
        "groups_merged": len(reports),
        "total_losers_deleted": total_merged,
        "merges": reports,
        "errors": errors,
    }


@app.get("/api/debug/wcl-buffs", dependencies=[Depends(require_api_key)])
def debug_wcl_buffs(code: str, player: str):
    """Return the BuffsTable auras for a player in a report's first M+ fight.
    Lets us verify which buff IDs WCL records for cooldowns we care about.
    If a CD in cooldowns.py doesn't appear with the expected id, that's our
    bug (wrong id) or a genuine 'player never cast it' signal."""
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    if not fights:
        return {"error": "no M+ fights", "code": code}

    # Search every fight for the player (they may not be in fight #1).
    found_fight_id = None
    actor_id = None
    tried = []
    for f in fights:
        fid = f.get("id")
        rd = wcl_client.get_report_player_data(code, [fid])
        pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {})
        names_here = []
        for role in ("tanks", "healers", "dps"):
            for p in pd.get(role, []):
                names_here.append(p.get("name"))
                if (p.get("name") or "").lower() == player.lower():
                    actor_id = p.get("id")
                    found_fight_id = fid
                    break
            if actor_id:
                break
        tried.append({"fight_id": fid, "names": names_here})
        if actor_id:
            break

    if actor_id is None:
        return {"error": "player not in any fight", "fights_inspected": tried}

    auras_data = wcl_client.get_player_auras(code, [found_fight_id], actor_id)
    buffs = auras_data.get("buffsTable", {}).get("data", {}).get("auras", [])
    sorted_buffs = sorted(buffs, key=lambda b: b.get("totalUses", 0), reverse=True)
    return {
        "code": code,
        "fight_id": found_fight_id,
        "player": player,
        "actor_id": actor_id,
        "buff_count": len(buffs),
        "buffs": [
            {"guid": b.get("guid"), "name": b.get("name"),
             "totalUses": b.get("totalUses"), "totalUptime": b.get("totalUptime")}
            for b in sorted_buffs[:60]
        ],
    }


@app.get("/api/admin/sample-dungeon-mechanics", dependencies=[Depends(require_api_key)])
def sample_dungeon_mechanics(
    encounter_id: int,
    top_n: int = Query(default=10, le=20),
    consensus_pct: float = Query(default=30.0, ge=0, le=100),
):
    """Sample top-N WCL logs for a dungeon encounter, aggregate damage-
    taken across them, and return abilities that appear in `consensus_pct`%
    or more of the logs. The cross-log filter is the key trick: party-spec
    abilities (Warlock procs polluting one log, Paladin procs polluting
    another) only survive aggregation if they recur, while real boss
    mechanics show up everywhere. Use this output as the input to
    populate `avoidable_abilities` in dungeon modules.

    Writes nothing to our DB. Pure read against WCL.
    """
    from collections import defaultdict
    from app.wcl.client import wcl_client

    # 1. Find the top logs for this encounter.
    top_logs = wcl_client.get_top_logs_for_encounter(encounter_id, metric="speed", limit=top_n)
    if not top_logs:
        return {"error": "no rankings returned for this encounter", "encounter_id": encounter_id}

    # 2. For each log, pull damage-taken EVENTS filtered to NPC/Boss
    # sources only (the table view leaks player abilities and Aug
    # Evoker buff aura noise that we can't filter post-hoc by
    # ability ID alone).
    appearances: dict[int, set] = defaultdict(set)
    total_damage: dict[int, int] = defaultdict(int)
    name_for_id: dict[int, str] = {}
    successful_logs = 0
    for log in top_logs:
        try:
            per_ability = wcl_client.get_damage_taken_from_npcs(
                log["report_code"], [log["fight_id"]]
            )
        except Exception:
            continue
        if not per_ability:
            continue
        successful_logs += 1
        for gid, slot in per_ability.items():
            appearances[gid].add(log["report_code"])
            total_damage[gid] += int(slot.get("total") or 0)
            name_for_id[gid] = slot.get("name") or name_for_id.get(gid, "?")

    if successful_logs == 0:
        return {"error": "fetched 0 successful logs", "logs_attempted": len(top_logs)}

    # 3. Filter by consensus threshold and rank by total damage.
    threshold = (consensus_pct / 100.0) * successful_logs
    consensus = [
        {
            "guid": gid,
            "name": name_for_id[gid],
            "logs_seen_in": len(appearances[gid]),
            "logs_pct": round(100 * len(appearances[gid]) / successful_logs, 1),
            "total_damage": total_damage[gid],
        }
        for gid in appearances
        if len(appearances[gid]) >= threshold
    ]
    consensus.sort(key=lambda x: x["total_damage"], reverse=True)

    return {
        "encounter_id": encounter_id,
        "logs_sampled": successful_logs,
        "consensus_threshold_pct": consensus_pct,
        "abilities_passing_threshold": len(consensus),
        "abilities": consensus[:30],
    }


@app.get("/api/debug/wcl-interrupts", dependencies=[Depends(require_api_key)])
def debug_wcl_interrupts(code: str, fight_id: int):
    """Return the raw interruptTable payload for one specific fight so we
    can see the shape WCL returns. Used to debug sample-dungeon-interrupts."""
    from app.wcl.client import wcl_client
    query = """
    query($code: String!, $fightIDs: [Int!]!) {
      reportData {
        report(code: $code) {
          interruptTable: table(fightIDs: $fightIDs, dataType: Interrupts)
        }
      }
    }
    """
    data = wcl_client.query(query, {"code": code, "fightIDs": [fight_id]})
    return {
        "code": code,
        "fight_id": fight_id,
        "raw": data.get("reportData", {}).get("report", {}).get("interruptTable"),
    }


@app.get("/api/admin/sample-dungeon-interrupts", dependencies=[Depends(require_api_key)])
def sample_dungeon_interrupts(
    encounter_id: int,
    top_n: int = Query(default=20, le=30),
    consensus_pct: float = Query(default=50.0, ge=0, le=100),
):
    """Sample top-N WCL logs for a dungeon encounter, aggregate per-spell
    interrupt counts across them, and return spells that appear in
    `consensus_pct`% or more of the logs. Use this output as the input
    to populate `critical_interrupts` in dungeon modules — these are
    the casts top parties consistently target for kicks.

    Writes nothing to our DB. Pure read against WCL.
    """
    from collections import defaultdict
    from app.wcl.client import wcl_client

    top_logs = wcl_client.get_top_logs_for_encounter(encounter_id, metric="speed", limit=top_n)
    if not top_logs:
        return {"error": "no rankings returned for this encounter", "encounter_id": encounter_id}

    # InterruptTable shape (from queries.py REPORT_PLAYER_DATA):
    #   entries: [{ guid, name, total, entries: [{ details: [...] }] }]
    # Top-level guid is the ABILITY that was interrupted; total is the
    # party-wide count across the fight. Perfect for cross-log aggregation.
    interrupt_query = """
    query($code: String!, $fightIDs: [Int!]!) {
      reportData {
        report(code: $code) {
          interruptTable: table(fightIDs: $fightIDs, dataType: Interrupts)
        }
      }
    }
    """

    appearances: dict[int, set] = defaultdict(set)
    total_kicks: dict[int, int] = defaultdict(int)
    name_for_id: dict[int, str] = {}
    successful_logs = 0
    for log in top_logs:
        try:
            data = wcl_client.query(
                interrupt_query,
                {"code": log["report_code"], "fightIDs": [log["fight_id"]]},
            )
        except Exception:
            continue
        table = (
            data.get("reportData", {}).get("report", {}).get("interruptTable", {})
            or {}
        )
        entries = (table.get("data") or {}).get("entries") or []
        if not entries:
            continue
        successful_logs += 1
        for entry in entries:
            gid = entry.get("guid")
            if not isinstance(gid, int):
                continue
            appearances[gid].add(log["report_code"])
            total_kicks[gid] += int(entry.get("total") or 0)
            name_for_id[gid] = entry.get("name") or name_for_id.get(gid, "?")

    if successful_logs == 0:
        return {"error": "fetched 0 successful logs", "logs_attempted": len(top_logs)}

    threshold = (consensus_pct / 100.0) * successful_logs
    consensus = [
        {
            "guid": gid,
            "name": name_for_id[gid],
            "logs_seen_in": len(appearances[gid]),
            "logs_pct": round(100 * len(appearances[gid]) / successful_logs, 1),
            "total_kicks": total_kicks[gid],
        }
        for gid in appearances
        if len(appearances[gid]) >= threshold
    ]
    consensus.sort(key=lambda x: x["total_kicks"], reverse=True)

    return {
        "encounter_id": encounter_id,
        "logs_sampled": successful_logs,
        "consensus_threshold_pct": consensus_pct,
        "abilities_passing_threshold": len(consensus),
        "abilities": consensus[:40],
    }


@app.get("/api/admin/sample-spec-cooldowns", dependencies=[Depends(require_api_key)])
def sample_spec_cooldowns(
    class_id: int = Query(..., ge=1, le=13),
    spec: str = Query(..., min_length=2, max_length=30),
    encounter_id: int = Query(default=10658),  # Pit of Saron — high traffic
    top_n: int = Query(default=10, le=20),
    consensus_pct: float = Query(default=80.0, ge=0, le=100),
    metric: str = Query(default="dps", pattern="^(dps|hps)$"),
):
    """Sample top-N players of a (class, spec) on a representative
    encounter, fetch their buffs from their top log, aggregate which
    buffs they consistently have, and return ones present in
    `consensus_pct`% or more of the sample. That's the consensus
    cooldown list — if 80% of top Frost Mages all have buff X, X is a
    real major CD they're talented into; if only 20% have it, it's a
    talent choice we shouldn't track as universal.

    Writes nothing to our DB. Pure read against WCL.
    """
    from collections import defaultdict
    from app.wcl.client import wcl_client
    from app.scoring.spec_to_class import CLASS_NAME_TO_ID

    # Reverse lookup: class_id -> WCL className. Pick the no-space variant
    # since WCL's API expects single-token names ("DemonHunter", not
    # "Demon Hunter").
    class_name = next(
        (k for k, v in CLASS_NAME_TO_ID.items() if v == class_id and " " not in k),
        None,
    )
    if not class_name:
        raise HTTPException(status_code=400, detail=f"Unknown class_id {class_id}")

    top_chars = wcl_client.get_top_characters_for_spec(
        encounter_id=encounter_id,
        class_name=class_name,
        spec_name=spec,
        metric=metric,
        limit=top_n,
    )
    if not top_chars:
        return {
            "error": "no rankings returned",
            "class_name": class_name, "spec": spec, "encounter_id": encounter_id,
        }

    # For each top character, resolve their actor_id in the fight, then
    # pull their buffs aura table and tally each buff_id's appearance.
    appearances: dict[int, set] = defaultdict(set)
    name_for_id: dict[int, str] = {}
    sample_uses: dict[int, list[int]] = defaultdict(list)
    successful = 0
    failures: list[dict] = []
    for ch in top_chars:
        report_code = ch["report_code"]
        fight_id = ch["fight_id"]
        char_name = ch["name"]
        try:
            rd = wcl_client.get_report_player_data(report_code, [fight_id])
            pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {}) if rd else {}
            actor_id = None
            for role in ("tanks", "healers", "dps"):
                for p in pd.get(role, []) or []:
                    if (p.get("name") or "").lower() == char_name.lower():
                        actor_id = p.get("id")
                        break
                if actor_id:
                    break
            if actor_id is None:
                failures.append({"name": char_name, "reason": "actor_id not found"})
                continue
            auras_data = wcl_client.get_player_auras(report_code, [fight_id], actor_id)
        except Exception as e:
            failures.append({"name": char_name, "reason": str(e)})
            continue

        buffs = auras_data.get("buffsTable", {}).get("data", {}).get("auras", []) or []
        successful += 1
        for b in buffs:
            gid = b.get("guid")
            if not isinstance(gid, int):
                continue
            appearances[gid].add(char_name.lower())
            name_for_id[gid] = b.get("name") or name_for_id.get(gid, "?")
            uses = b.get("totalUses") or 0
            sample_uses[gid].append(int(uses))

    if successful == 0:
        return {
            "error": "fetched 0 successful character buff sets",
            "class_name": class_name, "spec": spec,
            "characters_attempted": len(top_chars),
            "failures": failures,
        }

    threshold = (consensus_pct / 100.0) * successful
    consensus = [
        {
            "buff_id": gid,
            "name": name_for_id[gid],
            "players_seen_in": len(appearances[gid]),
            "players_pct": round(100 * len(appearances[gid]) / successful, 1),
            "median_uses": sorted(sample_uses[gid])[len(sample_uses[gid]) // 2],
            "max_uses": max(sample_uses[gid]),
        }
        for gid in appearances
        if len(appearances[gid]) >= threshold
    ]
    # Sort by median uses (high → low). Real CDs get used multiple times
    # per fight; passive procs get used hundreds of times. Both will pass
    # the consensus filter; the rate distinguishes them when reviewed.
    consensus.sort(key=lambda x: x["median_uses"])

    return {
        "class_id": class_id,
        "class_name": class_name,
        "spec": spec,
        "encounter_id": encounter_id,
        "characters_sampled": successful,
        "characters_attempted": len(top_chars),
        "consensus_threshold_pct": consensus_pct,
        "buffs_passing_threshold": len(consensus),
        "buffs": consensus[:50],
        "failures": failures,
    }


@app.get("/api/admin/cd-audit-coverage", dependencies=[Depends(require_api_key)])
def cd_audit_coverage(session: Session = Depends(get_session)):
    """Run the CD audit across every (class_id, spec) we have data for.

    Picks one representative DungeonRun per unique (class_id, spec) —
    the most recent — and runs the buff audit against it. Returns a
    per-spec summary so we can see in a single response which specs
    need `cooldowns.py` cleanup first. Slow (1 WCL round-trip per
    unique spec); admin-only, no rate-limit.

    Each result contains the same three buckets as /api/debug/wcl-cd-audit
    plus a sample_log field pointing at the source run."""
    from app.scoring.cooldowns import SPEC_MAJOR_COOLDOWNS
    from app.wcl.client import wcl_client

    # Pick one representative row per (player_id, spec_name) — most recent.
    # Then de-duplicate across players per (class_id, spec_name).
    runs = list(session.execute(
        select(
            DungeonRun.id,
            DungeonRun.player_id,
            DungeonRun.spec_name,
            DungeonRun.wcl_report_id,
            DungeonRun.fight_id,
            DungeonRun.logged_at,
        ).order_by(DungeonRun.logged_at.desc())
    ))

    # Build (class_id, spec) -> first encountered run (newest first).
    seen: dict[tuple[int, str], dict] = {}
    for r in runs:
        player = session.get(Player, r.player_id)
        if not player:
            continue
        key = (player.class_id, r.spec_name)
        if key in seen:
            continue
        seen[key] = {
            "player_name": player.name,
            "realm": player.realm,
            "region": player.region,
            "class_id": player.class_id,
            "spec": r.spec_name,
            "report_code": r.wcl_report_id,
            "fight_id": r.fight_id,
            "logged_at": r.logged_at,
        }

    results: list[dict] = []
    for key, sample in seen.items():
        class_id, spec = key
        tracked = SPEC_MAJOR_COOLDOWNS.get((class_id, spec), [])
        tracked_ids = {cd[0] for cd in tracked}

        report_code = sample["report_code"]
        fight_id = sample["fight_id"]
        player_name = sample["player_name"]

        # Resolve actor_id via playerDetails for this single fight.
        actor_id: int | None = None
        try:
            rd = wcl_client.get_report_player_data(report_code, [fight_id])
            pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {}) if rd else {}
            for role in ("tanks", "healers", "dps"):
                for p in pd.get(role, []) or []:
                    if (p.get("name") or "").lower() == player_name.lower():
                        actor_id = p.get("id")
                        break
                if actor_id:
                    break
        except Exception as e:
            results.append({**sample, "error": f"player_data fetch failed: {e}"})
            continue

        if actor_id is None:
            results.append({**sample, "error": "player not in fight playerDetails"})
            continue

        try:
            auras_data = wcl_client.get_player_auras(report_code, [fight_id], actor_id)
        except Exception as e:
            results.append({**sample, "error": f"auras fetch failed: {e}"})
            continue

        buffs = auras_data.get("buffsTable", {}).get("data", {}).get("auras", []) or []
        observed = {b.get("guid"): b for b in buffs if isinstance(b.get("guid"), int)}

        tracked_and_seen = []
        tracked_never_seen = []
        for buff_id, name, expected_uptime in tracked:
            obs = observed.get(buff_id)
            if obs:
                tracked_and_seen.append({
                    "buff_id": buff_id, "our_name": name,
                    "wcl_name": obs.get("name"),
                    "total_uses": obs.get("totalUses"),
                })
            else:
                tracked_never_seen.append({"buff_id": buff_id, "our_name": name})

        untracked = [b for b in buffs if b.get("guid") not in tracked_ids]
        untracked.sort(key=lambda b: b.get("totalUses", 0), reverse=True)
        seen_not_tracked = [
            {"buff_id": b.get("guid"), "name": b.get("name"),
             "total_uses": b.get("totalUses")}
            for b in untracked[:10]
        ]

        results.append({
            **sample,
            "tracked_count": len(tracked),
            "tracked_and_seen": tracked_and_seen,
            "tracked_never_seen": tracked_never_seen,
            "seen_not_tracked": seen_not_tracked,
        })

    # Sort: highest "suspect" count first so worst-off specs surface at top.
    results.sort(
        key=lambda r: len(r.get("tracked_never_seen", [])) if "tracked_never_seen" in r else 0,
        reverse=True,
    )
    return {"unique_specs": len(results), "results": results}


@app.get("/api/debug/wcl-cd-audit", dependencies=[Depends(require_api_key)])
def debug_wcl_cd_audit(code: str, player: str):
    """Audit our tracked major cooldowns against what a player actually used.

    Resolves the player's class/spec from the first M+ fight's
    playerDetails, then compares our `SPEC_MAJOR_COOLDOWNS[(class_id,
    spec)]` list to the player's BuffsTable for that fight. Returns
    three buckets:

      - `tracked_and_seen`  : tracked CDs with >=1 use. Validated.
      - `tracked_never_seen`: tracked CDs with 0 uses. Either our buff ID
                              is wrong OR the player didn't talent into
                              this CD. Needs a human judgment call.
      - `seen_not_tracked`  : top buffs (by totalUses) not in our list.
                              Candidates to add if they're major CDs we
                              missed.

    Audit workflow: paste a recent +M+ log, read the output, update
    `app/scoring/cooldowns.py` accordingly, commit. Repeat per spec as
    logs arrive.
    """
    from app.scoring.cooldowns import SPEC_MAJOR_COOLDOWNS
    from app.scoring.spec_to_class import class_id_from_name
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    if not fights:
        return {"error": "no M+ fights in report", "code": code}

    # Find the player across any fight in the report. Use the first match.
    found_fight_id: int | None = None
    actor_id: int | None = None
    resolved_class_name: str | None = None
    resolved_spec: str | None = None
    tried: list[dict] = []
    for f in fights:
        fid = f.get("id")
        rd = wcl_client.get_report_player_data(code, [fid])
        pd = (rd or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {})
        names_here: list[str] = []
        for role in ("tanks", "healers", "dps"):
            for p in pd.get(role, []) or []:
                names_here.append(p.get("name"))
                if (p.get("name") or "").lower() == player.lower():
                    actor_id = p.get("id")
                    resolved_class_name = p.get("type") or p.get("class")
                    resolved_spec = p.get("specs", [{}])[0].get("spec") if p.get("specs") else None
                    if not resolved_spec:
                        resolved_spec = p.get("icon", "").split("-")[-1] or None
                    found_fight_id = fid
                    break
            if actor_id:
                break
        tried.append({"fight_id": fid, "names": names_here})
        if actor_id:
            break

    if actor_id is None:
        return {"error": "player not in any fight", "fights_inspected": tried}

    class_id = class_id_from_name(resolved_class_name)
    if not class_id:
        return {
            "error": f"could not resolve class_id from '{resolved_class_name}'",
            "player": player,
        }

    tracked = SPEC_MAJOR_COOLDOWNS.get((class_id, resolved_spec or ""), [])
    tracked_ids = {cd[0] for cd in tracked}

    auras_data = wcl_client.get_player_auras(code, [found_fight_id], actor_id)
    buffs = auras_data.get("buffsTable", {}).get("data", {}).get("auras", []) or []

    # Index observed buffs by guid for fast lookup.
    observed: dict[int, dict] = {}
    for b in buffs:
        gid = b.get("guid")
        if isinstance(gid, int):
            observed[gid] = b

    # Bucket 1: tracked CDs that appeared (validated our ID + player talented in).
    tracked_and_seen: list[dict] = []
    # Bucket 2: tracked CDs that never appeared (our ID wrong OR player didn't talent).
    tracked_never_seen: list[dict] = []
    for buff_id, name, expected_uptime in tracked:
        obs = observed.get(buff_id)
        if obs:
            tracked_and_seen.append({
                "buff_id": buff_id,
                "our_name": name,
                "wcl_name": obs.get("name"),
                "total_uses": obs.get("totalUses"),
                "total_uptime_ms": obs.get("totalUptime"),
                "expected_uptime_pct": expected_uptime,
            })
        else:
            tracked_never_seen.append({
                "buff_id": buff_id,
                "our_name": name,
                "expected_uptime_pct": expected_uptime,
            })

    # Bucket 3: observed buffs we don't track, sorted by frequency. Limit to
    # 15 so output stays skimmable — real major CDs cluster near the top.
    untracked = [b for b in buffs if b.get("guid") not in tracked_ids]
    untracked.sort(key=lambda b: b.get("totalUses", 0), reverse=True)
    seen_not_tracked = [
        {
            "buff_id": b.get("guid"),
            "name": b.get("name"),
            "total_uses": b.get("totalUses"),
            "total_uptime_ms": b.get("totalUptime"),
        }
        for b in untracked[:15]
    ]

    return {
        "code": code,
        "fight_id": found_fight_id,
        "player": player,
        "class_id": class_id,
        "class_name": resolved_class_name,
        "spec": resolved_spec,
        "tracked_count": len(tracked),
        "observed_buff_count": len(buffs),
        "tracked_and_seen": tracked_and_seen,
        "tracked_never_seen": tracked_never_seen,
        "seen_not_tracked": seen_not_tracked,
    }


@app.get("/api/debug/wcl-casts", dependencies=[Depends(require_api_key)])
def debug_wcl_casts(code: str, player: str):
    """Return the per-ability casts breakdown for a player in a report's
    first M+ fight. Lets us see exactly which ability IDs WCL reports —
    critical for debugging 'cc_casts=0' when the player swears they cast
    Leg Sweep / Paralysis / Capacitor Totem etc. If the ID WCL returns
    differs from what our cc_abilities.py has, that's our bug."""
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    if not fights:
        return {"error": "no M+ fights in report", "code": code}

    fight_id = fights[0]["id"]
    rd = wcl_client.get_report_player_data(code, [fight_id])
    if not rd:
        return {"error": "no report_data", "code": code, "fight_id": fight_id}

    casts = rd.get("castsTable", {}).get("data", {}).get("entries", [])
    target = None
    for entry in casts:
        if entry.get("name", "").lower() == player.lower():
            target = entry
            break
    if target is None:
        return {
            "error": "player not in casts table",
            "players_in_casts": [e.get("name") for e in casts],
        }
    abilities = target.get("abilities") or []
    sorted_abilities = sorted(abilities, key=lambda a: a.get("total", 0), reverse=True)
    # Raw target keys + top-level table keys so we can see what fields exist
    # (WCL's 'Casts' table sometimes truncates abilities[] to top 5).
    return {
        "code": code,
        "fight_id": fight_id,
        "player": target.get("name"),
        "total_casts": target.get("total"),
        "ability_count_in_response": len(abilities),
        "target_keys": sorted(target.keys()),
        "table_top_level_keys": sorted(rd.get("castsTable", {}).get("data", {}).keys()),
        "abilities": [
            {"guid": a.get("guid"), "name": a.get("name"), "total": a.get("total")}
            for a in sorted_abilities
        ],
    }


@app.get("/api/debug/wcl-report", dependencies=[Depends(require_api_key)])
def debug_wcl_report(code: str):
    """Admin diagnostic. Returns the list of M+ fights in a given report
    plus the players in the first fight. Lets us verify whether our
    difficulty=10 filter matches the log, and which players WCL sees."""
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    def _fight_info(f: dict) -> dict:
        start = f.get("startTime") or 0
        end = f.get("endTime") or 0
        par = f.get("keystoneTime") or 0
        return {
            "id": f.get("id"),
            "encounterID": f.get("encounterID"),
            "name": f.get("name"),
            "keystoneLevel": f.get("keystoneLevel"),
            "kill": f.get("kill"),
            "startTime": start,
            "endTime": end,
            "duration_min": round((end - start) / 60000, 2),
            "keystoneTime_min": round(par / 60000, 2),
            "timed_by_our_math": bool(f.get("kill") and par > 0 and (end - start) <= par),
            "rating": f.get("rating"),
            "averageItemLevel": f.get("averageItemLevel"),
            "keystoneAffixes": f.get("keystoneAffixes"),
        }

    result = {
        "code": code,
        "fight_count": len(fights),
        "fights": [_fight_info(f) for f in fights[:10]],
    }
    if fights:
        try:
            pdata = wcl_client.get_report_player_data(code, [fights[0]["id"]])
            pd = (pdata or {}).get("playerDetails", {}).get("data", {}).get("playerDetails", {})
            players = []
            for role in ("tanks", "healers", "dps"):
                for p in pd.get(role, []):
                    players.append({
                        "role": role, "name": p.get("name"),
                        "type": p.get("type"), "server": p.get("server"),
                    })
            result["players_in_first_fight"] = players
        except Exception as e:
            result["players_error"] = str(e)
    return result


@app.get("/api/admin/scheduler-status", dependencies=[Depends(require_api_key)])
def scheduler_status(session: Session = Depends(get_session)):
    """Report what the background refresher is seeing: config, the 10 stalest
    players, and the 10 most-recently-refreshed. Use when a run doesn't
    show up on the site and we want to know if the scheduler saw it."""
    from app import scheduler as _sched

    stalest = list(session.execute(
        select(Player.name, Player.realm, Player.region, Player.last_ingested_at)
        .order_by(Player.last_ingested_at.asc().nullsfirst())
        .limit(10)
    ))
    freshest = list(session.execute(
        select(Player.name, Player.realm, Player.region, Player.last_ingested_at)
        .where(Player.last_ingested_at.is_not(None))
        .order_by(Player.last_ingested_at.desc())
        .limit(10)
    ))
    return {
        "enabled": settings.scheduler_enabled,
        "interval_seconds": settings.scheduler_interval_seconds,
        "batch_size": settings.scheduler_batch_size,
        "stale_after_seconds": settings.scheduler_stale_after_seconds,
        "thread_alive": bool(_sched._thread and _sched._thread.is_alive()),
        "stalest": [
            {"name": n, "realm": r, "region": rg, "last_ingested_at": ts}
            for n, r, rg, ts in stalest
        ],
        "freshest": [
            {"name": n, "realm": r, "region": rg, "last_ingested_at": ts}
            for n, r, rg, ts in freshest
        ],
    }


@app.get("/api/debug/wcl-encounters", dependencies=[Depends(require_api_key)])
def debug_wcl_encounters(code: str):
    """List every M+ fight in a report with its encounterID + name. Used to
    resolve `encounter_id=0` stubs in dungeon modules — paste a log from
    the dungeon, read the encounter_id off the output."""
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    return {
        "code": code,
        "fight_count": len(fights),
        "encounters": [
            {
                "fight_id": f.get("id"),
                "encounter_id": f.get("encounterID"),
                "name": f.get("name"),
                "keystone_level": f.get("keystoneLevel"),
                "kill": f.get("kill"),
            }
            for f in fights
        ],
    }


@app.get("/api/debug/wcl-damage-taken", dependencies=[Depends(require_api_key)])
def debug_wcl_damage_taken(
    code: str,
    encounter_id: int | None = None,
    limit: int = 30,
):
    """Aggregate the damage-taken table across every fight in the report
    matching `encounter_id` (or every fight if omitted). Returns top-N
    abilities by total damage — the raw input for picking
    `avoidable_abilities` entries for a dungeon module.

    Output is sorted descending, with `guid` + `name` + `total`. Human
    review decides which are avoidable (dodgeable AoEs, telegraphed casts)
    vs. unavoidable (tank autos, raid-wide pulses)."""
    from app.wcl.client import wcl_client

    fights = wcl_client.get_report_fights(code)
    if not fights:
        return {"error": "no M+ fights in report", "code": code}

    if encounter_id is not None:
        matching = [f for f in fights if f.get("encounterID") == encounter_id]
    else:
        matching = fights
    if not matching:
        return {
            "error": f"no fights with encounterID={encounter_id}",
            "encounters_in_report": sorted({
                (f.get("encounterID"), f.get("name")) for f in fights
            }),
        }

    fight_ids = [f["id"] for f in matching]
    entries = wcl_client.get_damage_taken_table(code, fight_ids)
    entries.sort(key=lambda e: e.get("total", 0), reverse=True)
    total_all = sum(e.get("total", 0) for e in entries) or 1
    return {
        "code": code,
        "encounter_id": encounter_id,
        "fight_ids": fight_ids,
        "fight_count": len(fight_ids),
        "ability_count": len(entries),
        "total_damage_taken": total_all,
        "top_abilities": [
            {
                "guid": e.get("guid"),
                "name": e.get("name"),
                "total": e.get("total"),
                "pct_of_total": round(100 * e.get("total", 0) / total_all, 1),
            }
            for e in entries[:limit]
        ],
    }


@app.get("/api/export/lua", response_class=PlainTextResponse)
@limiter.limit(settings.rate_limit_public)
def export_lua(
    request: Request,
    region: str | None = None,
    session: Session = Depends(get_session),
):
    """Download the generated UmbraData.lua file, optionally filtered by region."""
    content = generate_lua(session, region)
    filename = f"UmbraData_{region.upper()}.lua" if region else "UmbraData.lua"
    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── New endpoints for web frontend ──────────────────────────────────────────

@app.get("/api/stats/summary")
@limiter.limit(settings.rate_limit_public)
def stats_summary(
    request: Request,
    session: Session = Depends(get_session),
):
    """Public homepage stats: total characters, runs, and role counts.
    Cheap aggregate queries — used by the homepage header strip."""
    from sqlalchemy import func as _f
    from app.models import Role

    total_players = session.execute(select(_f.count()).select_from(Player)).scalar() or 0
    total_runs = session.execute(select(_f.count()).select_from(DungeonRun)).scalar() or 0
    graded_players = session.execute(
        select(_f.count(_f.distinct(PlayerScore.player_id)))
    ).scalar() or 0

    role_counts: dict[str, int] = {}
    for r in (Role.tank, Role.healer, Role.dps):
        role_counts[r.value] = session.execute(
            select(_f.count(_f.distinct(PlayerScore.player_id)))
            .where(PlayerScore.role == r, PlayerScore.primary_role.is_(True))
        ).scalar() or 0

    return {
        "total_players": total_players,
        "total_runs": total_runs,
        "graded_players": graded_players,
        "role_counts": role_counts,
    }


@app.get("/api/players/top", response_model=list[PlayerSearchResult])
@limiter.limit(settings.rate_limit_public)
def top_players(
    request: Request,
    role: str | None = None,
    region: str | None = None,
    limit: int = Query(default=10, le=50),
    session: Session = Depends(get_session),
):
    """Recently-graded players surfaced for the homepage showcase.

    Ordered by most-recent PlayerScore computation so the homepage
    reflects fresh ingests. Filters to primary-role scores only so we
    don't return the same player twice (once per role).
    """
    stmt = (
        select(PlayerScore)
        .where(PlayerScore.primary_role.is_(True))
        .options(selectinload(PlayerScore.player))
        .order_by(PlayerScore.computed_at.desc())
        .limit(limit * 2)  # over-fetch, then filter in Python for region
    )
    scores = session.execute(stmt).scalars().all()

    results: list[PlayerSearchResult] = []
    for score in scores:
        player = score.player
        if region and player.region.upper() != region.upper():
            continue
        if role and score.role.value != role.lower():
            continue
        run_stmt = (
            select(DungeonRun.spec_name)
            .where(DungeonRun.player_id == player.id)
            .order_by(DungeonRun.logged_at.desc())
            .limit(1)
        )
        spec = session.execute(run_stmt).scalar_one_or_none()
        results.append(PlayerSearchResult(
            name=player.name,
            realm=player.realm,
            region=player.region,
            class_id=player.class_id,
            grade=score.overall_grade,
            role=score.role.value,
            spec=spec,
            runs_analyzed=score.runs_analyzed,
            avatar_url=player.avatar_url,
            inset_url=player.inset_url,
        ))
        if len(results) >= limit:
            break

    return results


@app.get("/api/players/leaderboard", response_model=list[PlayerSearchResult])
@limiter.limit(settings.rate_limit_public)
def leaderboard(
    request: Request,
    role: str | None = None,
    region: str | None = None,
    class_id: int | None = Query(default=None, ge=1, le=13),
    limit: int = Query(default=50, le=200),
    session: Session = Depends(get_session),
):
    """Top-N players ordered by composite score.

    Optional filters: role (tank/healer/dps), region (EU/US/KR/TW/CN),
    class_id (1-13 Blizzard class mapping). Falls back to letter-grade
    ordering on rows where `composite_score` is NULL (pre-migration-005
    writes) so older data still appears — just at the end of the list.
    """
    stmt = (
        select(PlayerScore)
        .where(PlayerScore.primary_role.is_(True))
        .options(selectinload(PlayerScore.player))
        # NULL composite sorts LAST (Postgres default is NULLS LAST on DESC).
        .order_by(PlayerScore.composite_score.desc(), PlayerScore.computed_at.desc())
    )
    if role:
        try:
            stmt = stmt.where(PlayerScore.role == Role(role.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown role: {role}")

    # Over-fetch so region + class filters still produce `limit` results
    # without a second query. Worst case we scan 4× what we return.
    scores = session.execute(stmt.limit(limit * 4)).scalars().all()

    results: list[PlayerSearchResult] = []
    for score in scores:
        player = score.player
        if region and player.region.upper() != region.upper():
            continue
        if class_id is not None and player.class_id != class_id:
            continue
        spec = session.execute(
            select(DungeonRun.spec_name)
            .where(DungeonRun.player_id == player.id)
            .order_by(DungeonRun.logged_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        results.append(PlayerSearchResult(
            name=player.name,
            realm=player.realm,
            region=player.region,
            class_id=player.class_id,
            grade=score.overall_grade,
            role=score.role.value,
            spec=spec,
            runs_analyzed=score.runs_analyzed,
            avatar_url=player.avatar_url,
            inset_url=player.inset_url,
            composite_score=score.composite_score,
            rank=len(results) + 1,
        ))
        if len(results) >= limit:
            break
    return results


@app.get("/api/players/search", response_model=list[PlayerSearchResult])
@limiter.limit(settings.rate_limit_public)
def search_players(
    request: Request,
    q: str = Query(..., min_length=2, max_length=50),
    region: str | None = None,
    limit: int = Query(default=20, le=50),
    session: Session = Depends(get_session),
):
    """Search players by name prefix."""
    stmt = (
        select(Player)
        .where(Player.name.ilike(f"{q}%"))
        .options(selectinload(Player.scores))
    )
    if region:
        stmt = stmt.where(Player.region.ilike(region))
    stmt = stmt.limit(limit)

    players = session.execute(stmt).scalars().all()

    results = []
    for player in players:
        primary = next((s for s in player.scores if s.primary_role), None)
        # Get most recent spec from runs
        spec = None
        if primary:
            run_stmt = (
                select(DungeonRun.spec_name)
                .where(DungeonRun.player_id == player.id)
                .order_by(DungeonRun.logged_at.desc())
                .limit(1)
            )
            spec = session.execute(run_stmt).scalar_one_or_none()

        results.append(PlayerSearchResult(
            name=player.name,
            realm=player.realm,
            region=player.region,
            class_id=player.class_id,
            grade=primary.overall_grade if primary else None,
            role=primary.role.value if primary else None,
            spec=spec,
            runs_analyzed=primary.runs_analyzed if primary else None,
            avatar_url=player.avatar_url,
            inset_url=player.inset_url,
        ))

    return results


@app.get("/api/player/{region}/{realm}/{name}/all", response_model=PlayerProfileResponse)
@limiter.limit(settings.rate_limit_player_lookup)
def get_player_profile(
    request: Request,
    region: str,
    realm: str,
    name: str,
    session: Session = Depends(get_session),
):
    """Full player profile: all role scores + recent runs.

    If the character isn't in our DB yet, we try a one-shot ingest from
    WCL so anyone searching their own character gets a real answer
    instead of a dead-end 404. The stricter player-lookup rate limit
    applies (not the public limit) because each miss can trigger a
    chain of WCL calls.

    Outcomes:
      - Player in DB: served from cache, scores may or may not be
        populated depending on runs-analyzed threshold.
      - Player not in DB, WCL has recent M+ reports: ingested live,
        profile returned with whatever scored.
      - Player not in DB, WCL returns nothing: 404 with reason
        'wcl_not_found' so the frontend can show a tailored message.
      - Player not in DB, WCL has the character but no M+ in recent
        reports: profile returned with empty scores so the page can
        render with a 'no runs yet' state.
    """
    name, realm, region = _canonical_identity(name, realm, region)
    player = _find_player(session, region, realm, name)
    if not player:
        # Try a live ingest before giving up.
        try:
            result = ingest_player(session, name, realm, region)
        except Exception as e:
            logger.warning("Auto-ingest failed for %s-%s (%s): %s",
                           name, realm, region, e)
            result = None

        if result is None or result.player is None:
            reason = getattr(result, "reason", None) if result else None
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "not_found",
                    "reason": reason or "wcl_not_found",
                    "message": (
                        "Character not found on Warcraft Logs. Double-check "
                        "the name and realm, or make sure you've uploaded "
                        "at least one M+ log via the Warcraft Logs Uploader."
                    ),
                },
            )
        player = _find_player(session, region, realm, name)
        if not player:
            # Ingest returned a player but our lookup can't find it —
            # should never happen, but surface it as a generic 500-ish
            # 404 rather than silently returning nothing.
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "lookup_failed_post_ingest",
                    "message": "Ingest succeeded but player lookup failed. Try again in a minute.",
                },
            )

    # Build role scores
    scores = [
        RoleScore(
            role=s.role.value,
            grade=s.overall_grade,
            category_scores=s.category_scores,
            runs_analyzed=s.runs_analyzed,
            primary_role=s.primary_role,
        )
        for s in player.scores
    ]

    # Recent runs (last 20)
    run_stmt = (
        select(DungeonRun)
        .where(DungeonRun.player_id == player.id)
        .order_by(DungeonRun.logged_at.desc())
        .limit(20)
    )
    recent_runs = [_run_to_response(r) for r in session.execute(run_stmt).scalars()]

    # Timed percentage
    total_stmt = select(func.count()).where(DungeonRun.player_id == player.id)
    total_runs = session.execute(total_stmt).scalar() or 0

    timed_stmt = (
        select(func.count())
        .where(DungeonRun.player_id == player.id, DungeonRun.timed.is_(True))
    )
    timed_runs = session.execute(timed_stmt).scalar() or 0
    timed_pct = round((timed_runs / total_runs) * 100, 1) if total_runs > 0 else 0

    return PlayerProfileResponse(
        name=player.name,
        realm=player.realm,
        region=player.region,
        class_id=player.class_id,
        scores=scores,
        recent_runs=recent_runs,
        timed_pct=timed_pct,
        total_runs=total_runs,
        avatar_url=player.avatar_url,
        inset_url=player.inset_url,
        render_url=player.render_url,
    )


@app.get("/api/player/{region}/{realm}/{name}/runs", response_model=RunListResponse)
@limiter.limit(settings.rate_limit_public)
def get_player_runs(
    request: Request,
    region: str,
    realm: str,
    name: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=50),
    session: Session = Depends(get_session),
):
    """Paginated run history for a player."""
    name, realm, region = _canonical_identity(name, realm, region)
    player = _find_player(session, region, realm, name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Total count
    total = session.execute(
        select(func.count()).where(DungeonRun.player_id == player.id)
    ).scalar() or 0

    # Paginated runs
    offset = (page - 1) * per_page
    run_stmt = (
        select(DungeonRun)
        .where(DungeonRun.player_id == player.id)
        .order_by(DungeonRun.logged_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    runs = [_run_to_response(r) for r in session.execute(run_stmt).scalars()]

    return RunListResponse(runs=runs, total=total, page=page, per_page=per_page)


@app.get("/api/player/{region}/{realm}/{name}/runs/{run_id}", response_model=RunResponse)
@limiter.limit(settings.rate_limit_public)
def get_run_detail(
    request: Request,
    region: str,
    realm: str,
    name: str,
    run_id: int,
    session: Session = Depends(get_session),
):
    """Single run detail."""
    name, realm, region = _canonical_identity(name, realm, region)
    player = _find_player(session, region, realm, name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    run = session.execute(
        select(DungeonRun).where(
            DungeonRun.id == run_id,
            DungeonRun.player_id == player.id,
        )
    ).scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return _run_to_response(run)


@app.get("/api/player/{region}/{realm}/{name}/history", response_model=HistoryResponse)
@limiter.limit(settings.rate_limit_public)
def get_player_history(
    request: Request,
    region: str,
    realm: str,
    name: str,
    period: str = Query(default="month", pattern="^(week|month|season)$"),
    session: Session = Depends(get_session),
):
    """Time-series stats aggregated by day/week."""
    name, realm, region = _canonical_identity(name, realm, region)
    player = _find_player(session, region, realm, name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Determine date range
    now = datetime.utcnow()
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:  # season
        start = now - timedelta(days=120)

    # Fetch runs in range
    stmt = (
        select(DungeonRun)
        .where(
            DungeonRun.player_id == player.id,
            DungeonRun.logged_at >= start,
        )
        .order_by(DungeonRun.logged_at.asc())
    )
    runs = list(session.execute(stmt).scalars())

    # Bucket by day
    buckets: dict[str, list[DungeonRun]] = {}
    for run in runs:
        day = run.logged_at.strftime("%Y-%m-%d")
        buckets.setdefault(day, []).append(run)

    points = []
    for date, day_runs in sorted(buckets.items()):
        points.append(HistoryPoint(
            date=date,
            runs_count=len(day_runs),
            avg_keystone_level=round(
                sum(r.keystone_level for r in day_runs) / len(day_runs), 1
            ),
            timed_count=sum(1 for r in day_runs if r.timed),
            avg_deaths=round(
                sum(r.deaths for r in day_runs) / len(day_runs), 1
            ),
            avg_interrupts=round(
                sum(r.interrupts for r in day_runs) / len(day_runs), 1
            ),
            avg_dps=round(
                sum(r.dps for r in day_runs) / len(day_runs), 1
            ),
        ))

    return HistoryResponse(points=points, period=period)
