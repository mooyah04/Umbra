#!/usr/bin/env bash
set -e

# Install and start PostgreSQL
sudo apt-get update -qq
sudo apt-get install -y -qq postgresql postgresql-client > /dev/null
sudo service postgresql start

# Create database and user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'umbra';"
sudo -u postgres createdb umbra 2>/dev/null || true

# Install Python dependencies
cd backend
pip install -q -r requirements.txt

# Copy env file if not present (secrets should be added via Codespaces settings)
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "========================================="
  echo "  .env created from .env.example"
  echo "  Add your WCL API credentials via:"
  echo "  Codespaces > Settings > Secrets"
  echo "  or edit backend/.env directly"
  echo "========================================="
fi

# Run migrations
alembic upgrade head

echo ""
echo "Ready! Run: cd backend && uvicorn app.main:app --reload"
