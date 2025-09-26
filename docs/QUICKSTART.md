# 🚀 Quickstart Guide

## 1. 🧰 Prerequisites

- macOS Terminal (used during development).
- Docker **or** Python 3.13 + Node.js 18 +.
- If you run the backend locally without Docker, install system libraries required by Pillow/HEIF support (Debian/Ubuntu example: `sudo apt-get install libheif1 libde265-0 libjpeg62-turbo libtiff6 libwebp7 libopenjp2-7`).
- Telegram account to create a bot (free).
- ngrok account if you plan to share the local instance temporarily.

## 2. 📥 Clone the repository

```bash
git clone https://github.com/khmelevskiy/daily_dish_hub.git
cd daily_dish_hub
```

## 3. 🧾 Copy the environment template

Just run `setup.sh` or manually steps:

```bash
cp env.example .env
```

Fill the following keys in `.env`:

- `SECRET_KEY` – generate with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `POSTGRES_PASSWORD` – any password (used by Docker Postgres).
- `BOT_TOKEN` – obtained from BotFather (next step).
  Optional but handy:
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` – bootstrap the first admin account.
- Other important environment variables to fill out are marked `❗️`

For local development without Docker:

- Set `POSTGRES_HOST=localhost` (instead of 'db' which is for Docker)
- Set `POSTGRES_PORT=5433` (or whatever port your local Postgres uses)
- Make sure your local Postgres is running and accessible with these credentials

## 4. 🤖 Create a Telegram bot (one time)

1. Open Telegram and chat with [@BotFather](https://t.me/BotFather).
2. Open UI for settings or just chat:
   1. Send `/newbot` and follow the prompts.
   2. Copy the token and paste it into `.env` as `BOT_TOKEN=<your-token>`.
   3. (Optional) Upload an avatar and description via BotFather → `/mybots`.
   4. Add commands `start, menu and help`
   5. (Optional) Add your public url to `Menu Button` and `Main App` (UI bot father -> your bot -> Mini Apps)

## 5. ▶️ Run the stack

### Option A — Docker

```bash
./scripts/run_docker.sh build
./scripts/run_docker.sh up
```

Services start in the background: web app, Telegram bot, PostgreSQL, Redis (for rate limiting). Stop them with `./scripts/run_docker.sh down`.

### Option B — Local development

```bash
./scripts/setup.sh
./scripts/run_web.sh        # FastAPI + React, reload enabled
./scripts/run_bot.sh        # Telegram bot (separate terminal)
```

ℹ️ Both scripts expect PostgreSQL and Redis to be running. The easiest way is to start them in parallel via `./scripts/run_docker.sh up`. If you prefer to use your own instances, set `POSTGRES_HOST`/`POSTGRES_PORT` in `.env` to your local values and switch `RATE_LIMIT_BACKEND=memory` (or provide the URL of your Redis).

Need an admin later? Run `uv run python scripts/create_admin.py` to add one interactively.

## 6. ✅ Check that it works

- Public site: <http://localhost:8000/>
- Admin dashboard: <http://localhost:8000/admin>
- API health: <http://localhost:8000/health>
- Telegram: send `/start` to your bot; try `/menu`.

## 7. 🏭 Production deployment

For production deployment, update these settings in `.env`:

- `ENV=production` - enables production-specific security settings
- `TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com` - restrict to your domains
- `ENABLE_PROXY_HEADERS=true` - if behind nginx/load balancer
- `TRUSTED_PROXIES=127.0.0.1` - IP of your proxy server
- `JWT_ISSUER=daily_dish_hub` - who issued the token (your app name)
- `JWT_AUDIENCE=admin-panel` - who should use the token (admin interface)

## 8. ➡️ Next steps

- Read [README.md](README.md) for architecture details.
- Dive deeper into flows via [Daily_Dish_Hub_Technical_Atlas.md](Daily_Dish_Hub_Technical_Atlas.md).
- Harden your deployment with [SECURITY.md](SECURITY.md).
- Contribute improvements following [../CONTRIBUTING.md](../CONTRIBUTING.md).
