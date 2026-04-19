"""Pydantic response/request models for the Umbra API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.validators import ValidationError, validate_player_identity


# ── Existing schemas (moved from main.py) ────────────────────────────────────

class PlayerScoreResponse(BaseModel):
    name: str
    realm: str
    region: str
    role: str
    grade: str
    category_scores: dict[str, float]
    runs_analyzed: int


class IngestPlayer(BaseModel):
    name: str
    realm: str
    region: str
    # Optional class hint — overrides WCL's unreliable character endpoint
    # classID when provided. Accept either the class name ('Mage') or the
    # numeric class_id (1-13). Hint wins over per-fight playerDetails and
    # spec-based inference, since the caller knows best.
    class_name: str | None = None
    class_id: int | None = None
    # Optional list of WCL report codes (the "XYZ123abc" part of a
    # warcraftlogs.com/reports/XYZ123abc URL). When supplied, we ingest
    # fights directly from these reports and skip the broken character()
    # lookup that returns wrong entities on name-colliding realms.
    report_codes: list[str] | None = None

    @field_validator("name", "realm", "region", mode="after")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        # Per-field emptiness is caught by validate_player_identity below; this
        # just ensures pydantic doesn't strip-and-accept "  ".
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v

    @field_validator("class_id", mode="after")
    @classmethod
    def _valid_class_id(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if not (1 <= v <= 13):
            raise ValueError("class_id must be between 1 and 13")
        return v


class IngestRequest(BaseModel):
    # Max 500 players/batch — prevents a single request from queueing thousands
    # of WCL calls. Adjust if bulk imports need more.
    players: list[IngestPlayer] = Field(..., min_length=1, max_length=500)

    @field_validator("players", mode="after")
    @classmethod
    def _canonicalize(cls, players: list["IngestPlayer"]) -> list["IngestPlayer"]:
        """Validate + canonicalize every entry; reject the whole batch on any bad row."""
        out: list[IngestPlayer] = []
        for i, p in enumerate(players):
            try:
                name, realm, region = validate_player_identity(p.name, p.realm, p.region)
            except ValidationError as e:
                raise ValueError(f"players[{i}]: {e}")
            out.append(IngestPlayer(
                name=name, realm=realm, region=region,
                class_name=p.class_name, class_id=p.class_id,
                report_codes=p.report_codes,
            ))
        return out


class IngestResponse(BaseModel):
    ingested: int
    failed: int


class ClaimRequest(BaseModel):
    """A visitor disambiguates 'which character named X is me?' by pasting a
    WCL report URL (or bare report code) that contains their actual character.
    We read playerDetails from that report, find the matching name, pull the
    class from the per-fight 'type' field, and ingest via report_codes mode —
    bypassing WCL's ambiguous character() lookup entirely."""
    name: str
    realm: str
    region: str
    report_url_or_code: str = Field(..., min_length=3, max_length=300)


class ClaimResponse(BaseModel):
    ok: bool
    report_code: str
    class_name: str | None = None
    class_id: int | None = None
    runs_ingested: int = 0
    reason: str | None = None


# ── New schemas for web frontend ─────────────────────────────────────────────

class PlayerSearchResult(BaseModel):
    name: str
    realm: str
    region: str
    class_id: int
    grade: str | None = None
    role: str | None = None
    spec: str | None = None
    runs_analyzed: int | None = None
    avatar_url: str | None = None
    inset_url: str | None = None
    # Populated on leaderboard responses so the UI can show "B+ · 78.3".
    # Null on older score rows written before migration 005.
    composite_score: float | None = None
    # Rank within the filtered leaderboard slice (1-based).
    rank: int | None = None


class RunResponse(BaseModel):
    id: int
    encounter_id: int
    keystone_level: int
    role: str
    spec_name: str
    dps: float
    hps: float
    ilvl: float
    duration: int
    deaths: int
    interrupts: int
    dispels: int
    avoidable_damage_taken: float
    damage_taken_total: float
    casts_total: int
    cooldown_usage_pct: float
    timed: bool
    logged_at: datetime
    # WCL provenance — exposed so the frontend can deep-link to the source
    # log page (e.g. "Open on WCL") and future backfill work can key on
    # these fields without a round-trip.
    wcl_report_id: str
    fight_id: int
    # Enrichment fields (nullable)
    rating: int | None = None
    average_item_level: float | None = None
    keystone_affixes: list | None = None
    keystone_bonus: int | None = None
    healing_received: float | None = None
    cc_casts: int | None = None
    critical_interrupts: int | None = None
    avoidable_deaths: int | None = None
    party_comp: list[dict] | None = None
    # Level B v2 — pull-by-pull breakdown. List of pull objects with
    # nested events. None on runs below the keystone-level threshold
    # (+2, was +8) or ingested before Level B v2 shipped.
    pulls: list[dict] | None = None
    # Per-run grade — scoring engine applied to this one run alone.
    # Answers "how did THIS particular run play?", letting the run page
    # show a grade for the pull the user clicked into alongside the
    # dungeon-wide aggregate below. Only populated by the single-run
    # endpoint.
    run_grade: str | None = None
    run_composite_score: float | None = None
    # Per-dungeon aggregate context — same scoring math applied across
    # every run the player has in this encounter+role. Answers "where
    # does this run sit inside my overall grade for this dungeon?"
    dungeon_grade: str | None = None
    dungeon_composite_score: float | None = None
    dungeon_runs_count: int | None = None


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    page: int
    per_page: int


