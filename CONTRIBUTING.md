# Contributing to Daily Dish Hub

Thanks for helping this project grow! Please keep contributions simple, secure, and well documented so newcomers can run the stack without surprises.

## Getting Started

1. Fork & clone the repository.
2. Follow the [Quickstart](QUICKSTART.md) to configure `.env`, create a Telegram bot token, and launch the stack (Docker or local).
3. Run `./scripts/setup.sh` once if you are developing locally. It installs Python dependencies (via `uv`), npm packages, and pre-commit hooks.

## Everyday developer workflow

```bash
./scripts/run_web.sh   # FastAPI + React (reload)
./scripts/run_bot.sh   # Telegram bot worker
```

If you rely on Docker, use `./scripts/run_docker.sh up` instead. Keep Postgres and Redis running while you iterate.

### Admin account

Set `ADMIN_USERNAME`/`ADMIN_PASSWORD` in `.env` before first start or run `uv run python scripts/create_admin.py` to create one interactively.

## Tests & quality

- Security + rate limiting suite: `bash tests/run_all.sh -b http://localhost:8000`
- Individual pytest files can be run against a live server (`pytest tests/test_security.py`).
- Unit tests for helpers: `pytest -q tests/test_utils_unit.py tests/test_image_service_unit.py`

Before opening a PR:

- ✅ `ruff` and `ruff-format` will run via pre-commit; make sure they pass.
- ✅ Update [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) placeholders if your change affects the UI.
- ✅ Mention new environment variables or steps in [README.md](README.md) / [QUICKSTART.md](QUICKSTART.md).
- ✅ Keep secrets out of commits; `.env` is never committed.

## Pull request guidelines

- Provide a clear description of the feature/fix and any migration impact.
- Add or update tests when behaviour changes.
- Update documentation for anything that affects setup, tooling, or user flows.
- Keep UI texts in English by default.

## Reporting issues

- For security vulnerabilities, follow [SECURITY.md](SECURITY.md) and reach out privately.
- For bugs, include reproduction steps and environment details (Docker vs local, OS, etc.).
- For ideas, describe the user scenario you want to improve.

Thank you for contributing! Every improvement helps other teams launch their menu bot faster.
