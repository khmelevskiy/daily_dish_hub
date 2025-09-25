from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.item import Item
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.services.ordered_entity_service import OrderedEntityService


class CategoryService(OrderedEntityService[Category]):
    model = Category
    sort_order_step = 10
    unique_field = "title"
    unique_error_message = "Category with this title already exists"
    related_item_fk = Item.category_id

    @classmethod
    async def create_category(cls, session: AsyncSession, category_data: CategoryCreate) -> Category:
        return await cls.create_ordered(session=session, payload=category_data)

    @classmethod
    async def get_category(cls, session: AsyncSession, category_id: int) -> Category | None:
        return await cls.get_by_id(session=session, pk=category_id)

    @classmethod
    async def update_category(
        cls, session: AsyncSession, category_id: int, category_data: CategoryUpdate
    ) -> Category | None:
        return await cls.update_ordered(session=session, entity_id=category_id, payload=category_data)

    @classmethod
    async def delete_category(cls, session: AsyncSession, category_id: int, keep_items: bool = True) -> bool:
        return await cls.delete_ordered(session=session, entity_id=category_id, keep_related=keep_items)

    @classmethod
    async def get_all_categories(cls, session: AsyncSession) -> list[Category]:
        return await cls.get_all(session=session, order_by=Category.sort_order)

    @classmethod
    async def get_category_by_title(cls, session: AsyncSession, title: str) -> Category | None:
        return await cls.get_by_unique(session=session, value=title)

    @classmethod
    async def move_category_up(cls, session: AsyncSession, category_id: int) -> bool:
        return await cls.move_up(session=session, entity_id=category_id)

    @classmethod
    async def move_category_down(cls, session: AsyncSession, category_id: int) -> bool:
        return await cls.move_down(session=session, entity_id=category_id)
