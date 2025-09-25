from typing import Any, ClassVar, Generic, Mapping, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


class BaseCRUDService(Generic[T]):
    """Lightweight base class with common CRUD helpers.

    Notes on behavior (kept 1:1 with existing services):
    - create(): adds the instance and flushes (no commit)
    - get_by_id(): returns the model instance or None
    - get_all(): returns a list of model instances
    - apply_updates(): sets provided fields, skipping None unless explicitly allowed
    - add_flush_refresh(): flushes and refreshes an instance without commit

    Services should still control when to commit vs flush to preserve existing semantics.
    """

    model: ClassVar[Type[T]]  # pyright: ignore[reportGeneralTypeIssues]

    @classmethod
    async def get_by_id(cls, session: AsyncSession, pk: Any) -> T | None:
        result = await session.execute(
            select(cls.model).where(cls.model.id == pk)  # pyright: ignore[reportAttributeAccessIssue]
        )

        return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession, order_by: Any | None = None) -> list[T]:
        stmt = select(cls.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)

        return list(result.scalars().all())

    @classmethod
    async def create(cls, session: AsyncSession, **fields: Any) -> T:
        obj: T = cls.model(**fields)  # type: ignore[arg-type]
        session.add(obj)
        await session.flush()

        return obj

    @staticmethod
    def apply_updates(
        obj: Any,
        updates: Mapping[str, Any],
        allow_none_fields: set[str] | None = None,
    ) -> None:
        """Apply field updates to an object.

        - Skips keys where value is None by default.
        - If a key is in allow_none_fields, sets attribute even if value is None.
        """
        allow_none_fields = allow_none_fields or set()
        for key, value in updates.items():
            if value is None and key not in allow_none_fields:
                continue
            setattr(obj, key, value)

    @staticmethod
    async def add_flush_refresh(session: AsyncSession, obj: Any) -> Any:
        """Flush and refresh an instance without committing."""
        await session.flush()
        await session.refresh(obj)

        return obj
