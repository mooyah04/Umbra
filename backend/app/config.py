from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    wcl_client_id: str = ""
    wcl_client_secret: str = ""
    database_url: str = "postgresql+psycopg://postgres:umbra@localhost:5432/umbra"

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
