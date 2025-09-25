#!/usr/bin/env python3
"""Admin permissions tests using real login to obtain tokens.

These tests require a running server and pre-configured admin credentials
available via environment variables ADMIN_USERNAME / ADMIN_PASSWORD.

If credentials are not provided, tests are skipped.
"""

import os
import sys
import time
import uuid

import pytest
from dotenv import load_dotenv


load_dotenv()

PACE_ADMIN_SEC = float(os.getenv("TEST_ADMIN_PACE_SEC", "0.5"))


def _env_admin_creds() -> tuple[str, str] | None:
    u = os.getenv("ADMIN_USERNAME")
    p = os.getenv("ADMIN_PASSWORD")
    if u and p:
        return u, p
    return None


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _require_admin_creds() -> tuple[str, str]:
    creds = _env_admin_creds()
    if not creds:
        pytest.skip("ADMIN_USERNAME/ADMIN_PASSWORD not set; skipping admin permission tests")
    return creds


def _login(http, base_url: str, username: str, password: str) -> str:
    r = http.post(
        f"{base_url}/auth/login",
        json={"username": username, "password": password},
        timeout=5,
    )
    assert r.status_code == 200, f"Login failed for {username}: {r.text}"
    token = r.json().get("access_token")
    assert token, "No access_token in login response"
    return token


def test_admin_and_non_admin_access(http, base_url: str) -> None:
    admin_user, admin_pass = _require_admin_creds()

    # Login as admin
    admin_token = _login(http, base_url, admin_user, admin_pass)
    time.sleep(PACE_ADMIN_SEC)

    # Admin should access /admin/items
    r = http.get(f"{base_url}/admin/items", headers=_auth_headers(admin_token), timeout=5)
    assert r.status_code == 200, f"Admin should access /admin/items, got {r.status_code}: {r.text}"
    time.sleep(PACE_ADMIN_SEC)

    # Create a non-admin user via admin-protected register endpoint
    new_username = f"test_user_{uuid.uuid4().hex[:8]}"
    new_password = "Test12345pass"  # pragma: allowlist secret
    user_id: int | None = None
    try:
        r = http.post(
            f"{base_url}/auth/register",
            headers=_auth_headers(admin_token),
            json={"username": new_username, "password": new_password, "is_admin": False},
            timeout=5,
        )
        assert r.status_code == 200, f"Admin /auth/register failed: {r.status_code} {r.text}"
        payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        user_id = int(payload.get("data", {}).get("id")) if payload.get("data") else None
        time.sleep(PACE_ADMIN_SEC)

        # Login as the non-admin user
        user_token = _login(http, base_url, new_username, new_password)
        time.sleep(PACE_ADMIN_SEC)

        # Non-admin must receive 403 for /admin endpoints
        r = http.get(f"{base_url}/admin/items", headers=_auth_headers(user_token), timeout=5)
        assert r.status_code == 403, f"Non-admin should be forbidden, got {r.status_code}"
    finally:
        # Cleanup: delete the temp user to keep DB clean
        if user_id is not None:
            dr = http.delete(
                f"{base_url}/auth/users/{user_id}",
                headers=_auth_headers(admin_token),
                timeout=5,
            )
            # 200 expected; tolerate 404 if the test failed before creation/login
            assert dr.status_code in {200, 404}, f"Cleanup failed: {dr.status_code} {dr.text}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
