#!/usr/bin/env python3
"""Tests for MenuService query helpers."""

from __future__ import annotations

import sys
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.category import Category
from app.models.daily_menu import DailyMenu
from app.models.daily_menu_item import DailyMenuItem
from app.models.item import Item
from app.models.unit import Unit
from app.services.menu_service import MenuService


@pytest_asyncio.fixture
async def session() -> AsyncSession:  # pyright: ignore[reportInvalidTypeForm]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as db:
        yield db  # pyright: ignore[reportReturnType]

    await engine.dispose()


async def _seed_menu(session: AsyncSession, count: int = 3) -> None:
    unit = Unit(name="pcs", sort_order=1)
    categories = [
        Category(title="Cat A", sort_order=10),
        Category(title="Cat B", sort_order=20),
    ]
    menu = DailyMenu()
    session.add_all([unit, *categories, menu])
    await session.flush()

    for index in range(count):
        category = categories[index % len(categories)]
        item = Item(
            name=f"Item {index}",
            price=Decimal("1.00") + Decimal(index),
            category_id=category.id,
            unit_id=unit.id,
        )
        session.add(item)
        await session.flush()
        session.add(DailyMenuItem(daily_menu_id=menu.id, item_id=item.id))
    await session.flush()


@pytest.mark.asyncio
async def test_get_current_menu_items_supports_limit(session: AsyncSession) -> None:
    await _seed_menu(session, count=5)

    results = await MenuService.get_current_menu_items(session=session, limit=2)

    assert len(results) == 2
    assert all("item_id" in row for row in results)


@pytest.mark.asyncio
async def test_get_current_menu_items_supports_offset(session: AsyncSession) -> None:
    await _seed_menu(session, count=4)

    first = await MenuService.get_current_menu_items(session=session, limit=1)
    second = await MenuService.get_current_menu_items(session=session, limit=1, offset=1)

    assert first and second
    assert first[0]["item_id"] != second[0]["item_id"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
