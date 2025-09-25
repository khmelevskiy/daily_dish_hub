from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.unit import Unit
from app.schemas.categories import CategoryCreate
from app.schemas.units import UnitCreate
from app.services import CategoryService, UnitService


async def ensure_initial_data(session: AsyncSession) -> None:
    """Ensure default categories and units exist.

    Behavior is intentionally identical to the previous inline logic in app/web.py:
    - Checks if any `Category` rows exist; if none, inserts the predefined list in the same order.
    - Checks if any `Unit` rows exist; if none, inserts the predefined list in the same order.
    """
    # Categories
    result = await session.execute(select(Category))
    categories = result.scalars().all()
    if not categories:
        categories = [
            CategoryCreate(title="Breakfast", sort_order=1),
            CategoryCreate(title="Salads", sort_order=2),
            CategoryCreate(title="Soups", sort_order=3),
            CategoryCreate(title="Sides", sort_order=4),
            CategoryCreate(title="Main Courses", sort_order=5),
            CategoryCreate(title="Bakery", sort_order=6),
            CategoryCreate(title="Sauces", sort_order=7),
            CategoryCreate(title="Non-Alcoholic Drinks", sort_order=8),
            CategoryCreate(title="Alcoholic Drinks", sort_order=9),
            CategoryCreate(title="Other", sort_order=10),
        ]

        for category in categories:
            await CategoryService.create_category(session=session, category_data=category)

    # Units
    result = await session.execute(select(Unit))
    units = result.scalars().all()
    if not units:
        units = [
            UnitCreate(name="serving", sort_order=1),
            UnitCreate(name="pcs", sort_order=2),
            UnitCreate(name="glass", sort_order=3),
            UnitCreate(name="1 L", sort_order=4),
            UnitCreate(name="kg", sort_order=5),
            UnitCreate(name="g", sort_order=6),
            UnitCreate(name="L", sort_order=7),
            UnitCreate(name="ml", sort_order=8),
            UnitCreate(name="pack", sort_order=9),
            UnitCreate(name="can", sort_order=10),
        ]
        for unit in units:
            await UnitService.create_unit(session=session, unit_data=unit)
