import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db import session_scope
from app.models.daily_menu_item import DailyMenuItem
from app.schemas.common import SuccessResponse
from app.schemas.daily_menu import AddToMenuRequest, DailyMenuCreate, DailyMenuResponse, MenuDateRange, MenuDateResponse
from app.services import MenuService


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=DailyMenuResponse,
    summary="Get Daily Menu",
    description="Get or create today's daily menu with items.",
)
async def get_daily_menu() -> DailyMenuResponse:
    async with session_scope() as session:
        menu_data = await MenuService.get_or_create_public_daily_menu(session=session)

        return DailyMenuResponse(**menu_data)


@router.post(
    "/replace",
    response_model=SuccessResponse,
    summary="Replace Menu Items",
    description="Replace all items in today's daily menu with the provided list.",
)
async def replace_menu_items(item_ids: DailyMenuCreate) -> SuccessResponse:
    async with session_scope() as session:
        success = await MenuService.recreate_current_menu(session=session, item_ids=item_ids.item_ids)
        if not success:
            logger.error("Failed to replace menu with item IDs: %s", item_ids.item_ids)
            raise HTTPException(status_code=400, detail="Failed to replace menu")

        return SuccessResponse(message="Menu replaced successfully")


@router.get(
    "/date",
    response_model=MenuDateResponse,
    summary="Get Menu Date",
    description="Get current menu date/time window settings.",
)
async def get_menu_date() -> MenuDateResponse:
    """Get current menu date."""
    async with session_scope() as session:
        date_info = await MenuService.get_menu_date(session=session)

        return MenuDateResponse(menu_date=date_info)


@router.post(
    "/date",
    response_model=SuccessResponse,
    summary="Set Menu Date",
    description="Set menu date/time window settings.",
)
async def set_menu_date(date_range: MenuDateRange) -> SuccessResponse:
    """Set menu date."""
    async with session_scope() as session:
        success = await MenuService.set_menu_date(session=session, date_range=date_range.model_dump())
        if not success:
            logger.error("Failed to set menu date with data: %s", date_range.model_dump())
            raise HTTPException(status_code=400, detail="Failed to set menu date")

        return SuccessResponse(message="Menu date set successfully")


@router.post(
    "/add",
    summary="Add Item To Menu",
    description="Add a single item to today's daily menu.",
)
async def add_to_menu(payload: AddToMenuRequest) -> SuccessResponse:
    async with session_scope() as session:
        item_id = payload.item_id

        success = await MenuService.add_item_to_menu(session=session, item_id=item_id)
        if not success:
            logger.error("Failed to add item to menu with ID: %s", item_id)
            raise HTTPException(status_code=404, detail="Item not found or already in menu")

        return SuccessResponse(message="Item added to menu")


@router.delete(
    "/clear",
    summary="Clear Daily Menu",
    description="Remove all items from today's daily menu.",
)
async def clear_daily_menu() -> SuccessResponse:
    async with session_scope() as session:
        await MenuService.clear_today_menu(session=session)

        return SuccessResponse(message="Menu cleared")


@router.delete(
    "/{menu_item_id}",
    summary="Remove From Menu",
    description="Remove a specific item from today's daily menu by menu item ID.",
)
async def remove_from_menu(menu_item_id: int) -> SuccessResponse:
    async with session_scope() as session:
        # Get item_id from menu_item_id
        result = await session.execute(select(DailyMenuItem).where(DailyMenuItem.id == menu_item_id))
        menu_item = result.scalar_one_or_none()

        if not menu_item:
            logger.error("Menu item not found with ID: %s", menu_item_id)
            raise HTTPException(status_code=404, detail="Menu item not found")

        success = await MenuService.remove_item_from_menu(session=session, item_id=menu_item.item_id)
        if not success:
            logger.error("Failed to remove menu item with ID: %s", menu_item_id)
            raise HTTPException(status_code=404, detail="Menu item not found")

        return SuccessResponse(message="Item removed from menu")
