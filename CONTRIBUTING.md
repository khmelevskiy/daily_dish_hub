# 🤝 Contributing to Daily Dish Hub

## 🚀 Getting Started

1. Fork & clone the repository.
2. Follow the [Quickstart](docs/QUICKSTART.md) to configure `.env`, create a Telegram bot token, and launch the stack (Docker or local).
3. Run `./scripts/setup.sh` once if you are developing locally. It installs Python dependencies (via `uv`), npm packages, and pre-commit hooks.
4. Fill `.env` with your settings (see `.env.example`).

## 🔄 Everyday developer workflow

```bash
./scripts/run_web.sh   # FastAPI + React (reload)
./scripts/run_bot.sh   # Telegram bot worker
```

If you rely on Docker, use `./scripts/run_docker.sh up` instead. Keep Postgres and Redis running while you iterate.

## ✅ Tests & quality

- You can run all tests with `tests/run_all.sh`, or run only the specific tests you need.

## 🐞 Reporting issues

- For security vulnerabilities, follow [SECURITY.md](docs/SECURITY.md) and create a issue.
- For bugs, include reproduction steps and environment details (Docker vs local, OS, etc.).
- For ideas, describe the user scenario you want to improve.

Thank you for contributing! Every improvement helps other teams launch their menu bot faster.
