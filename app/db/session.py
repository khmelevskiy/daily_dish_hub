"""Database session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db.engine import create_database_url, create_engine


logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_engine_url: str | None = None


def init_database(*, prefer_external: bool = False) -> None:
    """Initialize database engine and session factory.

    ``prefer_external`` mirrors Alembic's behaviour: when running tools outside the
    container network we prefer the externally exposed host/port if configured.
    Repeated calls reuse the existing engine to avoid leaking connections.
    """
    global _engine, _session_factory, _engine_url

    database_url = create_database_url(prefer_external=prefer_external)

    if _engine is not None:
        if _engine_url and _engine_url != database_url:
            logger.warning(
                "init_database called with prefer_external=%s but engine already initialized for %s; "
                "reusing existing engine",
                prefer_external,
                _engine_url,
            )
        return

    _engine = create_engine(db_url=database_url)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    _engine_url = database_url


def get_engine() -> AsyncEngine:
    """Get the database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return _engine


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager for database sessions.

    Provides automatic transaction management:
    - Commits on success
    - Rolls back on exception
    - Always closes the session
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def create_schema(base_class) -> None:
    """Create database schema for all models."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(base_class.metadata.create_all)
