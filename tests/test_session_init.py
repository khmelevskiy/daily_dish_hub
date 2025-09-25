#!/usr/bin/env python3
"""Tests for database session initialization idempotency."""

import sys

import pytest

from app.db import session as session_module


@pytest.fixture(autouse=True)
def reset_session_state():
    """Ensure module-level state is reset before and after each test."""
    session_module._engine = None  # type: ignore[attr-defined]
    session_module._session_factory = None  # type: ignore[attr-defined]
    session_module._engine_url = None  # type: ignore[attr-defined]
    yield
    session_module._engine = None  # type: ignore[attr-defined]
    session_module._session_factory = None  # type: ignore[attr-defined]
    session_module._engine_url = None  # type: ignore[attr-defined]


def test_init_database_idempotent(monkeypatch, caplog):
    calls: list[str] = []

    class DummyEngine:
        def __init__(self, url: str) -> None:
            self.url = url

    def fake_create_database_url(*, prefer_external: bool = False) -> str:
        return "postgresql://external" if prefer_external else "postgresql://internal"

    def fake_create_engine(db_url: str):
        calls.append(db_url)
        return DummyEngine(db_url)

    def fake_sessionmaker(engine, expire_on_commit: bool = False):  # noqa: ANN001 - signature mirrors async_sessionmaker
        return (engine, expire_on_commit)

    monkeypatch.setattr(session_module, "create_database_url", fake_create_database_url)
    monkeypatch.setattr(session_module, "create_engine", fake_create_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_sessionmaker)

    session_module.init_database()
    engine_first = session_module._engine
    session_module.init_database()

    assert session_module._engine is engine_first
    assert calls == ["postgresql://internal"]

    with caplog.at_level("WARNING"):
        session_module.init_database(prefer_external=True)

    assert session_module._engine is engine_first
    assert calls == ["postgresql://internal"], "Engine should not be recreated"
    assert "init_database called with prefer_external" in caplog.text


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
