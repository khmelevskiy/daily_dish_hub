# 🍽️ Daily Dish Hub

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI 0.117.1](https://img.shields.io/badge/FastAPI-0.117.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19.1](https://img.shields.io/badge/React-19.1-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![License MIT](https://img.shields.io/badge/License-MIT-000000?style=flat-square&logo=opensourceinitiative&logoColor=white)](LICENSE)

Simple full-stack toolkit for running a “menu of the day” canteen. The stack includes a FastAPI backend, React admin UI, PostgreSQL storage, and a Telegram bot for guests who prefer chat.

> Quick links: [Quickstart](docs/QUICKSTART.md) · [Architecture](docs/README.md) · [Security checklist](docs/SECURITY.md) · [Screenshots plan](docs/SCREENSHOTS.md)

## 🎯 What you get

- Web admin UI to create categories, dishes, and daily menus.
- Public site that shows today’s menu.
- Telegram bot commands (`/menu`, `/start`, `/help`) for quick lookups.
- Image uploads with automatic JPEG conversion.
- Secure defaults: JWT auth, bcrypt password hashing, rate limiting, CSP, hardened middleware.

## 📸 Screenshots

![Public menu](docs/pics/web_menu.png)

![Admin dashboard](docs/pics/web_admin.png)

## 🚀 Getting started

- Follow the step-by-step [Quickstart](docs/QUICKSTART.md) to clone the repo, configure `.env`, create the Telegram bot, and run the stack (Docker or local).
- Need a one-liner? `./scripts/run_docker.sh up` builds the image, runs migrations, and starts the full stack; `./scripts/run_docker.sh down` stops it.
- Create an admin at any time with `uv run python scripts/create_admin.py` (or set credentials in `.env` before the first launch).
- Capture or review planned screenshots listed in [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md).

## 🌐 Share your local instance quickly (ngrok)

Want colleagues to test the menu remotely? You can expose port 8000 using [ngrok](https://ngrok.com/).

1. Install the Docker ngrok extension (`docker extension install ngrok/ngrok-for-docker`) or enable it via Docker Desktop → Extensions.
2. Start the stack: `docker compose up`.
3. In the ngrok extension, start an HTTP tunnel to port 8000 and copy the forwarding URL.
4. In BotFather, go to your bot → *Mini Apps* → add that URL both to **Menu Button** and **Main App**.

## 🏭 Production notes

- Generate a strong `SECRET_KEY` (>=32 random characters) and keep it outside version control; rotate it if leaked.
- Set `ENV=production` to enforce production-specific security defaults.
- Set `TRUSTED_HOSTS` to your real domain and serve the app behind HTTPS (nginx, Caddy, Traefik, etc.).
- Keep docs disabled in public environments (`DISABLE_DOCS=true`).
- Enable `ENABLE_PROXY_HEADERS=true` plus `FORWARDED_ALLOW_IPS`/`TRUSTED_PROXIES` when running behind a load balancer.
- Keep `.env` secrets out of version control; rotate tokens if leaked.
- For enhanced JWT security, set `JWT_ISSUER` and `JWT_AUDIENCE` to restrict token usage.
- Prefer Redis rate limiting (`RATE_LIMIT_BACKEND=redis`) for multi-instance deployments.
- Use a managed PostgreSQL instance and persistent storage.

## 📚 Documentation & support

- Architecture overview: [docs/README.md](docs/README.md)
- Quickstart walkthrough: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Docker playbook: [docs/DOCKER.md](docs/DOCKER.md)
- Security checklist: [docs/SECURITY.md](docs/SECURITY.md)
- Technical atlas (flows & diagrams): [docs/Daily_Dish_Hub_Technical_Atlas.md](docs/Daily_Dish_Hub_Technical_Atlas.md)
- Screenshot plan: [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md)
- Roadmap & chores: [docs/TODO.md](docs/TODO.md)
- Testing guide: [tests/README.md](tests/README.md)
- Contribution guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)
- Schema diagram: [docs/pics/db_schema.png](docs/pics/db_schema.png)
- Syntax checks workflow: `.github/workflows/syntax-checks.yml` (ruff lint/format, detect-secrets scan, frontend lint/tests)

## ⚠️ Security reminder

Read [docs/SECURITY.md](docs/SECURITY.md) before exposing the project to the internet. The application refuses to start in production mode when `SECRET_KEY` or `TRUSTED_HOSTS` are missing on purpose—keep those protections in place.

Happy cooking!
