# Daily Dish Hub

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat-square&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![FastAPI 0.117.1](https://img.shields.io/badge/FastAPI-0.117.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![React 19.1](https://img.shields.io/badge/React-19.1-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![License MIT](https://img.shields.io/badge/License-MIT-000000?style=flat-square&logo=opensourceinitiative&logoColor=white)](LICENSE)

Simple full-stack toolkit for running a “menu of the day” canteen. The stack includes a FastAPI backend, React admin UI, PostgreSQL storage, and a Telegram bot for guests who prefer chat.

> Quick links: [Quickstart](QUICKSTART.md) · [Architecture](docs/README.md) · [Security checklist](SECURITY.md) · [Screenshots placeholders](docs/SCREENSHOTS.md)

## What you get

- Web admin UI to create categories, dishes, and daily menus.
- Public site that shows today’s menu.
- Telegram bot commands (`/menu`, `/start`, `/help`) for quick lookups.
- Image uploads with automatic JPEG conversion.
- Secure defaults: JWT auth, bcrypt password hashing, rate limiting, CSP, hardened middleware.

## Launch in 5 minutes

### Prerequisites

- Python 3.13 (if you are running the backend locally without Docker).
- Node.js 18 or newer.
- System image libraries for Pillow/HEIF support: `libheif1`, `libde265-0`, `libjpeg62-turbo`, `libtiff6`, `libwebp7`, `libopenjp2-7` (install via `apt-get` on Debian/Ubuntu or the equivalents for your platform).

### 1. Clone and prepare

```bash
git clone https://github.com/khmelevskiy/daily_dish_hub.git
cd daily_dish_hub
cp env.example .env
```

Generate secrets and fill the new .env (ensure your IDE loads environment variables, or define them manually):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"  # SECRET_KEY
```

Minimum values to set:

- `SECRET_KEY` – 32+ random characters.
- `POSTGRES_PASSWORD` – database password used by Docker (any value you like).
- `BOT_TOKEN` – Telegram token (see next step).
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` to auto-create the first admin.

### 2. Create a Telegram bot (one time)

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a display name, then a unique username (must end with `bot`).
3. Copy the token BotFather returns.
4. Paste that value into `.env` as `BOT_TOKEN=...`.
5. (Optional) Send `/mybots` → choose your bot → *Bot Settings* to upload an avatar and description.

### 3. Start the stack

#### Option A – Docker (fastest)**

```bash
./scripts/run_docker.sh build
./scripts/run_docker.sh up
# First start creates the database, applies migrations, and seeds default data
```

URLs:

- Public site: <http://localhost:8000/>
- Admin UI: <http://localhost:8000/admin>
- API health: <http://localhost:8000/health>

#### Option B – Local development (uv + Node)**

```bash
./scripts/setup.sh            # installs Python deps, npm packages, pre-commit hooks
./scripts/run_web.sh          # FastAPI + bundled React (reload enabled)
./scripts/run_bot.sh          # Telegram bot in a separate terminal
```

Need an admin user? Either set `ADMIN_USERNAME`/`ADMIN_PASSWORD` before the first launch **or** run:

```bash
uv run python scripts/create_admin.py
```

### 4. Explore and take notes

- Log into the admin UI (credentials from `.env` or the `create_admin.py` script).
- Build a menu, upload images, and confirm the Telegram bot answers `/menu`.
- Drop placeholders for screenshots in [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) (see instructions inside).

## Share your local instance quickly (ngrok)

Want colleagues to test the menu remotely? You can expose port 8000 using [ngrok](https://ngrok.com/).

1. Install the Docker ngrok extension (`docker extension install ngrok/ngrok-for-docker`) or enable it via Docker Desktop → Extensions.
2. Start the stack: `docker compose up`.
3. In the ngrok extension, start an HTTP tunnel to port 8000 and copy the forwarding URL.
4. In BotFather, go to your bot → *Mini Apps* → add that URL both to **Menu Button** and **Main App**.

## Production notes

- Generate a strong `SECRET_KEY` (>=32 random characters) and keep it outside version control; rotate it if leaked.
- Set `ENV=production` to enforce production-specific security defaults.
- Set `TRUSTED_HOSTS` to your real domain and serve the app behind HTTPS (nginx, Caddy, Traefik, etc.).
- Keep docs disabled in public environments (`DISABLE_DOCS=true`).
- Enable `ENABLE_PROXY_HEADERS=true` plus `FORWARDED_ALLOW_IPS`/`TRUSTED_PROXIES` when running behind a load balancer.
- Keep `.env` secrets out of version control; rotate tokens if leaked.
- For enhanced JWT security, set `JWT_ISSUER` and `JWT_AUDIENCE` to restrict token usage.
- Prefer Redis rate limiting (`RATE_LIMIT_BACKEND=redis`) for multi-instance deployments.
- Use a managed PostgreSQL instance and persistent storage.

## Documentation & support

- Architecture, data flow, and API summary live in [docs/README.md](docs/README.md).
- Docker tricks: [DOCKER.md](DOCKER.md)
- Quick step-by-step cheat sheet: [QUICKSTART.md](QUICKSTART.md)
- Contribution guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)
- CI: GitHub Actions runs backend Ruff lint/format checks and frontend lint/tests (`.github/workflows/ci.yml`).

## Security reminder

Read [SECURITY.md](SECURITY.md) before exposing the project to the internet. The application refuses to start in production mode when `SECRET_KEY` or `TRUSTED_HOSTS` are missing on purpose—keep those protections in place.

Happy cooking!
