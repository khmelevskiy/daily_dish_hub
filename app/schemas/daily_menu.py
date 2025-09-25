from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.items import ItemResponse


class DailyMenuCreate(BaseModel):
    item_ids: list[int] = Field(..., description="List of item IDs for the menu")

    @field_validator("item_ids")
    def validate_item_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("Items must be unique")
        return value


class DailyMenuItemResponse(BaseModel):
    id: int
    item_id: int
    daily_menu_id: int
    item: ItemResponse

    model_config = ConfigDict(from_attributes=True)


class DailyMenuResponse(BaseModel):
    id: int
    created_at: datetime
    items: list[DailyMenuItemResponse]

    model_config = ConfigDict(from_attributes=True)


class AddToMenuRequest(BaseModel):
    item_id: int = Field(..., description="ID of the item to add to today's menu")


class MenuDateRange(BaseModel):
    start_date: str = Field(..., description="Start date in format YYYY-MM-DD HH:MM")
    end_date: str = Field(..., description="End date in format YYYY-MM-DD HH:MM")

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if value is None:
            raise ValueError("Date value cannot be empty")
        candidate = value.strip()
        if not candidate:
            raise ValueError("Date value cannot be empty")
        normalized = candidate.replace("T", " ")
        try:
            return datetime.fromisoformat(normalized.replace(" ", "T"))
        except ValueError as exc:
            raise ValueError("Invalid datetime format. Use ISO 'YYYY-MM-DD HH:MM'.") from exc

    @field_validator("start_date", "end_date")
    def validate_iso_format(cls, value: str) -> str:
        parsed = cls._parse_datetime(value)
        return parsed.strftime("%Y-%m-%d %H:%M")

    @model_validator(mode="after")
    def validate_order(self) -> "MenuDateRange":
        start_dt = datetime.fromisoformat(self.start_date.replace(" ", "T"))
        end_dt = datetime.fromisoformat(self.end_date.replace(" ", "T"))
        if end_dt < start_dt:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class MenuDateInfo(BaseModel):
    start_date: str
    end_date: str
    current_date: str


class MenuDateResponse(BaseModel):
    menu_date: MenuDateInfo


__all__ = [
    "DailyMenuCreate",
    "DailyMenuItemResponse",
    "DailyMenuResponse",
    "AddToMenuRequest",
    "MenuDateRange",
    "MenuDateInfo",
    "MenuDateResponse",
]
