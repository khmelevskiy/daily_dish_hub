# 🧪 Test Suite (integration + services)

This folder contains functional security, rate limiting, API wiring, and unit-level service tests.

## Files

- `test_admin_protection_smoke.py`: unauthenticated smoke to ensure `/admin/*` routes are protected.
- `test_security.py`: security checks (dangerous inputs, methods, headers, public API queries, health endpoint).
- `test_rate_limiter.py`: stress tests for rate limiting (bursts + concurrency).
- `test_api_dependencies.py`: static assertion that admin/public routers keep mandatory dependencies.
- `test_session_init.py`: guards against double initialisation of the async engine in tooling.
- `test_ordered_entity_service.py`: covers ordered CRUD helpers (explicit sort order, cascading behaviour).
- `test_menu_service.py`: checks menu query helper limit/offset handling.
- `test_image_service_unit.py`: image processing/path hardening unit tests.
- `test_utils_unit.py`: utility helpers (formatting, sanitisation).
- `conftest.py`: shared pytest fixtures (`--base-url`, `http`).
- `run_all.sh`: run all tests in order (rate-limiter after smoke tests).

## Running

```bash
# Run all in correct order (rate limiter runs after other HTTP smoke checks)
bash tests/run_all.sh -b http://localhost:8000

# Or use pytest directly
pytest -q --base-url=http://localhost:8000

# Run a single file
python tests/test_admin_protection_smoke.py
python tests/test_security.py
python tests/test_rate_limiter.py
```

Pacing to avoid accidental rate-limit hits during functional tests:

```bash
export TEST_ADMIN_PACE_SEC=0.5   # default 0.5s between admin requests
export TEST_PUBLIC_PACE_SEC=0.1  # default 0.1s between public requests
```

## Coverage

- 🚫 Dangerous admin paths/queries: SQLi, XSS, traversal, command injection.
- 🤖 Suspicious User-Agent blocking on public pages.
- 🔒 HTTP method protection on `/admin` (PUT/DELETE/PATCH/OPTIONS/TRACE).
- 📁 Upload security (unauthenticated rejection).
- 🌐 Public API query handling (safe statuses and traversal blocking on `/public/*`).
- 🛡️ Security headers (CSP, Frame Options, Referrer Policy, COOP, CORP, Permissions-Policy).
- ❤️ Health endpoint (`/health`).
- ⏱️ Rate limiting: admin/public/auth, headers, concurrency (in `test_rate_limiter.py`).
- 🧩 Router wiring + DB init: `test_api_dependencies.py`, `test_session_init.py`.
- 🔢 Ordered entities and menu pagination helpers (`test_ordered_entity_service.py`, `test_menu_service.py`).

## Requirements

- Running server (`--base-url` or `BASE_URL`, default `http://localhost:8000`).
- Dependencies: `pytest`, `requests` (see `pyproject.toml`).

## Notes

- Tests use small delays between requests to prevent false 429s.
- `test_rate_limiter.py` is stress-oriented; rely on `run_all.sh` to sequence it after the other HTTP smoke tests.

## Security

Tests do not contain real tokens or secrets; tokens are intentionally invalid.
