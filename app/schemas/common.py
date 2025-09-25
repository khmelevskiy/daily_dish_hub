from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    message: str
    data: dict | None = None


class ItemIdsOnlyRequest(BaseModel):
    item_ids: list[int] = Field(..., description="List of item IDs")


__all__ = [
    "SuccessResponse",
    "ItemIdsOnlyRequest",
]
