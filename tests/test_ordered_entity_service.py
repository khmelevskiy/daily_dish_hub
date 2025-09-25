#!/usr/bin/env python3
"""Tests for OrderedEntityService behaviours."""

from __future__ import annotations

import sys
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.category import Category
from app.models.item import Item
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService


@pytest_asyncio.fixture
async def session() -> AsyncSession:  # pyright: ignore[reportInvalidTypeForm]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as db:
        yield db  # pyright: ignore[reportReturnType]

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_ordered_respects_explicit_sort_order(session: AsyncSession) -> None:
    session.add_all(
        [
            Category(title="A", sort_order=10),
            Category(title="B", sort_order=20),
        ]
    )
    await session.flush()

    payload = CategoryCreate(title="C", sort_order=35)
    entity = await CategoryService.create_category(session=session, category_data=payload)

    assert entity.sort_order == 35


@pytest.mark.asyncio
async def test_create_ordered_falls_back_when_explicit_is_low(session: AsyncSession) -> None:
    session.add(Category(title="Base", sort_order=40))
    await session.flush()

    payload = CategoryCreate(title="Next", sort_order=5)
    entity = await CategoryService.create_category(session=session, category_data=payload)

    assert entity.sort_order == 50  # previous 40 + step 10


@pytest.mark.asyncio
async def test_update_ordered_allows_explicit_sort_order(session: AsyncSession) -> None:
    entity = Category(title="ToUpdate", sort_order=10)
    session.add(entity)
    await session.flush()

    payload = CategoryUpdate(title="Test title", sort_order=80)
    updated = await CategoryService.update_category(session=session, category_id=entity.id, category_data=payload)
    await session.flush()

    assert updated is not None
    assert updated.sort_order == 80


@pytest.mark.asyncio
async def test_delete_ordered_nulls_related_items(session: AsyncSession) -> None:
    category = Category(title="WithItems", sort_order=10)
    item = Item(name="Soup", price=Decimal("1.00"), category=category)
    session.add_all([category, item])
    await session.flush()

    result = await CategoryService.delete_category(session=session, category_id=category.id, keep_items=True)
    await session.flush()

    assert result is True
    refreshed = await session.get(Item, item.id)
    assert refreshed is not None
    assert refreshed.category_id is None


@pytest.mark.asyncio
async def test_delete_ordered_removes_related_items(session: AsyncSession) -> None:
    category = Category(title="RemoveItems", sort_order=10)
    item = Item(name="Cake", price=Decimal("2.50"), category=category)
    session.add_all([category, item])
    await session.flush()

    result = await CategoryService.delete_category(session=session, category_id=category.id, keep_items=False)
    await session.flush()

    assert result is True
    assert await session.get(Item, item.id) is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
