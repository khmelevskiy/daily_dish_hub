import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.db import session_scope
from app.models.item import Item
from app.models.unit import Unit
from app.schemas.common import ItemIdsOnlyRequest, SuccessResponse
from app.schemas.units import MoveItemsToUnitRequest, UnitCreate, UnitListResponse, UnitResponse, UnitUpdate
from app.services import ItemService, UnitService


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=UnitListResponse,
    summary="List Units",
    description="Return all units ordered by sort_order.",
)
async def list_units() -> UnitListResponse:
    async with session_scope() as session:
        units = await UnitService.get_all_units(session=session)
        units_list = [
            UnitResponse(
                id=unit.id,
                name=unit.name,
                sort_order=unit.sort_order,
            )
            for unit in units
        ]

        return UnitListResponse(units=units_list, total=len(units_list))


@router.post(
    "",
    response_model=SuccessResponse,
    summary="Create Unit",
    description="Create a new unit.",
)
async def create_unit(payload: UnitCreate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            unit = await UnitService.create_unit(session=session, unit_data=payload)
        except ValueError as exc:
            logger.error(f"ValueError occurred: {exc}")
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return SuccessResponse(message="Unit created successfully", data={"id": unit.id})


@router.put(
    "/{unit_id}",
    response_model=SuccessResponse,
    summary="Update Unit",
    description="Update unit fields.",
)
async def update_unit(unit_id: int, payload: UnitUpdate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            unit = await UnitService.update_unit(session=session, unit_id=unit_id, unit_data=payload)
        except ValueError as exc:
            logger.error(f"ValueError occurred: {exc}")
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not unit:
            logger.error(f"Unit with id {unit_id} not found")
            raise HTTPException(status_code=404, detail="Unit not found")

        return SuccessResponse(message="Unit updated successfully", data={"id": unit.id})


@router.delete(
    "/{unit_id}",
    response_model=SuccessResponse,
    summary="Delete Unit",
    description="Delete a unit (optionally keep its items).",
)
async def delete_unit(unit_id: int, keep_items: bool = True) -> SuccessResponse:
    async with session_scope() as session:
        success = await UnitService.delete_unit(session=session, unit_id=unit_id, keep_items=keep_items)
        if not success:
            logger.error(f"Unit with id {unit_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Unit not found")

        message = "Unit deleted" if keep_items else "Unit and all items with it deleted"

        return SuccessResponse(message=message)


@router.post(
    "/{unit_id}/move-up",
    summary="Move Unit Up",
    description="Swap sort order to move a unit up.",
)
async def move_unit_up(unit_id: int) -> SuccessResponse:
    async with session_scope() as session:
        success = await UnitService.move_unit_up(session=session, unit_id=unit_id)
        if not success:
            raise HTTPException(status_code=404, detail="Unit not found or already at top")

        return SuccessResponse(message="Unit moved up")


@router.post(
    "/{unit_id}/move-down",
    summary="Move Unit Down",
    description="Swap sort order to move a unit down.",
)
async def move_unit_down(unit_id: int) -> SuccessResponse:
    async with session_scope() as session:
        success = await UnitService.move_unit_down(session=session, unit_id=unit_id)
        if not success:
            logger.error(f"Unit with id {unit_id} not found or already at bottom")
            raise HTTPException(status_code=404, detail="Unit not found or already at bottom")

        return SuccessResponse(message="Unit moved down")


@router.post(
    "/move-items",
    summary="Move Items To Unit",
    description="Assign selected items to the specified unit.",
)
async def move_items_to_unit(payload: MoveItemsToUnitRequest) -> SuccessResponse:
    async with session_scope() as session:
        # Ensure unit exists
        result = await session.execute(select(Unit).where(Unit.id == payload.unit_id))
        unit = result.scalar_one_or_none()

        if not unit:
            logger.error(f"Unit with id {payload.unit_id} not found for moving items")
            raise HTTPException(status_code=404, detail="Unit not found")

        updated_count = await ItemService.move_items_to_unit(
            session=session, unit_id=payload.unit_id, item_ids=payload.item_ids
        )
        await session.commit()

        return SuccessResponse(message=f"Items moved: {updated_count}")


@router.post(
    "/{unit_id}/move-no-unit",
    summary="Move Items Without Unit",
    description="Assign items with no unit to the specified unit.",
)
async def move_no_unit_items_to_unit(
    unit_id: int, payload: MoveItemsToUnitRequest | ItemIdsOnlyRequest
) -> SuccessResponse:
    async with session_scope() as session:
        # Ensure unit exists
        result = await session.execute(select(Unit).where(Unit.id == unit_id))
        unit = result.scalar_one_or_none()

        if not unit:
            logger.error(f"Unit with id {unit_id} not found for moving no-unit items")
            raise HTTPException(status_code=404, detail="Unit not found")

        # Backward compatible: accept both full request (with unit_id) and item_ids-only
        if isinstance(payload, ItemIdsOnlyRequest):
            item_ids = payload.item_ids
        else:
            if payload.unit_id != unit_id:
                logger.error("unit_id in path and body do not match")
                raise HTTPException(status_code=400, detail="unit_id mismatch between path and body")
            item_ids = payload.item_ids
        if not item_ids:
            logger.error("Item list cannot be empty")
            raise HTTPException(status_code=400, detail="Item list cannot be empty")

        # Move items without units
        update_stmt = (
            update(Item)
            .where(Item.id.in_(item_ids), Item.unit_id.is_(None))
            .values(unit_id=unit_id)
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(update_stmt)
        updated_count = int(result.rowcount or 0)

        await session.commit()

        return SuccessResponse(message=f"Items moved: {updated_count}")
