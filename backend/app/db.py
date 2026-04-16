from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import settings

# Use sync psycopg driver (no greenlet needed)
sync_url = settings.database_url.replace("+psycopg", "+psycopg2").replace("+asyncpg", "+psycopg2")
# psycopg3 works with the plain "psycopg" dialect too
if "+psycopg2" in sync_url:
    sync_url = sync_url.replace("+psycopg2", "+psycopg")

# Pool sized to accommodate parallel ingest (5 scheduler workers + pooler
# slack for visitor traffic + FastAPI deps). Pool kwargs only apply to
# real DBs — SQLite uses SingletonThreadPool and rejects them.
_engine_kwargs: dict = {"echo": False}
if "sqlite" not in sync_url:
    _engine_kwargs.update(
        pool_size=15,
        max_overflow=10,
        pool_pre_ping=True,
    )
engine = create_engine(sync_url, **_engine_kwargs)
SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)


def get_session() -> Session:
    with SessionLocal() as session:
        yield session
