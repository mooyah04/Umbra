"""Fresh-DB bootstrap: create schema from current models and stamp alembic.

Runs in the container entrypoint before any migration attempts. For a DB that
already has tables (normal redeploy) this is a no-op via create_all's
IF NOT EXISTS semantics, and the stamp is skipped.

Why: migration 001 was written as an incremental 'add enrichment fields' on
top of an already-live schema. On a brand-new Railway/production DB there's
nothing to alter yet, so alembic upgrade fails immediately. This script makes
'alembic upgrade head' correct both for fresh DBs (no-op after stamp) and
for existing DBs (normal upgrade).
"""
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import settings
from app.models import Base


def main() -> int:
    if not settings.database_url:
        print("bootstrap_db: DATABASE_URL is empty, skipping", flush=True)
        return 0

    engine = create_engine(settings.database_url)
    insp = inspect(engine)
    existing = set(insp.get_table_names())

    has_alembic = "alembic_version" in existing
    has_app_tables = {"players", "dungeon_runs", "player_scores"}.issubset(existing)

    if has_alembic and has_app_tables:
        # Normal redeploy — leave it to 'alembic upgrade head'.
        print("bootstrap_db: existing DB detected, deferring to alembic upgrade", flush=True)
        return 0

    print("bootstrap_db: fresh DB — running Base.metadata.create_all", flush=True)
    Base.metadata.create_all(engine)

    print("bootstrap_db: stamping alembic at head", flush=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.stamp(cfg, "head")

    print("bootstrap_db: done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
