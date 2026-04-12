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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
