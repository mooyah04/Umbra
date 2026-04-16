import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    tank = "tank"
    healer = "healer"
    dps = "dps"


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    realm: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(10), nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    wcl_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    # Blizzard character-media URLs, populated from the Game Data API.
    # Nullable because some characters are hidden/private.
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    inset_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    render_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Set on every ingest_player attempt (even zero-run outcomes). The
    # scheduler picks the stalest rows by this timestamp to re-ingest;
    # `updated_at` is unsuitable because it also fires on media refreshes.
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list["DungeonRun"]] = relationship(back_populates="player")
    scores: Mapped[list["PlayerScore"]] = relationship(back_populates="player")


class DungeonRun(Base):
    __tablename__ = "dungeon_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    encounter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    keystone_level: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    spec_name: Mapped[str] = mapped_column(String(50), nullable=False)
    dps: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    hps: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    ilvl: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interrupts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispels: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avoidable_damage_taken: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    damage_taken_total: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    casts_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cooldown_usage_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    wcl_report_id: Mapped[str] = mapped_column(String(50), nullable=False)
    fight_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Enrichment fields (nullable for backwards compat with existing rows)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_item_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    keystone_affixes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    healing_received: Mapped[float | None] = mapped_column(Float, nullable=True)
    cc_casts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    critical_interrupts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avoidable_deaths: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Party composition snapshot — [{name, realm, class, role, spec}, ...] for
    # all 5 participants in the fight. Captured from WCL's playerDetails.
    party_comp: Mapped[list | None] = mapped_column(JSON, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="runs")


class PlayerScore(Base):
    __tablename__ = "player_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    overall_grade: Mapped[str] = mapped_column(String(5), nullable=False)
    # Raw 0-100 composite score that produced overall_grade. Needed for
    # leaderboard ordering (letter grades tie too often). Nullable so rows
    # written before migration 005 survive without a backfill.
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    runs_analyzed: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    player: Mapped["Player"] = relationship(back_populates="scores")


class AddonDownload(Base):
    """One row per /api/addon/download request. ip_hash is salted so we can
    dedup uniques without storing raw IPs. user_agent helps filter bot
    traffic out of the stats view."""
    __tablename__ = "addon_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class BugReport(Base):
    """User-submitted bug reports from the website or the addon.

    Addon reports come in via the website form too — the addon can't make
    HTTP calls, so the /umbra bug slash command writes to SavedVariables
    and tells the user to paste it into the site form. The `source` field
    captures which path a given row came in on so we can tell addon-
    surface bugs from web-surface bugs when triaging.
    """
    __tablename__ = "bug_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    # "website" | "addon" — free-form but we filter on this in the admin view.
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="website")
    # Optional contact info — users can submit anonymously.
    submitter_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    submitter_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Freeform bug body; no format enforced so users can paste stack traces
    # or screenshots of WoW errors. Capped at 8k chars to prevent abuse.
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str] = mapped_column(String(8000), nullable=False, default="")
    # Context the site can fill in automatically.
    page_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Hashed submitter IP for abuse tracking (never store raw IPs).
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Triage state — simple enough to keep as a free-form string for now.
    # "new" | "triaged" | "resolved" | "wontfix"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")
