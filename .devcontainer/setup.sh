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

# Build .env from Codespaces secrets (fall back to example if secrets missing)
cat > .env <<EOL
WCL_CLIENT_ID=${WCL_CLIENT_ID:-your_client_id_here}
WCL_CLIENT_SECRET=${WCL_CLIENT_SECRET:-your_client_secret_here}
DATABASE_URL=${DATABASE_URL:-postgresql+psycopg://postgres:umbra@localhost:5432/umbra}
EOL

if [ "$WCL_CLIENT_ID" = "" ] || [ "$WCL_CLIENT_ID" = "your_client_id_here" ]; then
  echo ""
  echo "========================================="
  echo "  WCL secrets not found!"
  echo "  Add them at: GitHub > Repo Settings >"
  echo "  Secrets > Codespaces"
  echo "========================================="
fi

# Run migrations
alembic upgrade head

echo ""
echo "Ready! Run: cd backend && uvicorn app.main:app --reload"
