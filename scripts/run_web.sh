#!/usr/bin/env bash
# Script to run the web server (Uvicorn) for local development.
# Make sure to run `scripts/setup.sh` first and correct env vars for Postgres.
set -euo pipefail

echo "❗️❗️❗️ Attention: Ensure POSTGRES_HOST and POSTGRES_PORT in .env are set for external DB access.❗️❗️❗️" # TODO: make it better

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install via: pipx install uv" >&2
  exit 1
fi

# Build frontend (Vite) if present
if [ -d "frontend" ]; then
  echo "Building frontend (Vite)..."
  cd frontend
  npm run build
  cd ..
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

exec uv run uvicorn app.web:app --host "$HOST" --port "$PORT" --reload
