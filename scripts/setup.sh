#!/usr/bin/env bash
# Script to set up the development local environment.
set -euo pipefail

generate_secret_key() {
  if [ -r /dev/urandom ]; then
    local key
    key=$(LC_ALL=C tr -dc 'A-Za-z0-9-_' </dev/urandom | head -c 64 || true)
    if [ -n "$key" ]; then
      printf '%s\n' "$key"
      return 0
    fi
  fi

  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 48 | tr -d '\n' | head -c 64
    return 0
  fi

  echo "[ERROR] Unable to generate SECRET_KEY automatically (requires /dev/urandom or openssl)." >&2
  exit 1
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Args
# By default, do NOT build frontend during setup
# Use --build-frontend to enable build
NO_FRONTEND_BUILD=1
for arg in "$@"; do
  case "$arg" in
    --no-frontend-build)
      NO_FRONTEND_BUILD=1
      shift
      ;;
    --build-frontend)
      NO_FRONTEND_BUILD=0
      shift
      ;;
  esac
done

echo "[1/8] Checking uv..."
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found."
  if command -v brew >/dev/null 2>&1; then
    read -r -p "Install uv via Homebrew? [Y/n]: " REPLY
    REPLY=${REPLY:-Y}
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
      brew install uv || true
    fi
  fi
  if ! command -v uv >/dev/null 2>&1; then
    read -r -p "Install uv via official script (curl | sh)? [Y/n]: " REPLY
    REPLY=${REPLY:-Y}
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
      curl -LsSf https://astral.sh/uv/install.sh | sh || true
      # Ensure current shell can see installed binaries
      export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    fi
  fi
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv is required. Aborting." >&2
  exit 1
fi

