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
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 900       # 15 min between sweeps
    scheduler_batch_size: int = 5               # players per sweep
    scheduler_stale_after_seconds: int = 3600   # 1 hr since last ingest

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
