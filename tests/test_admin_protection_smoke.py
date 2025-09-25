#!/usr/bin/env python3
"""Simple smoke test ensuring admin endpoints are protected by auth.

Base URL is provided via `--base-url` pytest option or env BASE_URL.
"""

import sys

import pytest


@pytest.mark.parametrize(
    "endpoint",
    [
        "/admin/items",
        "/admin/categories",
        "/admin/units",
        "/admin/daily-menu",
        "/admin/daily-menu/date",
        "/admin/images",
    ],
)
def test_admin_routes_require_auth(http, base_url: str, endpoint: str) -> None:
    r = http.get(f"{base_url}{endpoint}", timeout=3)
    assert r.status_code in (401, 403), f"{endpoint} should be protected, got {r.status_code}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
