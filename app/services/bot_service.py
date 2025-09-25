from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.formatting import format_price, to_decimal
from app.services.menu_service import MenuService


class BotService:
    @staticmethod
    async def get_simple_menu_text(session: AsyncSession) -> str:
        """Get a simple text menu for the bot."""
        daily_menu = await MenuService.get_current_menu(session=session)
        if not daily_menu:
            return "🍽️ Menu is not ready yet."

        menu_items = await MenuService.get_current_menu_items(session=session)
        if not menu_items:
            return "🍽️ Today's menu is empty."

        # Group items by category

        categories = defaultdict(list)
        for item in menu_items:
            category_title = item["category_title"] or "Uncategorized"
            categories[category_title].append(item)

        # Build text
        menu_text = "🍽️ Current Menu\n\n"

        for category_title, items in categories.items():
            menu_text += f"📂 {category_title}:\n"
            for item in items:
                price = to_decimal(item["price"])
                unit_name = item["unit_name"] or "portion"
                menu_text += f"• {item['name']} - {format_price(price)}/{unit_name}\n"
            menu_text += "\n"

        menu_text += "\n🌐 The full menu with photos is available in the Telegram web app (click the 'Menu' button)."

        return menu_text

    @staticmethod
    def get_welcome_message() -> str:
        """Welcome message."""
        return (
            "🍽️ Welcome to the canteen menu bot!\n\n"
            "Available commands:\n"
            "📋 /menu - Show today's menu\n"
            "❓ /help - Help\n\n"
            "Choose a command, type /menu to view the menu, or tap the 'Menu' button (recommended)"
        )

    @staticmethod
    def get_help_message() -> str:
        """Help message."""
        return (
            "❓ Help\n\n"
            "📋 /menu - Show text version of today's menu\n"
            "🏠 /start - Back to main\n\n"
            "💡 Tip: Open the web menu using the 'Menu' button at the top"
        )
