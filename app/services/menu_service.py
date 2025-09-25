from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.daily_menu import DailyMenu
from app.models.daily_menu_item import DailyMenuItem
from app.models.image import Image
from app.models.item import Item
from app.models.menu_settings import MenuSettings
from app.models.unit import Unit
from app.schemas.daily_menu import MenuDateInfo
from app.services.formatting import decimal_to_float
from app.services.image_service import ImageService


class MenuService:
    @staticmethod
    async def get_current_menu(session: AsyncSession) -> DailyMenu | None:
        """Get current active menu (the most recent one)."""
        result = await session.execute(select(DailyMenu).order_by(DailyMenu.created_at.desc()).limit(1))

        return result.scalar_one_or_none()

    @staticmethod
    async def create_current_menu(session: AsyncSession) -> DailyMenu:
        """Create new current menu."""
        daily_menu = DailyMenu()
        session.add(daily_menu)
        await session.flush()
        await session.refresh(daily_menu)

        return daily_menu

    @staticmethod
    async def get_or_create_current_menu(session: AsyncSession) -> DailyMenu:
        """Get or create current menu."""
        menu = await MenuService.get_current_menu(session=session)
        if not menu:
            menu = await MenuService.create_current_menu(session=session)

        return menu

    @staticmethod
    async def recreate_current_menu(session: AsyncSession, item_ids: list[int]) -> bool:
        """Recreate current menu with the provided items, removing all old menus."""
        unique_ids = list(dict.fromkeys(item_ids))
        if unique_ids:
            result = await session.execute(select(Item.id).where(Item.id.in_(unique_ids)))
            existing_ids = {row[0] for row in result.fetchall()}
            missing = set(unique_ids) - existing_ids
            if missing:
                return False

        # Use the deduplicated order-preserving list to avoid violating the
        # unique constraint on (daily_menu_id, item_id).
        item_ids = unique_ids

        # Delete ALL existing daily menus
        await session.execute(delete(DailyMenu))

        # Create fresh current menu
        daily_menu = DailyMenu()
        session.add(daily_menu)
        await session.flush()
        await session.refresh(daily_menu)

        # Add new items to the fresh menu
        for item_id in item_ids:
            menu_item = DailyMenuItem(daily_menu_id=daily_menu.id, item_id=item_id)
            session.add(menu_item)

        return True

    @staticmethod
    async def get_menu_date(session: AsyncSession) -> MenuDateInfo:
        """Get current menu date settings."""
        from datetime import datetime

        # Try to get saved date range
        result = await session.execute(select(MenuSettings).where(MenuSettings.key == "menu_date_range"))
        menu_settings = result.scalar_one_or_none()

        if menu_settings:
            import json

            date_data = json.loads(menu_settings.value)

            return MenuDateInfo(
                start_date=date_data.get("start_date", ""),
                end_date=date_data.get("end_date", ""),
                current_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
        else:
            # Return default values
            now = datetime.now()
            start_date = now.replace(hour=10, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=22, minute=0, second=0, microsecond=0)

            return MenuDateInfo(
                start_date=start_date.strftime("%Y-%m-%d %H:%M"),
                end_date=end_date.strftime("%Y-%m-%d %H:%M"),
                current_date=now.strftime("%Y-%m-%d %H:%M"),
            )

    @staticmethod
    async def set_menu_date(session: AsyncSession, date_range: dict) -> bool:
        """Set the menu date range."""
        import json

        # Always keep a single, fresh record
        await session.execute(delete(MenuSettings).where(MenuSettings.key == "menu_date_range"))
        menu_settings = MenuSettings(
            key="menu_date_range",
            value=json.dumps(date_range),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(menu_settings)

        return True

    @staticmethod
    async def add_item_to_menu(session: AsyncSession, item_id: int) -> bool:
        """Add an item to today's menu."""
        # Ensure item exists
        result = await session.execute(select(Item).where(Item.id == item_id))
        if not result.scalar_one_or_none():
            return False

        # Get or create current menu
        daily_menu = await MenuService.get_or_create_current_menu(session=session)

        # Ensure item isn't already in the menu
        result = await session.execute(
            select(DailyMenuItem).where(
                DailyMenuItem.daily_menu_id == daily_menu.id,
                DailyMenuItem.item_id == item_id,
            )
        )
        if result.scalar_one_or_none():
            return False  # Item already in the menu

        # Add item to menu
        menu_item = DailyMenuItem(daily_menu_id=daily_menu.id, item_id=item_id)
        session.add(menu_item)

        return True

    @staticmethod
    async def remove_item_from_menu(session: AsyncSession, item_id: int) -> bool:
        """Remove an item from today's menu."""
        daily_menu = await MenuService.get_current_menu(session=session)
        if not daily_menu:
            return False

        result = await session.execute(
            delete(DailyMenuItem).where(
                DailyMenuItem.daily_menu_id == daily_menu.id,
                DailyMenuItem.item_id == item_id,
            )
        )

        return result.rowcount > 0

    @staticmethod
    async def clear_today_menu(session: AsyncSession) -> bool:
        """Clear today's menu."""
        daily_menu = await MenuService.get_current_menu(session=session)
        if not daily_menu:
            return False

        await session.execute(delete(DailyMenuItem).where(DailyMenuItem.daily_menu_id == daily_menu.id))

        return True

    @staticmethod
    async def get_current_menu_items(
        session: AsyncSession,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get current menu items with full details."""
        daily_menu = await MenuService.get_current_menu(session=session)
        if not daily_menu:
            return []

        stmt = (
            select(
                DailyMenuItem.id,
                DailyMenuItem.item_id,
                DailyMenuItem.daily_menu_id,
                Item.name,
                Item.price,
                Item.description,
                Item.category_id,
                Category.title.label("category_title"),
                Item.unit_id,
                Unit.name.label("unit_name"),
                Item.image_id,
                Image.filename.label("image_filename"),
                Image.created_at.label("image_created_at"),
            )
            .join(Item, DailyMenuItem.item_id == Item.id)
            .join(Category, Item.category_id == Category.id, isouter=True)
            .join(Unit, Item.unit_id == Unit.id, isouter=True)
            .join(Image, Item.image_id == Image.id, isouter=True)
            .where(DailyMenuItem.daily_menu_id == daily_menu.id)
            .order_by(func.coalesce(Category.sort_order, 9999), Category.title, Item.name)
        )
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    @staticmethod
    async def get_public_daily_menu(session: AsyncSession) -> dict[str, Any] | None:
        """Get current public menu for display."""
        daily_menu = await MenuService.get_current_menu(session=session)
        if not daily_menu:
            return None

        # Fetch menu items with full details
        menu_items = await MenuService.get_current_menu_items(session=session)

        # Debug info intentionally minimized

        return {
            "id": daily_menu.id,
            "created_at": daily_menu.created_at,
            "items": [
                {
                    "id": item["id"],
                    "item_id": item["item_id"],
                    "daily_menu_id": item["daily_menu_id"],
                    "item": {
                        "id": item["item_id"],
                        "name": item["name"],
                        "price": decimal_to_float(value=item["price"]),
                        "description": item["description"],
                        "category_id": item["category_id"],
                        "category_title": item["category_title"],
                        "unit_id": item["unit_id"],
                        "image_id": item["image_id"],
                        "image_filename": item["image_filename"],
                        "image_url": (
                            ImageService.get_image_url(
                                image_id=item["image_id"],
                                created_at=ImageService.timestamp_from_datetime(dt=item["image_created_at"]),
                            )
                            if item["image_id"]
                            else None
                        ),
                        "unit_name": item["unit_name"],
                    },
                }
                for item in menu_items
            ],
        }

    @staticmethod
    async def get_or_create_public_daily_menu(session: AsyncSession) -> dict[str, Any]:
        """Get public menu data; if absent, create today's menu and return empty items list."""
        data = await MenuService.get_public_daily_menu(session=session)
        if data is not None:
            return data

        daily_menu = await MenuService.get_or_create_current_menu(session=session)
        return {
            "id": daily_menu.id,
            "created_at": daily_menu.created_at,
            "items": [],
        }
