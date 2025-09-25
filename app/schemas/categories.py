from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Category title")
    sort_order: int = Field(100, ge=0, description="Sort order")

    @field_validator("title")
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Category title cannot be empty")
        return value.strip()


class CategoryUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100, description="Category title")
    sort_order: int | None = Field(None, ge=0, description="Sort order")

    @field_validator("title")
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Category title cannot be empty")
        return value.strip() if value is not None else value


class CategoryResponse(BaseModel):
    id: int
    title: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int


class MoveItemsToCategoryRequest(BaseModel):
    category_id: int = Field(..., description="Target category ID")
    item_ids: list[int] = Field(..., description="List of item IDs to move")

    @field_validator("item_ids")
    def validate_item_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("Item list cannot be empty")
        if len(set(value)) != len(value):
            raise ValueError("Items must be unique")
        return value


__all__ = [
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryListResponse",
    "MoveItemsToCategoryRequest",
]
