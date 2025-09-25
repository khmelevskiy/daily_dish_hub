#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def run_migration_command(args: list[str], description: str):
    """Run an Alembic command (argument-safe).

    Accepts a list of arguments to avoid shell quoting pitfalls (e.g. -m messages with spaces).
    """
    print(f"🔄 {description}...")

    cmd = ["uv", "run", "alembic", *args]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False

    print(f"✅ {description} completed successfully")
    if result.stdout.strip():
        print(result.stdout)

    return True


def main():
    """CLI for Alembic migrations."""
    if len(sys.argv) < 2:
        print(
            """
🚀 Alembic migration helper

Usage:
  python scripts/migrate.py <command>

Commands:
  upgrade     - Apply all migrations
  downgrade   - Revert last migration
  current     - Show current version
  history     - Show migration history
  revision    - Create new migration (requires message)
  init        - Initialize database

Examples:
  python scripts/migrate.py upgrade
  python scripts/migrate.py revision "Add new table"
  python scripts/migrate.py current
            """
        )
        return

    command = sys.argv[1]

    if command == "upgrade":
        run_migration_command(["upgrade", "head"], "Applying all migrations")

    elif command == "downgrade":
        run_migration_command(["downgrade", "-1"], "Reverting last migration")

    elif command == "current":
        run_migration_command(["current"], "Showing current version")

    elif command == "history":
        run_migration_command(["history"], "Showing migration history")

    elif command == "revision":
        if len(sys.argv) < 3:
            print("❌ The 'revision' command requires a message")
            print("Example: python scripts/migrate.py revision 'Add new table'")
            return
        message = sys.argv[2]
        run_migration_command(["revision", "--autogenerate", "-m", message], f"Creating migration: {message}")

    elif command == "init":
        print("🚀 Initializing database...")
        if run_migration_command(["upgrade", "head"], "Applying migrations"):
            print("✅ Database initialized successfully!")
        else:
            print("❌ Database initialization error")

    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python scripts/migrate.py' for help")


if __name__ == "__main__":
    # sys.argv.append("current") # for direct launch from IDE

    main()
