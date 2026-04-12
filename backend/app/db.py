from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import settings

# Use sync psycopg driver (no greenlet needed)
sync_url = settings.database_url.replace("+psycopg", "+psycopg2").replace("+asyncpg", "+psycopg2")
# psycopg3 works with the plain "psycopg" dialect too
if "+psycopg2" in sync_url:
    sync_url = sync_url.replace("+psycopg2", "+psycopg")

engine = create_engine(sync_url, echo=False)
SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)


def get_session() -> Session:
    with SessionLocal() as session:
        yield session
