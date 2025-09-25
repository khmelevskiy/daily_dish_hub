"""Command handlers for the Telegram bot."""

from aiogram.types import Message

from app.services import BotService


async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    # Received /start command from user {message.from_user.id if message.from_user else 'unknown'}
    welcome_message = BotService.get_welcome_message()
    await message.answer(welcome_message)


async def cmd_menu(message: Message) -> None:
    """Handle /menu command."""
    try:
        from app.db import session_scope

        async with session_scope() as session:
            menu_text = await BotService.get_simple_menu_text(session=session)

            if len(menu_text) > 4096:
                # Split into parts if too long
                parts = [menu_text[i : i + 4096] for i in range(0, len(menu_text), 4096)]
                for part in parts:
                    await message.answer(part)
            else:
                await message.answer(menu_text)

    except Exception:
        await message.answer("Error loading the menu. Please try again later.")


async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_message = BotService.get_help_message()
    await message.answer(help_message)
