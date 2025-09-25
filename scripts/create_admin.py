#!/usr/bin/env python3
"""Utility to create additional admin users via direct database access.

Run this from your workstation to provision extra administrators; the script
automatically prefers external Postgres connection parameters when they are
configured (mirroring Alembic).
"""

import asyncio
import sys
from getpass import getpass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from app.db import init_database, session_scope  # noqa: E402
from app.schemas.auth import UserCreate  # noqa: E402
from app.services import UserService  # noqa: E402


async def create_admin():
    """Create an admin user interactively."""
    print("🔧 Create admin user")
    print("=" * 40)

    # Read input
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return

    password = getpass("Enter password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return

    confirm_password = getpass("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return

    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return

    try:
        # Initialize database (prefer external connection params if provided)
        init_database(prefer_external=True)

        async with session_scope() as session:
            # Check if user already exists
            existing_user = await UserService.get_user_by_username(session=session, username=username)
            if existing_user:
                print(f"❌ User with username '{username}' already exists")
                return

            # Create admin user
            user_data = UserCreate(username=username, password=password, is_admin=True)

            user = await UserService.create_user(session=session, user_data=user_data)

            print(f"✅ Admin '{username}' created successfully!")
            print(f"   ID: {user.id}")
            print(f"   Admin: {'Yes' if user.is_admin else 'No'}")
            print(f"   Active: {'Yes' if user.is_active else 'No'}")
            print("\n🔑 You can now sign in to the admin panel using these credentials")

    except Exception as e:
        print(f"❌ Error creating admin: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin())
