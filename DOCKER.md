# Docker Guide

Use Docker when you want a repeatable environment without touching local Python/Node installations.

## 1. Prepare `.env`

Follow the main [Quickstart](QUICKSTART.md) through step 4. Docker reads exactly the same `.env` file.

Important values:

- `SECRET_KEY` – strong random string (32+ chars).
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` – used by the bundled PostgreSQL container (defaults in `env.example`).
- `BOT_TOKEN` – Telegram token from BotFather.
- Other important environment variables to fill out are marked `❗️`

## 2. Build and start

```bash
./scripts/run_docker.sh build   # builds the multi-stage image (frontend + backend)
./scripts/run_docker.sh up      # starts web, bot, postgres, redis
```

The `frontend-builder` stage compiles the Vite admin UI into `frontend/dist/`; the final image copies that bundle into `app/static/`.

First start initializes the database, applies Alembic migrations, seeds default categories/units, and creates the first admin if credentials are present in `.env`.

> The runtime image bundles the native libraries Pillow needs for HEIF/AVIF (`libheif1`, `libde265-0`, `libjpeg62-turbo`, `libtiff6`, `libwebp7`, `libopenjp2-7`), so image uploads work out of the box.

## 3. Helpful commands

- `./scripts/run_docker.sh logs` — follow logs from every service.
- `./scripts/run_docker.sh logs-web` / `logs-bot` — focus on a single service.
- `./scripts/run_docker.sh restart` — quick restart after changing environment variables.
- `./scripts/run_docker.sh down` — stop containers but keep volumes.
- `./scripts/run_docker.sh full-down` — stop everything and remove volumes/images.

## 4. Deploying beyond localhost

- Place the stack behind HTTPS (nginx, Traefik, Caddy, etc.).
- Update `TRUSTED_HOSTS` with your domain and set `ENABLE_PROXY_HEADERS=true` plus proxy CIDRs.
- Use persistent volumes or a managed PostgreSQL database.
- Adjust rate limits (`RATE_LIMIT_*`) for your real traffic profile.

That’s it—Docker keeps the workflow simple while preserving the project’s security defaults.

## 5. Expose the stack with ngrok (optional)

Want to share your local menu externally without deploying? You can use [ngrok](https://ngrok.com/) to tunnel port 8000 and get a public URL.

1. Install the Docker ngrok extension (`docker extension install ngrok/ngrok-for-docker`) or enable it from Docker Desktop → Extensions.
2. Start the stack as usual: `docker compose up --build`.
3. In the ngrok extension, start an HTTP tunnel to port 8000 and copy the forwarding URL.
4. In BotFather, go to your bot → *Mini Apps* → add that URL to both **Menu Button** and **Main App**.
