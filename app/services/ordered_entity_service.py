"""Shared helpers for ordered CRUD services (categories, units, etc.)."""

from __future__ import annotations

from typing import Any, ClassVar, Generic, Iterable, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.services.base_service import BaseCRUDService


T = TypeVar("T")


class OrderedEntityService(BaseCRUDService[T], Generic[T]):
    """Base service with helpers for entities that support ordered CRUD operations."""

    sort_order_step: ClassVar[int] = 10
    """Default distance between consecutive sort orders."""

    unique_field: ClassVar[str]
    """Name of the unique field on the model (e.g. 'name', 'title')."""

    unique_error_message: ClassVar[str]
    """Message raised when a duplicate unique value is detected."""

    related_item_fk: ClassVar[InstrumentedAttribute | None] = None
    """Foreign key attribute on a related model that should be nulled/removed on delete."""

    # ----- Internal helpers -------------------------------------------------

    @classmethod
    def _unique_column(cls) -> InstrumentedAttribute:
        return getattr(cls.model, cls.unique_field)

    @classmethod
    def _sort_column(cls) -> InstrumentedAttribute:
        return getattr(cls.model, "sort_order")

    @classmethod
    def _related_model(cls):
        if cls.related_item_fk is None:
            return None

        return cls.related_item_fk.parent.class_

    @classmethod
    def _needs_normalization(cls, entities: Iterable[Any]) -> bool:
        last_value = None
        for entity in entities:
            current = getattr(entity, "sort_order", 0) or 0
            if last_value is not None and current <= last_value:
                return True
            last_value = current

        return False

    # ----- Shared behaviour -------------------------------------------------

    @classmethod
    async def load_for_reordering(cls, session: AsyncSession) -> list[T]:
        """Return entities ordered by sort order, normalizing duplicates if required."""
        stmt = select(cls.model).order_by(
            cls._sort_column(),
            cls.model.id,  # pyright: ignore[reportAttributeAccessIssue]
        )
        result = await session.execute(stmt)
        entities = list(result.scalars().all())

        if cls._needs_normalization(entities):
            for index, entity in enumerate(entities):
                setattr(entity, "sort_order", (index + 1) * cls.sort_order_step)
            await session.flush()

        return entities

    @classmethod
    async def get_by_unique(cls, session: AsyncSession, value: str) -> T | None:
        stmt = select(cls.model).where(cls._unique_column() == value)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @classmethod
    async def _ensure_unique(cls, session: AsyncSession, value: str, *, exclude_id: int | None = None) -> None:
        existing = await cls.get_by_unique(session=session, value=value)
        if existing and (
            exclude_id is None or existing.id != exclude_id  # pyright: ignore[reportAttributeAccessIssue]
        ):
            raise ValueError(cls.unique_error_message)

    @staticmethod
    def _explicit_sort_order(payload: Any) -> tuple[bool, int | None]:
        sort_order = getattr(payload, "sort_order", None)
        fields_set = getattr(payload, "model_fields_set", set())
        has_explicit_value = "sort_order" in fields_set and sort_order is not None

        return has_explicit_value, sort_order

    @classmethod
    async def create_ordered(cls, session: AsyncSession, payload: Any) -> T:
        """Create a new entity keeping stable order semantics."""

        unique_value = getattr(payload, cls.unique_field)
        await cls._ensure_unique(session=session, value=unique_value)

        entities = await cls.load_for_reordering(session=session)

        if entities:
            raw_tail = getattr(entities[-1], "sort_order", 0)
            last_sort_order = raw_tail if raw_tail is not None else 0
        else:
            last_sort_order = 0
        explicit, requested_sort_order = cls._explicit_sort_order(payload)

        sort_order = (
            requested_sort_order
            if explicit and requested_sort_order is not None and requested_sort_order > last_sort_order
            else last_sort_order + cls.sort_order_step
        )

        return await cls.create(
            session=session,
            **{
                cls.unique_field: unique_value,
                "sort_order": sort_order,
            },
        )

    @classmethod
    async def update_ordered(cls, session: AsyncSession, entity_id: int, payload: Any) -> T | None:
        entity = await cls.get_by_id(session=session, pk=entity_id)
        if not entity:
            return None

        new_unique_value = getattr(payload, cls.unique_field)
        if new_unique_value is not None:
            await cls._ensure_unique(
                session=session,
                value=new_unique_value,
                exclude_id=entity.id,  # pyright: ignore[reportAttributeAccessIssue]
            )

        cls.apply_updates(
            obj=entity,
            updates={
                cls.unique_field: new_unique_value,
                "sort_order": getattr(payload, "sort_order", None),
            },
        )

        return entity

    @classmethod
    async def delete_ordered(
        cls,
        session: AsyncSession,
        entity_id: int,
        *,
        keep_related: bool = True,
    ) -> bool:
        entity = await cls.get_by_id(session=session, pk=entity_id)
        if not entity:
            return False

        related_model = cls._related_model()
        if related_model is not None and cls.related_item_fk is not None:
            stmt = select(related_model).where(cls.related_item_fk == entity_id)
            result = await session.execute(stmt)
            related_records = result.scalars().all()

            if keep_related:
                target_attr = cls.related_item_fk.key
                for record in related_records:
                    setattr(record, target_attr, None)
            else:
                await session.execute(delete(related_model).where(cls.related_item_fk == entity_id))

        await session.execute(
            delete(cls.model).where(cls.model.id == entity_id)  # pyright: ignore[reportAttributeAccessIssue]
        )

        return True

    @classmethod
    async def move(cls, session: AsyncSession, entity_id: int, direction: int) -> bool:
        entities = await cls.load_for_reordering(session=session)

        current_index = next(
            (
                index
                for index, entity in enumerate(entities)
                if entity.id == entity_id  # pyright: ignore[reportAttributeAccessIssue]
            ),
            None,
        )
        if current_index is None:
            return False

        target_index = current_index + direction
        if not (0 <= target_index < len(entities)):
            return False

        current = entities[current_index]
        target = entities[target_index]
        current.sort_order, target.sort_order = (  # pyright: ignore[reportAttributeAccessIssue]
            target.sort_order,  # pyright: ignore[reportAttributeAccessIssue]
            current.sort_order,  # pyright: ignore[reportAttributeAccessIssue]
        )

        return True

    @classmethod
    async def move_up(cls, session: AsyncSession, entity_id: int) -> bool:
        return await cls.move(session=session, entity_id=entity_id, direction=-1)

    @classmethod
    async def move_down(cls, session: AsyncSession, entity_id: int) -> bool:
        return await cls.move(session=session, entity_id=entity_id, direction=1)
