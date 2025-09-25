#!/usr/bin/env python3
"""Security tests with pytest:
- Dangerous path/query patterns are blocked or normalized
- Security headers are present
- Admin endpoints require authentication.
"""

import os
import sys
import time
from typing import Iterable

import pytest


PACE_ADMIN_SEC = float(os.getenv("TEST_ADMIN_PACE_SEC", "0.5"))  # 0.5s per admin request
PACE_PUBLIC_SEC = float(os.getenv("TEST_PUBLIC_PACE_SEC", "0.1"))


def _acceptable_block_statuses() -> set[int]:
    # Allow typical safe statuses for blocked/normalized requests
    return {401, 403, 404, 405, 307, 308}


@pytest.mark.parametrize(
    ("path", "case"),
    [
        # SQL Injection
        ("/admin/items/1' OR '1'='1", "SQL injection OR"),
        ("/admin/items/1' UNION SELECT * FROM users", "SQL injection UNION"),
        ("/admin/items/1' DROP TABLE users", "SQL injection DROP"),
        ("/admin/items/1'; DROP TABLE users; --", "SQL injection DROP with comment"),
        ("/admin/items/1' OR 1=1--", "SQL injection OR with comment"),
        ("/admin/items/1' AND 1=1--", "SQL injection AND"),
        # XSS
        ("/admin/items/1<script>alert('xss')</script>", "XSS script tag"),
        ("/admin/items/1?param=javascript:alert('xss')", "XSS javascript protocol"),
        ("/admin/items/1?param=<img src=x onerror=alert('xss')>", "XSS img onerror"),
        ("/admin/items/1?param=<svg onload=alert('xss')>", "XSS svg onload"),
        ("/admin/items/1?param=<iframe src=javascript:alert('xss')>", "XSS iframe"),
        # Path Traversal
        ("/admin/items/../../../etc/passwd", "Path traversal etc/passwd"),
        ("/admin/items/..\\..\\..\\windows\\system32\\config\\sam", "Path traversal WIN SAM"),
        ("/admin/items/....//....//....//etc/passwd", "Path traversal doubledots"),
        ("/admin/items/%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "Path traversal encoded"),
        # Command Injection
        ("/admin/items/1; ls -la", "Command injection ls"),
        ("/admin/items/1|cat /etc/passwd", "Command injection pipe"),
        ("/admin/items/1`whoami`", "Command injection backticks"),
        ("/admin/items/1$(id)", "Command injection dollar"),
        # Directory Traversal (normalized by Starlette/FastAPI)
        ("/admin/items/1/../../", "Directory traversal"),
        ("/admin/items/1/..%2f..%2f", "Directory traversal encoded"),
        # File Inclusion
        ("/admin/items/1?file=../../../etc/passwd", "File inclusion"),
        ("/admin/items/1?include=../../../etc/passwd", "File inclusion include"),
    ],
)
def test_dangerous_requests_blocked(http, base_url: str, path: str, case: str) -> None:
    r = http.get(f"{base_url}{path}", allow_redirects=False, timeout=3)
    assert r.status_code in _acceptable_block_statuses(), f"{case}: expected blocked/safe status, got {r.status_code}"
    time.sleep(PACE_ADMIN_SEC)


@pytest.mark.parametrize(
    ("filename", "content_type", "desc"),
    [
        ("test.php", "application/x-php", "PHP file"),
        ("test.exe", "application/x-executable", "Executable file"),
        ("test.sh", "application/x-sh", "Shell script"),
        ("test.js", "application/javascript", "JavaScript file"),
        ("test.html", "text/html", "HTML file"),
        ("test.txt", "text/plain", "Text file with .txt extension"),
    ],
)
def test_file_upload_security_unauth(http, base_url: str, filename: str, content_type: str, desc: str) -> None:
    files = {"file": (filename, b"test content", content_type)}
    r = http.post(f"{base_url}/admin/images/upload", files=files, timeout=5)
    assert r.status_code in {401, 400}, f"{desc}: expected 401 or 400, got {r.status_code}"
    time.sleep(PACE_ADMIN_SEC)


@pytest.mark.parametrize(
    "ua",
    [
        "sqlmap/1.0",
        "nikto/2.1.6",
        "nmap/7.80",
        "scanner/1.0",
        "bot/1.0",
        "crawler/1.0",
        "spider/1.0",
    ],
)
def test_suspicious_user_agents_blocked(http, base_url: str, ua: str) -> None:
    r = http.get(f"{base_url}/", headers={"User-Agent": ua}, timeout=3)
    assert r.status_code == 403, f"UA {ua} should be blocked, got {r.status_code}"
    time.sleep(PACE_PUBLIC_SEC)


@pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"])
@pytest.mark.parametrize("endpoint", ["/admin/items", "/admin/categories", "/admin/units"])
def test_method_security_on_admin(http, base_url: str, method: str, endpoint: str) -> None:
    r = http.request(method, f"{base_url}{endpoint}", json={}, timeout=5)
    assert r.status_code in {
        401,
        403,
        405,
    }, f"{method} {endpoint}: expected protected (401/403/405), got {r.status_code}"
    time.sleep(PACE_ADMIN_SEC)


@pytest.mark.parametrize(
    ("endpoint", "param"),
    [
        ("/public/daily-menu", "?param=javascript:alert('xss')"),
        ("/public/daily-menu", "?id=1' OR 1=1--"),
    ],
)
def test_public_api_query_handling(http, base_url: str, endpoint: str, param: str) -> None:
    r = http.get(f"{base_url}{endpoint}{param}", allow_redirects=False, timeout=3)
    assert r.status_code in {200, 404, 307, 308}, f"{endpoint}{param}: unexpected status {r.status_code}"
    time.sleep(PACE_PUBLIC_SEC)


def test_public_api_blocks_traversal_query(http, base_url: str) -> None:
    r = http.get(
        f"{base_url}/public/daily-menu?file=../../../etc/passwd",
        allow_redirects=False,
        timeout=3,
    )
    assert r.status_code == 403, "Traversal attempt on public endpoint should be blocked"
    time.sleep(PACE_PUBLIC_SEC)


def test_admin_authentication_required(http, base_url: str) -> None:
    r = http.get(f"{base_url}/admin/items", headers={"Authorization": "Bearer invalid"}, timeout=3)
    assert r.status_code == 401
    time.sleep(PACE_ADMIN_SEC)

    r2 = http.get(f"{base_url}/admin/items", timeout=3)
    assert r2.status_code == 401
    time.sleep(PACE_ADMIN_SEC)


def test_security_headers_present(http, base_url: str) -> None:
    r = http.get(f"{base_url}/", timeout=3)
    expected: Iterable[str] = (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Content-Security-Policy",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Resource-Policy",
        "Permissions-Policy",
    )
    missing = [h for h in expected if h not in r.headers]
    assert not missing, f"Missing security headers: {missing}"


def test_health_endpoint_exists(http, base_url: str) -> None:
    r = http.get(f"{base_url}/health", timeout=3)
    assert r.status_code == 200, "/health should exist and return 200"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
