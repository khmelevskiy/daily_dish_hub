import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db import init_database
from app.middleware import rate_limit_middleware, security_middleware


# Logging setup (consistent format)
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

# Configure documentation exposure depending on environment
_env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").strip().lower()
# Prefer settings from .env via pydantic; fallback to ENV flags
_disable_docs = settings.disable_docs or (_env in {"prod", "production"})
_docs_url = None if _disable_docs else "/docs"
_redoc_url = None if _disable_docs else "/redoc"
_openapi_url = None if _disable_docs else "/openapi.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup phase ---
    # Initialize DB engine
    init_database()

    # Validate critical settings
    settings.validate()

    # DB schema is created in scripts/init_db.py during Docker startup

    # Seed initial data if tables are empty
    from app.db import session_scope
    from app.factories.initial_data import ensure_initial_data

    async with session_scope() as session:
        await ensure_initial_data(session=session)

    # Hand control to the application
    yield


app = FastAPI(
    title="Daily Dish Hub",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan,
)

# Infrastructure middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)
# Note: proxy header handling is primarily done via uvicorn's --proxy-headers.
# We avoid adding Starlette's ProxyHeadersMiddleware to keep a single source of truth
# and rely on ENABLE_PROXY_HEADERS/FORWARDED_ALLOW_IPS at the server layer.
if settings.cors_allow_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods_list or ["GET"],
        allow_headers=settings.cors_allow_headers_list or ["Authorization", "Content-Type"],
    )

# Register middleware (order matters!)
app.middleware("http")(security_middleware)  # Security checks first
app.middleware("http")(rate_limit_middleware)  # Then rate limiting

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/public/static", StaticFiles(directory="app/public/static"), name="public_static")

# Template directories
public_templates = Jinja2Templates(directory="app/public/templates")

# Include API routers
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def public_menu(request: Request):
    """Public menu page."""
    return public_templates.TemplateResponse(
        "menu.html",
        {
            "request": request,
            "site_name": settings.site_name,
            "site_description": settings.site_description,
            "currency_symbol": settings.currency_symbol,
            "currency_locale": settings.currency_locale,
            "currency_code": settings.currency_code,
            "csp_nonce": getattr(request.state, "csp_nonce", None),
        },
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Admin panel - React app."""
    try:
        return FileResponse("app/static/index.html")
    except FileNotFoundError:
        # Fallback if React build is missing
        return HTMLResponse(
            """
        <html>
        <head><title>Admin</title></head>
        <body>
        <h1>Error</h1>
        <p>React app is not built.</p>
        </body>
        </html>
        """
        )
