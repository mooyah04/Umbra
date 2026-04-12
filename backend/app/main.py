"""Umbra Backend — FastAPI application."""

import logging
from contextlib import contextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import engine, get_session
from app.export.lua_writer import generate_lua
from app.models import Base, Player, PlayerScore
from app.pipeline.ingest import ingest_batch, ingest_player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


app = FastAPI(title="Umbra Score Engine", version="0.1.0", lifespan=lifespan)


# ── Schemas ──────────────────────────────────────────────────────────────────

class PlayerScoreResponse(BaseModel):
    name: str
    realm: str
    region: str
    role: str
    grade: str
    category_scores: dict[str, float]
    runs_analyzed: int


class IngestRequest(BaseModel):
    players: list[dict]  # [{name, realm, region}, ...]


class IngestResponse(BaseModel):
    ingested: int
    failed: int


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "umbra-score-engine"}


@app.get("/api/player/{region}/{realm}/{name}", response_model=PlayerScoreResponse)
def get_player_score(
    region: str,
    realm: str,
    name: str,
    refresh: bool = False,
    session: Session = Depends(get_session),
):
    """Look up a player's Umbra score. Triggers ingestion if not cached."""
    # Check cache first
    if not refresh:
        stmt = (
            select(Player)
            .where(
                Player.name.ilike(name),
                Player.realm.ilike(realm),
                Player.region.ilike(region),
            )
            .options(selectinload(Player.scores))
        )
        result = session.execute(stmt)
        player = result.scalar_one_or_none()

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
    player = ingest_player(session, name, realm, region)
    if not player:
        raise HTTPException(status_code=404, detail="Character not found on Warcraft Logs")

    # Reload with scores
    stmt = (
        select(Player)
        .where(Player.id == player.id)
        .options(selectinload(Player.scores))
    )
    result = session.execute(stmt)
    player = result.scalar_one()

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


@app.post("/api/ingest", response_model=IngestResponse)
def bulk_ingest(
    request: IngestRequest,
    session: Session = Depends(get_session),
):
    """Bulk ingest a list of players from WCL."""
    results = ingest_batch(session, request.players)
    return IngestResponse(
        ingested=len(results),
        failed=len(request.players) - len(results),
    )


@app.get("/api/export/lua", response_class=PlainTextResponse)
def export_lua(session: Session = Depends(get_session)):
    """Download the generated UmbraData.lua file."""
    content = generate_lua(session)
    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=UmbraData.lua"},
    )
