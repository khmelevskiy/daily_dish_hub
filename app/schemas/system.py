"""Schemas for system and infrastructure endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


__all__ = ["HealthResponse"]
