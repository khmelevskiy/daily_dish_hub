from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.db import session_scope
from app.models.category import Category
from app.models.item import Item
from app.schemas.categories import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
    MoveItemsToCategoryRequest,
)
from app.schemas.common import ItemIdsOnlyRequest, SuccessResponse
from app.services import CategoryService, ItemService


router = APIRouter()


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="List Categories",
    description="Return all categories ordered by sort_order.",
)
async def list_categories() -> CategoryListResponse:
    async with session_scope() as session:
        categories = await CategoryService.get_all_categories(session=session)
        categories_list = [
            CategoryResponse(
                id=category.id,
                title=category.title,
                sort_order=category.sort_order,
            )
            for category in categories
        ]

        return CategoryListResponse(categories=categories_list, total=len(categories_list))


@router.post(
    "",
    response_model=SuccessResponse,
    summary="Create Category",
    description="Create a new category.",
)
async def create_category(payload: CategoryCreate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            category = await CategoryService.create_category(session=session, category_data=payload)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return SuccessResponse(message="Category created successfully", data={"id": category.id})


@router.put(
    "/{category_id}",
    response_model=SuccessResponse,
    summary="Update Category",
    description="Update category fields.",
)
async def update_category(category_id: int, payload: CategoryUpdate) -> SuccessResponse:
    async with session_scope() as session:
        try:
            category = await CategoryService.update_category(
                session=session, category_id=category_id, category_data=payload
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return SuccessResponse(message="Category updated successfully", data={"id": category.id})


@router.delete(
    "/{category_id}",
    response_model=SuccessResponse,
    summary="Delete Category",
    description="Delete a category (optionally keep its items).",
)
async def delete_category(category_id: int, keep_items: bool = True) -> SuccessResponse:
    async with session_scope() as session:
        success = await CategoryService.delete_category(session=session, category_id=category_id, keep_items=keep_items)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")

        message = "Category deleted" if keep_items else "Category and all items in it deleted"

        return SuccessResponse(message=message)


@router.post(
    "/{category_id}/move-up",
    summary="Move Category Up",
    description="Swap sort order to move a category up.",
)
async def move_category_up(category_id: int) -> SuccessResponse:
    async with session_scope() as session:
        success = await CategoryService.move_category_up(session=session, category_id=category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found or already at top")

        return SuccessResponse(message="Category moved up")


@router.post(
    "/{category_id}/move-down",
    summary="Move Category Down",
    description="Swap sort order to move a category down.",
)
async def move_category_down(category_id: int) -> SuccessResponse:
    async with session_scope() as session:
        success = await CategoryService.move_category_down(session=session, category_id=category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found or already at bottom")

        return SuccessResponse(message="Category moved down")


@router.post(
    "/move-items",
    summary="Move Items To Category",
    description="Assign selected items to the specified category.",
)
async def move_items_to_category(payload: MoveItemsToCategoryRequest) -> SuccessResponse:
    async with session_scope() as session:
        # Ensure category exists
        result = await session.execute(select(Category).where(Category.id == payload.category_id))
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        updated_count = await ItemService.move_items_to_category(
            session=session, category_id=payload.category_id, item_ids=payload.item_ids
        )
        await session.commit()

        return SuccessResponse(message=f"Items moved: {updated_count}")


@router.post(
    "/{category_id}/move-orphaned",
    summary="Move Orphaned Items",
    description="Assign items without a category to the specified category.",
)
async def move_orphaned_items_to_category(
    category_id: int, payload: MoveItemsToCategoryRequest | ItemIdsOnlyRequest
) -> SuccessResponse:
    async with session_scope() as session:
        # Ensure category exists
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Backward compatible: accept both full request (with category_id) and item_ids-only
        if isinstance(payload, ItemIdsOnlyRequest):
            item_ids = payload.item_ids
        else:
            if payload.category_id != category_id:
                raise HTTPException(status_code=400, detail="category_id mismatch between path and body")
            item_ids = payload.item_ids
        if not item_ids:
            raise HTTPException(status_code=400, detail="Item list cannot be empty")

        # Move items without categories
        update_stmt = (
            update(Item)
            .where(Item.id.in_(item_ids), Item.category_id.is_(None))
            .values(category_id=category_id)
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(update_stmt)
        updated_count = int(result.rowcount or 0)

        await session.commit()

        return SuccessResponse(message=f"Items moved: {updated_count}")
