#!/usr/bin/env python3
"""Database initialization script
- Checks DB existence
- Runs Alembic migrations
- Seeds initial data if the DB is empty.
"""

import asyncio
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncpg  # noqa: E402
from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db import create_database_url, init_database  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.unit import Unit  # noqa: E402
from app.models.user import User  # noqa: E402


async def check_database_exists():
    """Return True if database exists."""
    try:
        init_database(prefer_external=True)
        from app.db import get_engine

        engine = get_engine()
        if engine is None:
            return False

        # Try to connect to DB
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        if "does not exist" in str(e).lower() or "database" in str(e).lower():
            return False
        raise


def _quote_pg_identifier(identifier: str) -> str:
    """Return a PostgreSQL-safe identifier with minimal quoting."""
    if not identifier:
        raise ValueError("Database name cannot be empty")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        return identifier
    return '"' + identifier.replace('"', '""') + '"'


async def create_database():
    """Create database if it does not exist (PostgreSQL), robust to special chars."""
    database_url = create_database_url(prefer_external=True)

    from sqlalchemy.engine.url import make_url

    url = make_url(database_url)
    user = url.username or ""
    password = url.password or ""
    host = settings.postgres_host_external or url.host or "localhost"
    port = settings.postgres_port_external or url.port or 5433
    dbname = url.database or "postgres"

    # Short-circuit if the database already exists.
    try:
        existing = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
        )
    except asyncpg.InvalidCatalogNameError:
        existing = None
    except Exception as exc:
        print(f"❌ Error checking database existence: {exc}")
        return False
    else:
        await existing.close()
        print(f"ℹ️ Database {dbname} already exists")

        return True

    # Connect to the control database ('postgres') to create the target DB.
    try:
        control_conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres",
        )
    except asyncpg.InvalidCatalogNameError:
        print("❌ Control database 'postgres' is not available; create the target database manually.")
        return False
    except Exception as exc:
        print(f"❌ Unable to connect to control database: {exc}")
        return False

    try:
        rendered_name = _quote_pg_identifier(dbname)
        await control_conn.execute(f"CREATE DATABASE {rendered_name}")
        print(f"✅ Database {dbname} created")

        return True
    except asyncpg.DuplicateDatabaseError:
        print(f"ℹ️ Database {dbname} already exists")
        return True
    except Exception as exc:
        print(f"❌ Database creation error: {exc}")
        return False
    finally:
        await control_conn.close()


async def run_migrations():
    """Run Alembic migrations."""
    print("🔄 Running Alembic migrations...")

    try:
        import subprocess

        # Apply migrations
        print("🔄 Applying existing migrations...")
        result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)

        if result.stdout and "Running upgrade" in result.stdout:
            print("✅ Migrations applied")
        else:
            print("ℹ️ No migrations required (DB is up to date)")

        # Check for schema drift between code and database
        print("🔍 Checking schema matches code...")
        try:
            result = subprocess.run(
                ["alembic", "check"],
                check=True,
                capture_output=True,
                text=True,
            )
            print("✅ DB schema matches code")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            stdout = e.stdout or ""
            combined_output = f"{stdout}\n{stderr}".strip()
            combined_lower = combined_output.lower()

            if "no such command" in combined_lower and "check" in combined_lower:
                print("⚠️ Alembic 'check' command not available; skipping drift check")
            else:
                print("❌ SCHEMA MISMATCH DETECTED!")
                print("📋 To fix, run:")
                print("   1. Create migration:")
                print("      uv run alembic revision --autogenerate -m 'Describe changes'")
                print("   2. Rebuild and start app:")
                print("      ./scripts/run_docker.sh build && ./scripts/run_docker.sh up")
                print("🚫 App stopped due to schema mismatch")

                return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Migration execution error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("⚠️ Alembic not found, skipping migrations")
        return True

    return True


async def check_if_database_empty():
    """Check if the database is empty."""
    from app.db import session_scope

    async with session_scope() as session:
        try:
            # Check presence of data in core tables
            result = await session.execute(select(Category))
            categories = result.scalars().all()

            result = await session.execute(select(Unit))
            units = result.scalars().all()

            result = await session.execute(select(User))
            users = result.scalars().all()

            return len(categories) == 0 and len(units) == 0 and len(users) == 0
        except Exception:
            # If tables do not exist, treat DB as empty
            return True


async def initialize_database():
    """Initialize DB, run migrations and seed data."""
    from app.db import session_scope
    from app.schemas.auth import UserCreate
    from app.services import UserService

    print("🔗 Connecting to database...")

    # Ensure DB exists
    if not await check_database_exists():
        print("📋 Database does not exist, creating...")
        if not await create_database():
            print("❌ Failed to create database")
            return False

    # Run migrations (create schema)
    if not await run_migrations():
        print("❌ Migration error")
        return False

    # Seeding of initial categories/units is handled by the web app on startup
    print("ℹ️ Initial data (categories/units) will be ensured by the web app at startup")

    # Create first admin from env
    admin_username = settings.admin_username
    admin_password = settings.admin_password

    if not admin_username or not admin_password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment")

    print(f"👤 Creating first admin: {admin_username}")
    async with session_scope() as session:
        existing = await UserService.get_user_by_username(session=session, username=admin_username)
        if existing:
            print(f"ℹ️ Admin '{admin_username}' already exists, skipping")
        else:
            admin_data = UserCreate(username=admin_username, password=admin_password, is_admin=True)
            await UserService.create_user(session=session, user_data=admin_data)
            print(f"✅ Admin {admin_username} created successfully!")

    print("✅ Database initialized successfully!")

    return True


def main() -> None:
    success = asyncio.run(initialize_database())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
