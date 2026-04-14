#!/bin/sh
# Run migrations, then exec the main command.
# Using exec so uvicorn receives signals (SIGTERM) directly and shuts down cleanly.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Running alembic upgrade head..."
  alembic upgrade head
fi

exec "$@"
