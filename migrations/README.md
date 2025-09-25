# Alembic quick start

All migration commands run against the database configured via the usual environment variables (`DATABASE_URL` or `POSTGRES_*`). A few useful recipes:

- `uv run alembic revision --autogenerate -m "describe change"` – create a new migration from model diffs.
- `uv run alembic upgrade head` – apply migrations.
- `uv run alembic downgrade -1` – roll back the last migration.
- `uv run alembic upgrade head --sql` – generate SQL without executing it (handy for reviews).

For day-to-day work you can also use the helper CLI: `uv run python scripts/migrate.py <command>`. It wraps the same operations with friendlier output and safe argument handling.
