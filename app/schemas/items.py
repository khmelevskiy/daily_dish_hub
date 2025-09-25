from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict, Field, condecimal, field_serializer, field_validator


PRICE_DECIMAL = condecimal(max_digits=10, decimal_places=2, ge=Decimal("0.00"))
POSITIVE_PRICE_DECIMAL = condecimal(max_digits=10, decimal_places=2, gt=Decimal("0.00"))
PRICE_QUANTIZE = Decimal("0.01")


class ItemCreate(BaseModel):
    category_id: int = Field(..., description="Item category ID")
    unit_id: int | None = Field(None, description="Unit ID")
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    price: POSITIVE_PRICE_DECIMAL = Field(..., description="Item price")  # type: ignore[misc]
    description: str | None = Field(None, max_length=1000, description="Item description")
    image_id: int | None = Field(None, description="Image ID")

    @field_validator("price")
    def normalize_price(cls, value: Decimal) -> Decimal:
        return value.quantize(PRICE_QUANTIZE, rounding=ROUND_HALF_UP)


class ItemUpdate(BaseModel):
    category_id: int | None = Field(None, description="Item category ID")
    unit_id: int | None = Field(None, description="Unit ID")
    name: str | None = Field(None, min_length=1, max_length=255, description="Item name")
    price: PRICE_DECIMAL | None = Field(None, description="Item price")  # type: ignore[misc]
    description: str | None = Field(None, max_length=1000, description="Item description")
    image_id: int | None = Field(None, description="Image ID")

    @field_validator("price")
    def normalize_price(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value <= Decimal("0"):
            raise ValueError("Price must be greater than 0")
        return value.quantize(PRICE_QUANTIZE, rounding=ROUND_HALF_UP)


class ItemResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    description: str | None
    category_id: int | None
    category_title: str | None
    unit_id: int | None
    image_id: int | None
    image_filename: str | None
    image_url: str | None
    unit_name: str | None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        return float(value)


class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int


__all__ = [
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "ItemListResponse",
    "PRICE_DECIMAL",
    "POSITIVE_PRICE_DECIMAL",
    "PRICE_QUANTIZE",
]
