#!/bin/sh
# Bootstrap a fresh DB (if needed), run migrations, then exec the main command.
# Using exec so uvicorn receives signals (SIGTERM) directly and shuts down cleanly.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Bootstrapping DB (create schema if fresh, stamp alembic)..."
  python bootstrap_db.py

  echo "Running alembic upgrade head..."
  alembic upgrade head
fi

exec "$@"
