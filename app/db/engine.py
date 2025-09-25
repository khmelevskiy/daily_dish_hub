"""Database engine configuration."""

from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


def create_database_url(*, prefer_external: bool = False) -> str:
    """Create database URL from settings.

    When ``prefer_external`` is True and external host/port overrides are provided,
    they are used instead of the default in-cluster coordinates. This mirrors the
    behaviour expected by local tooling (alembic, CLI scripts, etc.).
    """
    if settings.database_url:
        return settings.database_url

    user = settings.postgres_user
    password = settings.postgres_password
    host = (
        settings.postgres_host_external
        if prefer_external and settings.postgres_host_external
        else settings.postgres_host
    )
    port = (
        settings.postgres_port_external
        if prefer_external and settings.postgres_port_external
        else settings.postgres_port
    )
    db_name = settings.postgres_db

    if not all([user, host, db_name]):
        raise RuntimeError(
            "Database configuration is incomplete. Set DATABASE_URL or POSTGRES_{USER,PASSWORD,HOST,DB}."
        )

    safe_password = f":{quote_plus(password)}" if password else ""

    return f"postgresql+asyncpg://{quote_plus(user)}{safe_password}@{host}:{port}/{quote_plus(db_name)}"


def create_engine(db_url: str) -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(db_url, future=True, echo=False)
