"""Schemas for public-facing API responses."""

from pydantic import BaseModel


class PublicSettingsResponse(BaseModel):
    site_name: str
    site_description: str
    currency_code: str
    currency_symbol: str
    currency_locale: str


__all__ = ["PublicSettingsResponse"]
