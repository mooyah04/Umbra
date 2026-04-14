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


def _find_player(session: Session, region: str, realm: str, name: str) -> Player | None:
    """Match realm in both slug and display form.

    WCL uses slugs ('tarren-mill'), WoW displays use spaces ('Tarren Mill').
    Ingest stores the display form; URLs typically carry the slug form.
    Accept either so frontend routing and API calls match the stored row.
    """
    realm_variants = {realm, realm.replace("-", " "), realm.replace(" ", "-")}
    stmt = (
        select(Player)
        .where(
            Player.name.ilike(name),
            or_(*(Player.realm.ilike(v) for v in realm_variants)),
            Player.region.ilike(region),
        )
        .options(selectinload(Player.scores), selectinload(Player.runs))
    )
    return session.execute(stmt).scalar_one_or_none()


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
