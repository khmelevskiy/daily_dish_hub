from pydantic import BaseModel, ConfigDict, Field, field_validator


class UnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Unit name")
    sort_order: int = Field(100, ge=0, description="Sort order")

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Unit name cannot be empty")
        return value.strip()


class UnitUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50, description="Unit name")
    sort_order: int | None = Field(None, ge=0, description="Sort order")

    @field_validator("name")
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Unit name cannot be empty")
        return value.strip() if value is not None else value


class UnitResponse(BaseModel):
    id: int
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class UnitListResponse(BaseModel):
    units: list[UnitResponse]
    total: int


class MoveItemsToUnitRequest(BaseModel):
    unit_id: int = Field(..., description="Target unit ID")
    item_ids: list[int] = Field(..., description="List of item IDs to move")

    @field_validator("item_ids")
    def validate_item_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("Item list cannot be empty")
        if len(set(value)) != len(value):
            raise ValueError("Items must be unique")
        return value


__all__ = [
    "UnitCreate",
    "UnitUpdate",
    "UnitResponse",
    "UnitListResponse",
    "MoveItemsToUnitRequest",
]
