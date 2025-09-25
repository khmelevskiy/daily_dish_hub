import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.db import session_scope
from app.schemas.common import SuccessResponse
from app.schemas.items import ItemCreate, ItemListResponse, ItemResponse, ItemUpdate
from app.services.formatting import to_decimal
from app.services.item_service import ItemService


router = APIRouter()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=ItemListResponse,
    summary="List Items",
    description="Return all items with category/unit/image details.",
)
async def list_items() -> ItemListResponse:
    async with session_scope() as session:
        items_data = await ItemService.get_all_items_with_details(session=session)
        items_list = [ItemResponse(**item) for item in items_data]

        return ItemListResponse(items=items_list, total=len(items_list))


@router.get(
    "/orphaned",
    response_model=ItemListResponse,
    summary="Items Without Category",
    description="List items that do not have a category assigned.",
)
async def get_orphaned_items() -> ItemListResponse:
    async with session_scope() as session:
        items = await ItemService.get_orphaned_items(session=session)

        items_list = [
            ItemResponse(
                id=item.id,
                name=item.name,
                price=to_decimal(item.price),
                description=item.description,
                category_id=item.category_id,
                category_title=None,
                unit_id=item.unit_id,
                image_id=item.image_id,
                image_filename=None,
                image_url=None,
                unit_name=None,
            )
            for item in items
        ]

        return ItemListResponse(items=items_list, total=len(items_list))


@router.get(
    "/no-unit",
    response_model=ItemListResponse,
    summary="Items Without Unit",
    description="List items that do not have a unit assigned.",
)
async def get_items_without_unit() -> ItemListResponse:
    async with session_scope() as session:
        items = await ItemService.get_items_without_unit(session=session)
        items_list = [
            ItemResponse(
                id=item.id,
                name=item.name,
                price=to_decimal(item.price),
                description=item.description,
                category_id=item.category_id,
                category_title=None,
                unit_id=item.unit_id,
                image_id=item.image_id,
                image_filename=None,
                image_url=None,
                unit_name=None,
            )
            for item in items
        ]

        return ItemListResponse(items=items_list, total=len(items_list))


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get Item",
    description="Get an item by ID with full details.",
)
async def get_item(item_id: int) -> ItemResponse:
    async with session_scope() as session:
        item_data = await ItemService.get_item_with_details(session=session, item_id=item_id)
        if not item_data:
            logger.error(f"Item with ID {item_id} not found")
            raise HTTPException(status_code=404, detail="Item not found")

        return ItemResponse(**item_data)


@router.post(
    "",
    response_model=SuccessResponse,
    summary="Create Item",
    description="Create a new item.",
)
async def create_item(payload: ItemCreate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            item = await ItemService.create_item(session=session, item_data=payload)
        except ValueError as exc:
            logger.error(f"ValueError occurred: {exc}")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except IntegrityError as exc:
            logger.error(f"IntegrityError occurred: {exc}")
            raise HTTPException(status_code=400, detail="Unable to create item") from exc

        return SuccessResponse(message="Item created successfully", data={"id": item.id})


@router.put(
    "/{item_id}",
    response_model=SuccessResponse,
    summary="Update Item",
    description="Update an existing item.",
)
async def update_item(item_id: int, payload: ItemUpdate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            item = await ItemService.update_item(session=session, item_id=item_id, item_data=payload)
        except ValueError as exc:
            logger.error(f"ValueError occurred: {exc}")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except IntegrityError as exc:
            logger.error(f"IntegrityError occurred: {exc}")
            raise HTTPException(status_code=400, detail="Unable to update item") from exc
        if not item:
            logger.error(f"Item with ID {item_id} not found for update")
            raise HTTPException(status_code=404, detail="Item not found")

        return SuccessResponse(message="Item updated successfully", data={"id": item.id})


@router.delete(
    "/{item_id}",
    response_model=SuccessResponse,
    summary="Delete Item",
    description="Delete an item by ID.",
)
async def delete_item(item_id: int) -> SuccessResponse:
    async with session_scope() as session:
        success = await ItemService.delete_item(session=session, item_id=item_id)
        if not success:
            logger.error(f"Item with ID {item_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Item not found")

        return SuccessResponse(message="Item deleted")