class RoleScore(BaseModel):
    role: str
    grade: str
    category_scores: dict[str, float]
    runs_analyzed: int
    primary_role: bool


class PerDungeonGrade(BaseModel):
    """One tile of the 'Performance by Dungeon' breakdown on the player page.

    Grade + composite_score are the player's primary-role scoring result
    restricted to runs of this single dungeon. Empty dungeons (runs_count=0)
    carry the tile so the UI can surface coverage gaps — the frontend
    renders those dimmed.
    """
    encounter_id: int
    dungeon_name: str
    runs_count: int
    grade: str | None = None
    composite_score: float | None = None
    best_keystone_timed: int | None = None
    best_keystone_attempted: int | None = None



class PlayerProfileResponse(BaseModel):
    name: str
    realm: str
    region: str
    class_id: int
    scores: list[RoleScore]
    recent_runs: list[RunResponse]
    timed_pct: float
    total_runs: int
    avatar_url: str | None = None
    inset_url: str | None = None
    render_url: str | None = None
    # Sorted: graded tiles descending by composite, empty tiles last.
    per_dungeon: list[PerDungeonGrade] = []
    # True when the row is a stub we haven't finished ingesting yet.
    # Frontend renders an "analyzing…" state and the scheduler will
    # warm the row on its next sweep.
    is_indexing: bool = False
    # True when the character has never been ingested. The frontend
    # renders a "Parse Warcraft Logs" empty state instead of a spinner
    # so the user can trigger ingest explicitly via POST /parse.
    not_indexed: bool = False


class HistoryPoint(BaseModel):
    date: str
    runs_count: int
    avg_keystone_level: float
    timed_count: int
    avg_deaths: float
    avg_interrupts: float
    avg_dps: float


class HistoryResponse(BaseModel):
    points: list[HistoryPoint]
    period: str


# ── Bug reports ─────────────────────────────────────────────────────────────

class RefreshResponse(BaseModel):
    """Response from the user-triggered refresh endpoint.

    `refreshed_at` is the timestamp WCL ingest last completed for this player
    (read back from DB after the refresh finishes). `cooldown_ends_at` tells
    the frontend when the player is eligible for another refresh so it can
    disable the button and show a countdown without a second round-trip.
    """
    ok: bool
    refreshed_at: datetime
    cooldown_ends_at: datetime


class ParseResponse(BaseModel):
    """Result of a user-triggered cold parse."""
    ok: bool
    # Number of M+ runs ingested from the WCL reports we found. 0 is a
    # valid success — the character exists on WCL but has no M+ runs
    # in their recent reports yet.
    runs_ingested: int


class BugReportRequest(BaseModel):
    """Public submission from the website form (or a user pasting addon
    SavedVariables output into the same form)."""
    summary: str = Field(..., min_length=3, max_length=200)
    details: str = Field(default="", max_length=8000)
    source: str = Field(default="website", max_length=20)
    submitter_name: str | None = Field(default=None, max_length=80)
    submitter_email: str | None = Field(default=None, max_length=200)
    page_url: str | None = Field(default=None, max_length=500)

    @field_validator("source", mode="after")
    @classmethod
    def _valid_source(cls, v: str) -> str:
        if v not in ("website", "addon"):
            raise ValueError("source must be 'website' or 'addon'")
        return v


class BugReportStatusUpdate(BaseModel):
    """Admin-only status change for a bug report."""
    status: str = Field(..., max_length=20)

    @field_validator("status", mode="after")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        if v not in ("new", "triaged", "resolved", "wontfix"):
            raise ValueError(
                "status must be one of: new, triaged, resolved, wontfix"
            )
        return v


class BugReportResponse(BaseModel):
    id: int
    created_at: datetime
    source: str
    status: str
    submitter_name: str | None
    submitter_email: str | None
    summary: str
    details: str
    page_url: str | None
    user_agent: str | None
