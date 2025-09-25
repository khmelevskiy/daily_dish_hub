#!/usr/bin/env bash
# Script to perform a full reset of the local development project.
# Stops any running processes, cleans caches, and rebuilds the frontend.
# Use with caution as it removes build artifacts and temporary files.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 Full project cleanup..."

echo "[1/4] Stopping processes..."
pkill -f "uvicorn\|uv run" || true

echo "[2/4] Cleaning Python cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "[3/4] Cleaning old frontend build artifacts..."
# Vite artifacts copied by frontend/copy-build
rm -f app/static/index.html 2>/dev/null || true
rm -rf app/static/assets 2>/dev/null || true
# Remove any leftover build artifacts (menu.* files are handwritten)
rm -f app/static/js/*.chunk.js* 2>/dev/null || true
rm -f app/static/js/main.*.js* 2>/dev/null || true
rm -f app/static/css/main.*.css* 2>/dev/null || true

echo "[4/4] Rebuilding frontend (Vite)..."
if [ -d "frontend" ]; then
  cd frontend
  npm run build
  cd ..
else
  echo "  - 'frontend' folder not found, skipping React build"
fi

echo "✅ Cleanup complete!"
echo ""
echo "To initialize from scratch run:"
echo "  ./scripts/setup.sh"
echo ""
echo "Or for quick start:"
echo "  ./scripts/run_web.sh"
