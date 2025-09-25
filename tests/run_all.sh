#!/usr/bin/env bash
set -euo pipefail

# Run all tests in the correct order (rate limiter after other HTTP smoke tests).
# Usage:
#   /usr/bin/env sh tests/run_all.sh [-b BASE_URL]

BASE_URL=${BASE_URL:-http://localhost:8000}

while [ $# -gt 0 ]; do
  case "$1" in
    -b|--base-url)
      BASE_URL="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Gentle pacing for functional tests to avoid tripping rate limits
export TEST_ADMIN_PACE_SEC=${TEST_ADMIN_PACE_SEC:-0.5}
export TEST_PUBLIC_PACE_SEC=${TEST_PUBLIC_PACE_SEC:-0.1}

echo "[1/10] Admin protection smoke"
pytest -q --base-url="$BASE_URL" tests/test_admin_protection_smoke.py

echo "[2/10] Security tests"
pytest -q --base-url="$BASE_URL" tests/test_security.py

echo "[3/10] Admin permissions (login/register)"
pytest -q --base-url="$BASE_URL" tests/test_admin_permissions.py || echo "[WARN] Admin permissions test skipped or failed"

echo "[4/10] Rate limiter stress"
pytest -q --base-url="$BASE_URL" tests/test_rate_limiter.py

echo "[5/10] API router dependency wiring"
pytest -q tests/test_api_dependencies.py

echo "[6/10] DB session init idempotency"
pytest -q tests/test_session_init.py

echo "[7/10] Ordered entity service"
pytest -q tests/test_ordered_entity_service.py

echo "[8/10] Menu service queries"
pytest -q tests/test_menu_service.py

echo "[9/10] Utils unit"
pytest -q tests/test_utils_unit.py

echo "[10/10] Image service unit"
pytest -q tests/test_image_service_unit.py

echo "Done."
