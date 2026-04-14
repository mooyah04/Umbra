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

    player: Mapped["Player"] = relationship(back_populates="runs")


class PlayerScore(Base):
    __tablename__ = "player_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    overall_grade: Mapped[str] = mapped_column(String(5), nullable=False)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    runs_analyzed: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    player: Mapped["Player"] = relationship(back_populates="scores")
