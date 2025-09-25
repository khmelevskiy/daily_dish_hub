from fastapi import APIRouter, Depends

from app.api import auth, categories, daily_menu, health, images, items, public, public_images, units
from app.api.dependencies import verify_admin_token


api_router = APIRouter()

# Public endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(public_images.router, prefix="/images", tags=["public-images"])
api_router.include_router(public.router, prefix="/public")
api_router.include_router(health.router)

# Admin endpoints (prefix /admin, protected)
admin_router = APIRouter(prefix="/admin", dependencies=[Depends(verify_admin_token)])
admin_router.include_router(items.router, prefix="/items", tags=["items"])
admin_router.include_router(categories.router, prefix="/categories", tags=["categories"])
admin_router.include_router(units.router, prefix="/units", tags=["units"])
admin_router.include_router(images.router, prefix="/images", tags=["images"])
admin_router.include_router(daily_menu.router, prefix="/daily-menu", tags=["daily-menu"])

api_router.include_router(admin_router)
