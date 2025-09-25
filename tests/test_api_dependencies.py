#!/usr/bin/env python3
"""Static checks for router dependency wiring."""

import sys

import pytest
from fastapi.routing import APIRoute

from app.api import api_router
from app.api.auth import get_current_admin_user
from app.api.dependencies import verify_admin_token


def _dependency_calls(route: APIRoute) -> set:
    return {dep.call for dep in route.dependant.dependencies if getattr(dep, "call", None) is not None}


def test_admin_routes_require_admin_token():
    admin_routes = [
        route for route in api_router.routes if isinstance(route, APIRoute) and route.path.startswith("/admin")
    ]
    assert admin_routes, "Expected /admin routes to be registered"

    for route in admin_routes:
        calls = _dependency_calls(route)
        assert verify_admin_token in calls, f"Route {route.path} missing verify_admin_token dependency"


def test_auth_admin_endpoints_require_admin_user():
    admin_paths = {"/auth/register", "/auth/users", "/auth/users/{user_id}"}

    for route in api_router.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/auth"):
            continue

        calls = _dependency_calls(route)
        if route.path in admin_paths:
            assert get_current_admin_user in calls, f"Route {route.path} must depend on get_current_admin_user"
        else:
            assert get_current_admin_user not in calls, (
                f"Route {route.path} should not depend on get_current_admin_user"
            )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
