############################
# Stage 1: Frontend builder
############################
FROM node:18-alpine AS frontend-builder
WORKDIR /build

# Install deps and build (Vite)
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build:ci

############################
# Stage 2: Python runtime
############################
FROM python:3.13-slim AS runtime
WORKDIR /app

# Install only needed system deps
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    libheif1 \
    libde265-0 \
    libjpeg62-turbo \
    libtiff6 \
    libwebp7 \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (deterministic via uv.lock)
COPY pyproject.toml uv.lock README.md ./
RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev \
 && . .venv/bin/activate \
 && python -V
ENV PATH=/app/.venv/bin:${PATH}

# App code
COPY app app
COPY migrations migrations
COPY scripts scripts
COPY alembic.ini alembic.ini

# Static files from frontend builder (Vite)
RUN mkdir -p app/static
COPY --from=frontend-builder /build/dist/index.html app/static/
COPY --from=frontend-builder /build/dist/assets app/static/assets

# Permissions and user
RUN chmod +x scripts/init_db.py && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

# Startup script (supports optional proxy headers)
RUN cat <<'EOF_START' > /app/start.sh && chmod +x /app/start.sh
#!/bin/bash
set -euo pipefail

echo "🚀 Starting application..."

echo "🔗 Initializing database..."
python scripts/init_db.py

echo "🌐 Starting web server..."
cmd=(python -m uvicorn app.web:app --host 0.0.0.0 --port 8000)

case "$(echo "${ENABLE_PROXY_HEADERS:-}" | tr "[:upper:]" "[:lower:]")" in
  1|true|yes) cmd+=(--proxy-headers) ;;
esac

if [ -n "${FORWARDED_ALLOW_IPS:-}" ]; then
  cmd+=(--forwarded-allow-ips "${FORWARDED_ALLOW_IPS}")
fi

exec "${cmd[@]}"
EOF_START

CMD ["/app/start.sh"]
