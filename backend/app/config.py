from pydantic import field_validator
from pydantic_settings import BaseSettings


def _normalize_database_url(url: str) -> str:
    """Ensure the URL uses SQLAlchemy's psycopg3 driver scheme.

    Railway/Heroku/Render all inject DATABASE_URL as 'postgresql://...' or
    'postgres://...' — SQLAlchemy accepts the former but needs us to pin
    the driver to psycopg3 explicitly. This also rewrites the legacy
    'postgres://' scheme some providers still use.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Settings(BaseSettings):
    wcl_client_id: str = ""
    wcl_client_secret: str = ""
    database_url: str = "postgresql+psycopg://postgres:umbra@localhost:5432/umbra"

    @field_validator("database_url", mode="after")
    @classmethod
    def _fix_driver(cls, v: str) -> str:
        return _normalize_database_url(v)

    # WCL API endpoints
    wcl_token_url: str = "https://www.warcraftlogs.com/oauth/token"
    wcl_api_url: str = "https://www.warcraftlogs.com/api/v2/client"

    # Scoring defaults
    max_runs_to_analyze: int = 20
    min_runs_for_grade: int = 3
    max_reports_to_fetch: int = 20

    # WCL M+ season zone ID (update each season)
    # Midnight S1 = 47. Also mirrored in app/scoring/dungeons/seasons.py.
    wcl_mplus_zone_id: int = 47

    # Admin API key — required for bulk ingest and force-refresh.
    # Empty string means no key is configured → protected endpoints return 503.
    # Set via UMBRA_API_KEY env var. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    api_key: str = ""

    # Per-IP rate limits (slowapi syntax: "<count>/<period>").
    # Public read endpoints (search, profile, runs, history, export).
    rate_limit_public: str = "60/minute"
    # Player lookup — each uncached call triggers WCL ingest (expensive).
    rate_limit_player_lookup: str = "20/minute"

    # Blizzard Battle.net API credentials (develop.battle.net OAuth client).
    # Used to fetch character avatar / inset / render URLs for display on
    # player pages. Empty string disables all Blizzard lookups gracefully —
    # player pages fall back to the spec icon.
    bnet_client_id: str = ""
    bnet_client_secret: str = ""
    bnet_token_url: str = "https://oauth.battle.net/token"

    # Background refresher. Every `scheduler_interval_seconds`, picks up to
    # `scheduler_batch_size` players whose `last_ingested_at` is older than
    # `scheduler_stale_after_seconds` (or NULL) and re-ingests them. Keeps
    # logged data fresh without requiring anyone to visit their profile.
    # Disable in tests / one-off containers with `SCHEDULER_ENABLED=false`.
    # Defaults tuned for Platinum WCL (18k calls/hour). An ingest is ~30
    # WCL calls, so 15 players × (60s/300s) = 180/hr = ~5.4k calls/hr ≈ 30%
    # of budget — leaves room for visitor lookups and refresh=true calls.
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 300       # 5 min between sweeps
    scheduler_batch_size: int = 15              # players per sweep
    scheduler_stale_after_seconds: int = 3600   # 1 hr since last ingest
    # Optional region filter for the ingest sweep. Empty string = all regions;
    # set to "EU" (or comma-separated "EU,US") to prioritize specific regions
    # while leaving other regions' stubs in the queue untouched. Useful when
    # pre-public we only care about one region's data being fresh.
    scheduler_region_filter: str = ""
    # Parallel workers per sweep. Each ingest is network-bound (WCL HTTP)
    # so threading parallelizes the waits — 5 workers cuts sweep wall-clock
    # ~5× without raising the per-request WCL call count. Each worker
    # opens its own SessionLocal, so concurrent DB writes stay safe.
    # Keep ≤10 to avoid exhausting the DB pool (default pool is 5 + 10 overflow).
    scheduler_workers: int = 5

    # Leaderboard discovery. Polls Blizzard's mythic-keystone leaderboards
    # per connected realm per active-season dungeon, creating stub Player
    # rows for anyone not yet in our DB. Picked up by the WCL sweep above
    # on its next tick. Rotates through regions round-robin so Blizzard's
    # 36k/hr rate limit is never stressed.
    leaderboard_enabled: bool = True
    leaderboard_interval_seconds: int = 3600    # 1 hr between ticks
    leaderboard_realms_per_tick: int = 4        # 4 realms × 8 dungeons = 32 Blizzard calls/tick
    leaderboard_regions: str = "US,EU,KR,TW"    # CSV, round-robin one per tick

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
