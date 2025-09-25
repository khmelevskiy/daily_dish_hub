from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.unit import Unit
from app.schemas.units import UnitCreate, UnitUpdate
from app.services.ordered_entity_service import OrderedEntityService


class UnitService(OrderedEntityService[Unit]):
    model = Unit
    sort_order_step = 10
    unique_field = "name"
    unique_error_message = "Unit with this name already exists"
    related_item_fk = Item.unit_id

    @classmethod
    async def create_unit(cls, session: AsyncSession, unit_data: UnitCreate) -> Unit:
        return await cls.create_ordered(session=session, payload=unit_data)

    @classmethod
    async def get_unit(cls, session: AsyncSession, unit_id: int) -> Unit | None:
        return await cls.get_by_id(session=session, pk=unit_id)

    @classmethod
    async def update_unit(cls, session: AsyncSession, unit_id: int, unit_data: UnitUpdate) -> Unit | None:
        return await cls.update_ordered(session=session, entity_id=unit_id, payload=unit_data)

    @classmethod
    async def delete_unit(cls, session: AsyncSession, unit_id: int, keep_items: bool = True) -> bool:
        return await cls.delete_ordered(session=session, entity_id=unit_id, keep_related=keep_items)

    @classmethod
    async def get_all_units(cls, session: AsyncSession) -> list[Unit]:
        return await cls.get_all(session=session, order_by=Unit.sort_order)

    @classmethod
    async def get_unit_by_name(cls, session: AsyncSession, name: str) -> Unit | None:
        return await cls.get_by_unique(session=session, value=name)

    @classmethod
    async def move_unit_up(cls, session: AsyncSession, unit_id: int) -> bool:
        return await cls.move_up(session=session, entity_id=unit_id)

    @classmethod
    async def move_unit_down(cls, session: AsyncSession, unit_id: int) -> bool:
        return await cls.move_down(session=session, entity_id=unit_id)
