"""Public-facing API endpoints (menu preview, settings, etc.)."""

from fastapi import APIRouter

from app.core.config import settings
from app.db import session_scope
from app.schemas.daily_menu import DailyMenuResponse, MenuDateResponse
from app.schemas.public import PublicSettingsResponse
from app.services import MenuService


router = APIRouter(tags=["public"])


@router.get("/daily-menu", response_model=DailyMenuResponse)
async def get_public_daily_menu() -> DailyMenuResponse:
    async with session_scope() as session:
        menu_data = await MenuService.get_or_create_public_daily_menu(session=session)
        return DailyMenuResponse(**menu_data)


@router.get("/menu-date", response_model=MenuDateResponse)
async def get_public_menu_date() -> MenuDateResponse:
    async with session_scope() as session:
        date_info = await MenuService.get_menu_date(session=session)
        return MenuDateResponse(menu_date=date_info)


@router.get("/settings", response_model=PublicSettingsResponse)
async def get_public_settings() -> PublicSettingsResponse:
    return PublicSettingsResponse(
        site_name=settings.site_name,
        site_description=settings.site_description,
        currency_code=settings.currency_code,
        currency_symbol=settings.currency_symbol,
        currency_locale=settings.currency_locale,
    )