echo "[2/8] Checking Node.js..."
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Install Node.js (https://nodejs.org/)" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js which provides npm" >&2
  exit 1
fi

# Ensure Node.js >= 18
NODE_VERSION_RAW=$(node -v 2>/dev/null || echo "v0.0.0")
NODE_VERSION=${NODE_VERSION_RAW#v}
NODE_MAJOR=${NODE_VERSION%%.*}
if [ "${NODE_MAJOR:-0}" -lt 18 ]; then
  echo "[ERROR] Node.js >= 18 is required (found ${NODE_VERSION})." >&2
  exit 1
fi
echo "[OK] Node.js ${NODE_VERSION} detected"

echo "[3/8] Checking Docker..."
if ! command -v docker >/dev/null 2>&1; then
  echo "[WARN] Docker CLI not found. Docker is recommended for DB and runtime." >&2
else
  if docker compose version >/dev/null 2>&1; then
    : # OK
  elif command -v docker-compose >/dev/null 2>&1; then
    : # fallback OK
  else
    echo "[WARN] Neither 'docker compose' plugin nor 'docker-compose' found. Install Docker Desktop." >&2
  fi
fi

echo "[4/8] Creating .env if missing..."
if [ ! -f .env ]; then
  if [ -f env.example ]; then
    cp env.example .env
    echo ".env created from env.example"
  else
    cat > .env <<'EOF'
BOT_TOKEN=your_telegram_bot_token_here
EOF
    echo "Minimal .env created"
  fi
fi

# Check SECRET_KEY is set
if ! grep -qE '^SECRET_KEY=' .env; then
  echo "[ERROR] SECRET_KEY is missing in .env"
  echo "Please set a strong SECRET_KEY manually:"
  echo "1. Edit .env file"
  echo "2. Set SECRET_KEY to a strong random string (at least 32 characters)"
  echo "3. Example: SECRET_KEY=❗your-very-long-and-random-secret-key-here❗"
  echo ""
  echo "You can generate a strong key using:"
  echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
  echo "  openssl rand -base64 48"
  echo ""
  exit 1
else
  # Extract the value after the first '=' (allow '=' inside value)
  SECRET_PLACEHOLDER="❗your-very-long-and-random-secret-key-here❗"
  SECRET_VAL="$(sed -n 's/^SECRET_KEY=\(.*\)$/\1/p' .env | head -n1)"
  if [ "$SECRET_VAL" = "$SECRET_PLACEHOLDER" ]; then
    echo "[INFO] SECRET_KEY placeholder detected; generating a new secret..."
    NEW_SECRET=$(generate_secret_key)
    if [ -z "$NEW_SECRET" ]; then
      echo "[ERROR] Failed to generate a SECRET_KEY automatically." >&2
      exit 1
    fi
    TMP_ENV=$(mktemp)
    if [ ! -f "$TMP_ENV" ]; then
      echo "[ERROR] Unable to create temporary file while updating SECRET_KEY." >&2
      exit 1
    fi
    awk -v key="$NEW_SECRET" 'BEGIN{replaced=0} \
      /^SECRET_KEY=/ && !replaced {print "SECRET_KEY=" key; replaced=1; next} \
      {print} \
      END{if(!replaced) print "SECRET_KEY=" key}' .env >"$TMP_ENV"
    mv "$TMP_ENV" .env
    SECRET_VAL="$NEW_SECRET"
    echo "[INFO] SECRET_KEY updated automatically."
  else
    echo "[INFO] SECRET_KEY already set; skipping auto-generation."
  fi
  SECRET_LEN=${#SECRET_VAL}
  # Warn if placeholder
  if printf "%s" "$SECRET_VAL" | grep -qiE '(your[-_ ]?secret|change[-_ ]?this|secret[-_ ]?key|placeholder)'; then
    echo "[ERROR] SECRET_KEY contains placeholder-like value"
    echo "Please update SECRET_KEY in .env to a strong random value before continuing"
    echo ""
    exit 1
  fi
  # Enforce minimum length 32
  if [ "$SECRET_LEN" -lt 32 ]; then
    echo "[ERROR] SECRET_KEY is too short ($SECRET_LEN chars). Use at least 32 characters."
    echo "Generate one with:"
    echo "  python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
    exit 1
  fi
  echo "[OK] SECRET_KEY is properly configured (length: $SECRET_LEN)"
fi

echo "[5/8] Cleaning legacy artifacts..."
rm -rf daily_dish_hub.egg-info || true

echo "[6/8] Installing dependencies..."
echo "  - Python deps (uv sync)..."
if [ ! -f uv.lock ]; then
  echo "[ERROR] uv.lock not found. Run 'uv lock' (or 'uv pip compile') to generate it before setup." >&2
  exit 1
fi
uv sync --frozen

echo "  - Node.js deps..."
if [ -d "frontend" ]; then
  cd frontend
  if [ ! -f package-lock.json ]; then
    echo "[ERROR] frontend/package-lock.json not found. Run 'npm install' inside frontend to generate it before setup." >&2
    exit 1
  fi
  npm ci
  cd ..

  if [ "$NO_FRONTEND_BUILD" -eq 0 ]; then
    echo "  - Building frontend (Vite)..."
    cd frontend
    npm run build
    cd ..
  else
    echo "  - Skipping frontend build (default). Pass --build-frontend to enable."
  fi
else
  echo "  - 'frontend' folder not found, skipping React build"
fi

echo "[7/8] Installing pre-commit hooks..."
if command -v pre-commit >/dev/null 2>&1; then
  :
else
  # Prefer uv tool if available
  if command -v uv >/dev/null 2>&1; then
    uv tool install pre-commit || true
  fi
  if ! command -v pre-commit >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      read -r -p "Install pre-commit via Homebrew? [Y/n]: " REPLY
      REPLY=${REPLY:-Y}
      if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        brew install pre-commit || true
      fi
    fi
  fi
  if ! command -v pre-commit >/dev/null 2>&1; then
    if command -v pipx >/dev/null 2>&1; then
      pipx install pre-commit || true
    fi
  fi
  if ! command -v pre-commit >/dev/null 2>&1; then
    read -r -p "Install pre-commit via pip --user? [y/N]: " REPLY
    REPLY=${REPLY:-N}
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
      python3 -m pip install --user pre-commit || true
      export PATH="$HOME/.local/bin:$PATH"
    fi
  fi
fi
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install || true
  echo "  - pre-commit installed"
else
  echo "[WARN] pre-commit not found; install later to enable git hooks." >&2
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Run options:"
echo ""
echo "🐳 Docker (recommended):"
echo "   ./scripts/run_docker.sh build  # Build image"
echo "   ./scripts/run_docker.sh up     # Start"
echo ""
echo "💻 Local development:"
echo "   ./scripts/run_bot.sh           # Start bot"
echo "   ./scripts/run_web.sh           # Start web"
echo ""
echo "📋 Extra commands:"
echo "   ./scripts/run_docker.sh help   # Docker help"
echo "   ./scripts/run_docker.sh logs   # Logs"
