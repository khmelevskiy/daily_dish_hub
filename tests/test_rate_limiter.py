#!/usr/bin/env python3
"""Aggressive Rate Limiter test
Verifies rate limiting behavior under fast/high-volume requests.
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def test_admin_rate_limit_aggressive():
    """Test rate limiting for admin APIs with fast requests."""
    print("🔒 Aggressive rate limiting test for admin APIs...")

    # Very fast requests
    print("  Very fast requests (no pauses):")
    rate_limit_hit = False
    for i in range(250):  # Above 200 limit
        try:
            response = requests.get(f"{BASE_URL}/admin/items")
            if response.status_code == 429:
                print(f"    ✅ Rate limit triggered at request {i + 1}")
                rate_limit_hit = True
                break
        except Exception as e:
            print(f"    ❌ Error at request {i + 1}: {e}")

    if not rate_limit_hit:
        print("    ❌ Rate limit did not trigger after 250 requests")
    assert rate_limit_hit, "Admin rate limit did not trigger after 250 unauthenticated requests"

    # Check rate limit headers
    try:
        response = requests.get(f"{BASE_URL}/admin/items")
        if "X-RateLimit-Limit" in response.headers:
            print(f"    ✅ Header X-RateLimit-Limit: {response.headers['X-RateLimit-Limit']}")
        else:
            print("    ❌ Header X-RateLimit-Limit missing")

        if "X-RateLimit-Window" in response.headers:
            print(f"    ✅ Header X-RateLimit-Window: {response.headers['X-RateLimit-Window']}")
        else:
            print("    ❌ Header X-RateLimit-Window missing")
    except Exception as e:
        print(f"    ❌ Error checking headers: {e}")


def test_auth_rate_limit_aggressive():
    """Test rate limiting for login with fast attempts."""
    print("\n🔐 Aggressive rate limiting test for login...")

    print("  Very fast login attempts:")
    rate_limit_hit = False
    for i in range(60):  # Above 50 limit
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={"username": "test", "password": "test"})
            if response.status_code == 429:
                print(f"    ✅ Login rate limit triggered at attempt {i + 1}")
                rate_limit_hit = True
                break
        except Exception as e:
            print(f"    ❌ Error at attempt {i + 1}: {e}")

    if not rate_limit_hit:
        print("    ❌ Login rate limit did not trigger after 60 attempts")
    assert rate_limit_hit, "Auth rate limit did not trigger after 60 rapid login attempts"


def test_public_rate_limit_aggressive():
    """Test rate limiting for public APIs with very fast requests."""
    print("\n🌐 Aggressive rate limiting test for public APIs...")

    print("  Very fast requests to public API:")
    rate_limit_hit = False
    for i in range(600):  # Above 500 limit
        try:
            response = requests.get(f"{BASE_URL}/public/daily-menu")
            if response.status_code == 429:
                print(f"    ✅ Public API rate limit triggered at request {i + 1}")
                rate_limit_hit = True
                break
        except Exception as e:
            print(f"    ❌ Error at request {i + 1}: {e}")

    if not rate_limit_hit:
        print("    ❌ Public API rate limit did not trigger after 600 requests")
    assert rate_limit_hit, "Public API rate limit did not trigger after 600 rapid requests"


def test_concurrent_requests_aggressive():
    """Test rate limiting under very fast concurrent requests."""
    print("\n⚡ Aggressive rate limiting test under concurrent requests...")

    def make_request(endpoint, request_id):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            return {
                "id": request_id,
                "status": response.status_code,
                "endpoint": endpoint,
            }
        except Exception as e:
            return {
                "id": request_id,
                "status": "ERROR",
                "error": str(e),
                "endpoint": endpoint,
            }

    # Test very fast concurrent requests to admin API
    print("  Very fast concurrent requests to admin API:")
    with ThreadPoolExecutor(max_workers=10) as executor:  # More threads
        futures = []
        for i in range(250):  # More requests
            future = executor.submit(make_request, "/admin/items", i + 1)
            futures.append(future)

        results = []
        for future in as_completed(futures):
            results.append(future.result())

        # Analyze results
        blocked_requests = [r for r in results if r["status"] == 429]
        successful_requests = [r for r in results if r["status"] == 401]  # 401 is expected for unauthorized

        print(f"    Total requests: {len(results)}")
        print(f"    Blocked (429): {len(blocked_requests)}")
        print(f"    Successful (401): {len(successful_requests)}")

        if blocked_requests:
            print("    ✅ Rate limiting works under concurrency")
        else:
            print("    ❌ Rate limiting did not trigger under concurrency")

        assert blocked_requests, "Concurrent admin requests failed to trigger rate limiting"


def check_server_availability():
    """Check server availability."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is available")
            return True
        else:
            print(f"⚠️ Server responds with status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Server unavailable. Ensure it's running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False


def main():
    """Main test runner."""
    print("⏱️ AGGRESSIVE RATE LIMITER TEST")
    print("=" * 60)

    # Check server availability
    if not check_server_availability():
        print("\n❌ Testing aborted due to server unavailability")
        return

    print("\n🚀 Starting rate limiting tests...\n")

    test_admin_rate_limit_aggressive()
    test_auth_rate_limit_aggressive()
    test_public_rate_limit_aggressive()
    test_concurrent_requests_aggressive()

    print("\n" + "=" * 60)
    print("✅ Aggressive rate limiter testing completed!")
    print("📊 Check server logs for details")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
