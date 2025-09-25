"""Main bot application."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command

from app.bot.handlers import cmd_help, cmd_menu, cmd_start
from app.core.config import settings
from app.db import init_database


async def main() -> None:
    """Main bot function."""
    # Initialize database engine from environment
    init_database()
    settings.validate()
    token = (settings.bot_token or "").strip()

    if not token or "your_telegram_bot_token_here" in token:
        raise RuntimeError(
            "BOT_TOKEN is not configured. Set a real Telegram bot token in the environment before starting the bot."
        )

    bot = Bot(token=token)
    dp = Dispatcher()

    # Register command handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_menu, Command("menu"))
    dp.message.register(cmd_help, Command("help"))

    # Ensure DB schema
    # Schema is created automatically on startup

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def run_bot() -> None:
    """Entry point for uv run daily_dish_hub."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
