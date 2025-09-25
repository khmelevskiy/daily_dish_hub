#!/usr/bin/env bash
# Script to run the Telegram bot for local development.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f .env ]; then
  echo ".env not found. Run ./scripts/setup.sh first" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install via: pipx install uv" >&2
  exit 1
fi

exec uv run daily_dish_hub
