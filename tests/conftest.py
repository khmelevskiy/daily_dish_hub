#!/usr/bin/env python3
"""Common pytest fixtures for HTTP tests:
- base_url: target server base URL (env BASE_URL or default http://localhost:8000)
- http: shared requests.Session with sane defaults.
"""

import os
from typing import Iterator

import pytest
import requests


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default=os.getenv("BASE_URL", "http://localhost:8000"),
        help="Base URL of the running server (default: env BASE_URL or http://localhost:8000)",
    )


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    return str(pytestconfig.getoption("--base-url")).rstrip("/")


@pytest.fixture(scope="session")
def http() -> Iterator[requests.Session]:
    session = requests.Session()
    session.headers.setdefault("User-Agent", "pytest-http-client")
    yield session
    session.close()
