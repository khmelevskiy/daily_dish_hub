"""Health and status endpoints."""

from fastapi import APIRouter

from app import __version__
from app.schemas.system import HealthResponse


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    """Simple healthcheck endpoint for monitoring."""
    return HealthResponse(status="ok", version=__version__)
