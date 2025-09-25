#!/bin/bash

# Docker management script
# Usage: ./scripts/run_docker.sh [build|up|down|logs|restart]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Resolve docker compose command (plugin preferred)
if docker compose version >/dev/null 2>&1; then
  dc() { docker compose "$@"; }
elif command -v docker-compose >/dev/null 2>&1; then
  dc() { docker-compose "$@"; }
else
  echo "❌ Neither 'docker compose' nor 'docker-compose' found. Install Docker Desktop or docker-compose."
  exit 1
fi

# Check docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in project root"
    exit 1
fi

# Check .env presence
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📋 Create .env from env.example:"
    echo "   cp env.example .env"
    echo "   # Then edit .env and add your settings"
    echo ""
    read -p "Continue without .env file? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Help
show_help() {
    echo "🐳 Docker helper for Daily Dish Hub"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build     - Build Docker images"
    echo "  up        - Start app (web + bot)"
    echo "  up-web    - Start web only"
    echo "  up-bot    - Start bot only"
    echo "  down      - Stop app (quick)"
    echo "  full-down - Full stop and prune images/volumes (slow)"
    echo "  restart   - Restart app"
    echo "  logs      - Show all logs"
    echo "  logs-web  - Show web logs"
    echo "  logs-bot  - Show bot logs"
    echo "  clean     - Clean Docker (remove project images/containers)"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 build   # Build image"
    echo "  $0 up      # Start all"
    echo "  $0 up-web  # Web only"
    echo "  $0 up-bot  # Bot only"
    echo "  $0 logs    # All logs"
    echo "  $0 logs-bot # Bot logs"
    echo "  $0 down    # Stop"
}

# Build
build() {
    echo "🔨 Building Docker images..."
    dc build
    echo "✅ Build finished!"
}

# Start (web + bot)
up() {
    echo "🚀 Starting app in Docker (web + bot)..."
    dc up -d
  echo "✅ App is running!"
  echo ""
  echo "🌐 URLs:"
  echo "   Public menu: http://localhost:8000/"
  echo "   Admin:       http://localhost:8000/admin"
  echo "   Database:    localhost:5433"
  echo ""
  echo "🤖 Services:"
    echo "   Web app:   ✅ Running"
    echo "   Telegram bot: ✅ Running"
    echo ""
    echo "📋 Useful commands:"
    echo "   $0 logs      # Show all logs"
    echo "   $0 logs-web  # Web logs"
    echo "   $0 logs-bot  # Bot logs"
    echo "   $0 down      # Stop app"
}

# Start web only
up_web() {
    echo "🌐 Starting web only..."
    dc up -d app db
    echo "✅ Web app is running!"
    echo ""
    echo "🌐 URLs:"
    echo "   Public menu: http://localhost:8000/"
    echo "   Admin:       http://localhost:8000/admin"
    echo ""
    echo "📋 Useful commands:"
    echo "   $0 logs-web  # Web logs"
    echo "   $0 up        # Start all (including bot)"
}

# Start bot only
up_bot() {
    echo "🤖 Starting bot only..."
    dc up -d bot db
    echo "✅ Bot is running!"
    echo ""
    echo "📋 Useful commands:"
    echo "   $0 logs-bot  # Bot logs"
    echo "   $0 up        # Start all (including web)"
}

# Stop
down() {
    echo "🛑 Stopping app..."
    dc down
    echo "✅ App stopped!"
}

# Full stop
full_down() {
    echo "🛑 Full stop (remove images and volumes)..."
    dc down --rmi all --volumes --remove-orphans
    echo "✅ App fully stopped and cleaned!"
}

# Restart
restart() {
    echo "🔄 Restarting app..."
    dc restart
    echo "✅ App restarted!"
}

# Logs
logs() {
    echo "📋 Logs for all services:"
    dc logs -f
}

# Web logs
logs_web() {
    echo "🌐 Web logs:"
    dc logs -f app
}

# Bot logs
logs_bot() {
    echo "🤖 Telegram bot logs:"
    dc logs -f bot
}

# Clean
clean() {
    echo "🧹 Cleaning Docker..."
    echo "⚠️  This will remove all project images and containers!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dc down --rmi all --volumes --remove-orphans
        echo "✅ Cleanup complete!"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Main logic
case "${1:-help}" in
    build)
        build
        ;;
    up)
        up
        ;;
    up-web)
        up_web
        ;;
    up-bot)
        up_bot
        ;;
    down)
        down
        ;;
    full-down)
        full_down
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    logs-web)
        logs_web
        ;;
    logs-bot)
        logs_bot
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
