from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DailyMenuItem(Base):
    __tablename__ = "daily_menu_items"

    __table_args__ = (UniqueConstraint("daily_menu_id", "item_id", name="uq_daily_menu_items_daily_menu_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    daily_menu_id: Mapped[int] = mapped_column(ForeignKey("daily_menus.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)


__all__ = ["DailyMenuItem"]
