"""Umbra Backend — FastAPI application."""

import logging
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import Float, Integer, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import engine, get_session
from app.export.lua_writer import generate_lua
from app.models import Base, DungeonRun, Player, PlayerScore
from app.pipeline.ingest import ingest_batch, ingest_player
from app.security import limiter, require_api_key
from app.validators import ValidationError, validate_player_identity
from app.schemas import (
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
    yield
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
@limiter.limit(settings.rate_limit_public)
def get_player_profile(
    request: Request,
    region: str,
    realm: str,
    name: str,
    session: Session = Depends(get_session),
):
    """Full player profile: all role scores + recent runs."""
    name, realm, region = _canonical_identity(name, realm, region)
    player = _find_player(session, region, realm, name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

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
