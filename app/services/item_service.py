from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.image import Image
from app.models.item import Item
from app.models.unit import Unit
from app.schemas.items import ItemCreate, ItemUpdate
from app.services.base_service import BaseCRUDService
from app.services.formatting import normalize_price_in_list, to_decimal


class ItemService(BaseCRUDService[Item]):
    model = Item

    @staticmethod
    async def _validate_related_entities(
        session: AsyncSession,
        *,
        category_id: int | None,
        unit_id: int | None,
        image_id: int | None,
    ) -> None:
        if category_id is not None:
            category = await session.get(Category, category_id)
            if category is None:
                raise ValueError("Category not found")
        if unit_id is not None:
            unit = await session.get(Unit, unit_id)
            if unit is None:
                raise ValueError("Unit not found")
        if image_id is not None:
            image = await session.get(Image, image_id)
            if image is None:
                raise ValueError("Image not found")

    @classmethod
    async def create_item(cls, session: AsyncSession, item_data: ItemCreate) -> Item:
        await cls._validate_related_entities(
            session=session,
            category_id=item_data.category_id,
            unit_id=item_data.unit_id,
            image_id=item_data.image_id,
        )

        return await cls.create(
            session=session,
            category_id=item_data.category_id,
            unit_id=item_data.unit_id,
            name=item_data.name,
            price=item_data.price,
            description=item_data.description,
            image_id=item_data.image_id,
        )

    @classmethod
    async def get_item(cls, session: AsyncSession, item_id: int) -> Item | None:
        return await cls.get_by_id(session=session, pk=item_id)

    @staticmethod
    async def get_item_with_details(session: AsyncSession, item_id: int) -> dict | None:
        """Get an item with full info: category, unit and image."""
        stmt = (
            select(
                Item.id,
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
            .join(Category, Item.category_id == Category.id, isouter=True)
            .join(Unit, Item.unit_id == Unit.id, isouter=True)
            .join(Image, Item.image_id == Image.id, isouter=True)
            .where(Item.id == item_id)
        )
        result = await session.execute(stmt)
        row = result.fetchone()
        if not row:
            return None

        item_data = dict(row._mapping)

        # Ensure numeric price keeps currency precision
        item_data["price"] = to_decimal(value=item_data.get("price"))

        # Add image_url
        image_id = item_data.get("image_id")
        image_created_at = item_data.get("image_created_at")

        if image_id and image_created_at:
            try:
                from app.services.image_service import ImageService

                item_data["image_url"] = ImageService.get_image_url(
                    image_id=image_id,
                    created_at=ImageService.timestamp_from_datetime(dt=image_created_at),
                )
            except Exception:
                item_data["image_url"] = f"/images/{image_id}"
        else:
            item_data["image_url"] = None

        return item_data

    @classmethod
    async def update_item(cls, session: AsyncSession, item_id: int, item_data: ItemUpdate) -> Item | None:
        item = await cls.get_by_id(session=session, pk=item_id)
        if not item:
            return None

        candidate_category_id = (
            item.category_id if "category_id" not in item_data.model_fields_set else item_data.category_id
        )
        candidate_unit_id = item.unit_id if "unit_id" not in item_data.model_fields_set else item_data.unit_id
        candidate_image_id = item.image_id if "image_id" not in item_data.model_fields_set else item_data.image_id

        await cls._validate_related_entities(
            session=session,
            category_id=candidate_category_id,
            unit_id=candidate_unit_id,
            image_id=candidate_image_id,
        )

        # image_id must be updated in any case, including None
        cls.apply_updates(
            obj=item,
            updates={
                "category_id": item_data.category_id,
                "unit_id": item_data.unit_id,
                "name": item_data.name,
                "price": item_data.price,
                "description": item_data.description,
                "image_id": item_data.image_id,
            },
            allow_none_fields={"image_id"},
        )

        await session.flush()

        return item

    @staticmethod
    async def delete_item(session: AsyncSession, item_id: int) -> bool:
        item = await ItemService.get_item(session=session, item_id=item_id)
        if not item:
            return False

        # Remove item from daily menu if present
        from app.models.daily_menu_item import DailyMenuItem

        await session.execute(delete(DailyMenuItem).where(DailyMenuItem.item_id == item_id))
        await session.execute(delete(Item).where(Item.id == item_id))

        return True

    @classmethod
    async def get_all_items(cls, session: AsyncSession) -> list[Item]:
        return await cls.get_all(session=session, order_by=Item.id)

    @staticmethod
    async def get_all_items_with_details(session: AsyncSession) -> list[dict]:
        """Get all items with full info."""
        stmt = (
            select(
                Item.id,
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
            .join(Category, Item.category_id == Category.id, isouter=True)
            .join(Unit, Item.unit_id == Unit.id, isouter=True)
            .join(Image, Item.image_id == Image.id, isouter=True)
            .order_by(func.coalesce(Category.sort_order, 9999), Category.title, Item.name)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()
        items = [dict(row._mapping) for row in rows]

        # Add image_url for each item
        from app.services.image_service import ImageService

        normalize_price_in_list(items=items)
        for item in items:
            image_id = item.get("image_id")
            image_created_at = item.get("image_created_at")

            if image_id and image_created_at:
                try:
                    item["image_url"] = ImageService.get_image_url(
                        image_id=image_id,
                        created_at=ImageService.timestamp_from_datetime(dt=image_created_at),
                    )
                except Exception:
                    item["image_url"] = f"/images/{image_id}"
            else:
                item["image_url"] = None

        return items

    @staticmethod
    async def get_orphaned_items(session: AsyncSession) -> list[Item]:
        result = await session.execute(select(Item).where(Item.category_id.is_(None)))

        return list(result.scalars().all())

    @staticmethod
    async def get_items_without_unit(session: AsyncSession) -> list[Item]:
        result = await session.execute(select(Item).where(Item.unit_id.is_(None)))

        return list(result.scalars().all())

    @staticmethod
    async def move_items_to_category(session: AsyncSession, category_id: int, item_ids: list[int]) -> int:
        """Move items to a given category."""
        if not item_ids:
            return 0

        result = await session.execute(
            update(Item)
            .where(Item.id.in_(item_ids))
            .values(category_id=category_id)
            .execution_options(synchronize_session=False)
        )

        return int(result.rowcount or 0)

    @staticmethod
    async def move_items_to_unit(session: AsyncSession, unit_id: int, item_ids: list[int]) -> int:
        """Move items to a given unit."""
        if not item_ids:
            return 0

        result = await session.execute(
            update(Item)
            .where(Item.id.in_(item_ids))
            .values(unit_id=unit_id)
            .execution_options(synchronize_session=False)
        )

        return int(result.rowcount or 0)
