# 🗺️ Daily Dish Hub Technical Atlas

## 1. 🧭 Project Overview

Daily Dish Hub is a full-stack platform for publishing a daily cafeteria menu. It combines a FastAPI backend, a React-based admin dashboard, PostgreSQL storage, Redis-powered rate limiting, and an aiogram Telegram bot so that both guests and administrators have convenient entry points.

### 1.1 Key Capabilities

- **Public menu site** served from FastAPI templates with a rich client-side cart and formatting features.
- **Admin single-page application** (React + TypeScript) for managing categories, items, images, and daily menu composition.
- **Telegram bot** that answers `/menu`, `/start`, and `/help`, reusing the backend service layer.
- **Strong security defaults** including JWT auth, bcrypt passwords, CSP + security middleware, rate limiting, and production-safe configuration validation.
- **Image processing pipeline** that validates uploads, normalizes formats, and stores binaries directly in PostgreSQL.
- **Automated setup tooling** (shell scripts, Alembic migrations, uv-based dependency management) for local and Dockerized environments.

### 1.2 Runtime Components

- **Backend API (`app/`)** — FastAPI application entry point in `app/web.py`, with modular routers in `app/api/` and business logic under `app/services/`.
- **Database layer (`app/models/`, `app/db/`)** — SQLAlchemy models, async session helpers, and Alembic migrations in `migrations/`.
- **Frontend (`frontend/`)** — React/Vite project compiled into static assets consumed by the backend.
- **Background bot (`app/bot/__init__.py`)** — aiogram dispatcher sharing service code with the web API.
- **Tooling (`scripts/`)** — Shell/Python utilities that bootstrap, build, deploy, and maintain the project.
- **Test suite (`tests/`)** — Functional security/rate-limit tests plus unit coverage for utilities and services.

## 2. 📂 Directory & File Reference

### 2.1 Root Files

- `README.md` — High-level overview highlighting features, deployment notes, and documentation links.
- `CONTRIBUTING.md` — Contribution workflow, test expectations, and development tips.
- `LICENSE` — Project license file.
- `pyproject.toml` & `uv.lock` — uv-managed dependency definitions for backend tooling.
- `docker-compose.yml` — Multi-service compose stack (app, bot, Postgres, Redis) with health checks and environment wiring.
- `Dockerfile` — Multi-stage build that compiles the frontend, installs Python dependencies with uv, and boots Uvicorn via `start.sh`.
- `alembic.ini` — Alembic configuration referenced by migrations utilities.
- `env.example` — Sample environment variables covering secrets, DB, rate limits, and CORS/security tuning.

### 2.2 `app/` — Backend Application

- `__init__.py` — Declares package version (`__version__`), synchronized with `pyproject.toml`.
- `web.py` — FastAPI application factory: sets up docs exposure, mounts middleware (`TrustedHostMiddleware`, custom security & rate limiting), serves static assets, registers routers, provides public endpoints (`/public/daily-menu`, `/public/menu-date`, `/public/settings`, `/health`), and seeds initial data on startup.

#### `app/api/` — REST Routers

- `__init__.py` — Constructs the aggregated API router, defines admin token verification dependency, and wires sub-routers under `/auth`, `/images`, and `/admin/*` prefixes.
- `auth.py` — Authentication endpoints: login (JWT issuance), register/list/update/delete users, plus `get_current_user` helpers used by other routers.
- `categories.py` — Admin CRUD for menu categories (create/update/delete, ordering helpers, moving items between categories, handling orphaned items).
- `daily_menu.py` — Admin endpoints for viewing, replacing, clearing, and manipulating the daily menu, including menu date window management.
- `images.py` — Admin image management: upload via `ImageService`, list stored binaries, delete by ID; now responds with typed `ImageResponse` objects.
- `items.py` — Admin endpoints for items: listing with metadata, fetching orphaned/no-unit items, CRUD, moving items across categories/units.
- `public_images.py` — Public CDN-like endpoint serving stored images with cache headers, sanitised filenames, and ETag/If-Modified-Since handling.
- `units.py` — Admin CRUD for measurement units, reordering operations, and utilities to assign items to specific units.

#### `app/bot/`

- `__init__.py` — aiogram dispatcher registering `/start`, `/menu`, `/help` commands, replying with plain-text messages. Validates `BOT_TOKEN` before polling and reuses `BotService` plus shared DB session helpers.

#### `app/core/`

- `config.py` — Pydantic settings loader covering secrets, database URLs, rate limiting, CORS/CSP, trusted hosts, and validation helpers (e.g., enforce strong `SECRET_KEY`, production host restrictions).
- `logging_config.py` — Centralized logging formatter and configuration applied during app startup.

#### `app/db/`

- `engine.py` — Builds the async SQLAlchemy engine based on current settings.
- `session.py` — Initializes and exposes the global async engine/session factory with transaction helpers.
- `models.py` — Declarative base shared across ORM models.

#### `app/factories/`

- `initial_data.py` — Startup seed ensuring default categories and units exist when database is empty.

#### `app/middleware/`

- `__init__.py` — Re-exports middleware factories.
- `rate_limit.py` — Custom per-route rate limiter (memory or Redis backend), handles proxy header parsing, returns consistent 429 payloads, and appends rate-limit headers.
- `security.py` — Request hardening middleware blocking dangerous methods, suspicious user agents, traversal/injection patterns, and injecting security headers (CSP, HSTS, COOP/CORP, Permissions-Policy).

#### `app/models/`

- `__init__.py` - SQLAlchemy base model declaration.
- `category.py` — SQLAlchemy model for menu categories with sort order and backref to items.
- `unit.py` — Measurement unit model shared across items.
- `image.py` — Stored image metadata and binary payload relationship to items.
- `item.py` — Menu item entity referencing category, unit, and optional image.
- `daily_menu.py` — Current daily menu header (one active row maintained).
- `daily_menu_item.py` — Association table linking daily menu entries to items.
- `user.py` — Administrative user accounts with active/admin flags and timestamps.
- `menu_settings.py` — Key-value store for menu-specific settings (e.g., date window).

#### `app/schemas/`

- `auth.py` — Pydantic models for user creation/update, login responses, and token payloads.
- `categories.py` — Schemas for category CRUD and item move operations.
- `common.py` — Shared models (`SuccessResponse`, `ItemIdsOnlyRequest`).
- `daily_menu.py` — Schemas for daily menu operations, including `DailyMenuResponse`, `DailyMenuItemResponse`, `MenuDateRange`, `MenuDateResponse`.
- `images.py` — `ImageResponse` and `ImageListResponse` describing stored image metadata.
- `items.py` — Validation models for item creation/update plus list/response wrappers.
- `units.py` — Schemas for unit CRUD and bulk item reassignment.

#### `app/services/`

- `__init__.py` — Aggregated service exports.
- `base_service.py` — Generic CRUD helpers (create, get, update) reused by other services.
- `bot_service.py` — Business logic used by the Telegram bot (`get_simple_menu_text`, static welcome/help messages).
- `category_service.py` — Category CRUD logic, including order normalization and movement helpers.
- `formatting.py` — Currency/Decimal helpers for consistent price formatting and normalization.
- `image_service.py` — Image ingestion/compression pipeline (validation, JPEG re-encoding, filename generation, CMS-like metadata helpers).
- `item_service.py` — Item CRUD helpers with detail joins, validation of related entities, and bulk category/unit updates.
- `menu_service.py` — Core menu orchestration (create/replace/clear menu, fetch menu items with joins, manage menu date, public serialization).
- `unit_service.py` — Unit CRUD, reordering, and item reassignment utilities.
- `user_service.py` — User management (bcrypt hashing, JWT creation/verification, policy enforcement).

#### `app/static/`

- `index.html`, `assets/` — Build artifacts from the frontend (Vite) used for the React admin app.
- Shared static assets for the SPA (favicon, manifest, etc.).

#### `app/public/`

- `templates/menu.html` — Public menu Jinja template with site metadata, CSP nonce support, and cart markup.
- `static/css/menu.css`, `static/js/menu.js` — Bundled styles and script powering the standalone public menu experience.

### 2.3 `migrations/` - alembic migrations

- `env.py` — Alembic environment script wiring uv configuration and database URL selection.
- `versions/bdfcdaebcab1_initial.py` — Initial schema migration creating all core tables, indexes, and constraints.

### 2.4 `frontend/` — React Admin App

- `package.json` & `package-lock.json` — Frontend dependencies (React 19, Vite, Vitest, Testing Library, TypeScript).
- `src/index.tsx` — React entry point mounting `<App />` and bootstrapping global styles.
- `src/App.tsx` — Main SPA container orchestrating auth state, tabs (menu, items, categories, units, images), network calls, and modal workflows.
- `src/App.css`, `src/index.css`, `src/styles/*.css` — Stylesheets for layout, components, responsiveness, and UI modules.
- `src/components/`:
  - `Header.tsx` — Topbar with user info and public menu shortcut.
  - `Sidebar.tsx` — Navigation tabs and layout scaffolding.
  - `auth/LoginForm.tsx` — Authentication form interacting with `useAuth` hook.
  - `categories/CategoryManager.tsx` — Category list, editing, moving items, and orphan management UI.
  - `images/ImageManager.tsx` — Gallery plus upload/delete controls for images.
  - `items/AddItem.tsx` — Form for creating new items, selecting category/unit/image.
  - `items/ManageItems.tsx` — Table view for editing and deleting existing items.
  - `menu/ManageMenu.tsx` — Daily menu builder with filters, date controls, and add/remove actions.
  - `modals/ModalRoot.tsx` — Centralized modal renderer for CRUD dialogs.
  - `ui/TimeSpinner.tsx` & `.css` — Reusable numeric spinner for hour/minute selection.
  - `units/UnitManager.tsx` — Unit administration UI with item reassignment helpers.
- `src/hooks/`:
  - `useAuth.ts` — Auth state, token storage, login/logout helpers.
  - `useCategories.ts` — Fetch/update categories, handle orphan moves, provide modal helpers.
  - `useImages.ts` — Lazy load, upload, and delete image metadata.
  - `useMenu.ts` — Manage menu builder state, local item cache, persistence to backend.
  - `useModal.ts` — Modal state machine for the SPA.
  - `useSettings.ts` — Fetch and cache public settings (`/public/settings`), provide price formatter.
  - `useUnits.ts` — Unit management state similar to categories.
- `src/services/`:
  - `api.ts` — Fetch wrapper centralizing API calls, error normalization, and rate-limit metadata handling.
  - `config.ts` — Utility for combining base URLs (supports Vite env overrides).
- `src/types/types.ts` — Shared TypeScript interfaces mirroring backend schemas (items, categories, units, images, menu, responses).
- `src/utils/itemUtils.ts` — Helper functions for grouping and filtering item lists.
- `src/App.test.tsx`, `src/setupTests.ts` — React Testing Library harness.

### 2.5 `scripts/`

- `setup.sh` — Interactive project bootstrap: installs uv, node modules, ensures `.env` exists with strong secrets, runs pre-commit setup.
- `run_web.sh`, `run_bot.sh` — Convenience launchers for backend, bot, and Vite dev server.
- `run_docker.sh` — CLI for Docker compose lifecycle (build/up/down/logs/clean).
- `init_db.py` & `init_db.sh` — Database initialization, migrations execution, optional admin creation.
- `migrate.py` — Friendly wrapper around Alembic commands using uv.
- `create_admin.py` — Interactive CLI to add the first admin user via services.
- `reset.sh` — Cleanup script removing caches/build artifacts and rebuilding frontend.
- `update_secrets.sh` — Manage `detect-secrets` baseline.

### 2.6 `tests/`

- `README.md` — Test suite overview and execution instructions.
- `conftest.py` — Pytest fixtures for HTTP client, base URL, and pacing configuration.
- `run_all.sh` — Orchestrates functional tests in a safe order (admin/security before aggressive rate tests).
- `test_admin_protection_smoke.py` — Verifies admin endpoints require authentication.
- `test_security.py` — Exercises middleware against SQLi/XSS/traversal payloads, suspicious methods, headers, and health endpoint.
- `test_rate_limiter.py` — Stress test hammering admin/auth/public endpoints for 429 behavior under bursts and concurrency.
- `test_admin_permissions.py` — Validates role-based access (admin vs non-admin) by interacting with `/auth/register` and `/admin/items`.
- `test_api_dependencies.py` — Static assertion that admin/public routes keep required dependency wiring.
- `test_session_init.py` — Guards against accidental database engine reinitialization between CLI tools.
- `test_ordered_entity_service.py` — Verifies ordered CRUD helpers honour explicit sort order and clean related references.
- `test_menu_service.py` — Ensures menu queries expose limit/offset semantics without N+1 issues.
- `test_image_service_unit.py` — Unit coverage for image processing, size validation, and HTTP error mapping.
- `test_utils_unit.py` — Tests formatting helpers and filename sanitization logic.

### 2.7 `docs/`

- `README.md` — Architecture, data flow, API summary, deployment notes, and testing guidance.
- `QUICKSTART.md` — Step-by-step local setup instructions, including Telegram bot creation tips.
- `DOCKER.md` — Guidance for containerized workflows, compose commands, and production notes.
- `SECURITY.md` — Mandatory configuration requirements, threat mitigations, and response checklists.
- `TODO.md` — Running backlog of enhancements and chores.
- `SCREENSHOTS.md` — Planned visual assets with references to stored media.
- Media assets (`pics/`) — Example GIFs and PNGs referenced in documentation.
- `Daily_Dish_Hub_Technical_Atlas.md` — (this document) comprehensive technical reference created for deep-dive reviews.

## 3. 🔁 Cross-Cutting Notes

- **Shared Services:** Backend services (`app/services`) are reused by both API endpoints and the Telegram bot, ensuring consistent business rules.
- **Rate Limiting & Security:** Middleware ordering in `app/web.py` ensures security checks happen before rate limiting, yielding detailed logs for suspicious patterns.
- **Static Asset Workflow:** The frontend builds into `app/static/`; Dockerfile copies Vite output, while dev scripts use hot reload via Vite.
- **Configuration Validation:** `Settings.validate()` is called on startup for both web and bot to fail fast when secrets or trusted hosts are misconfigured.
- **Testing Philosophy:** Functional tests expect a running server; unit tests rely on uv/pytest and can be executed without external dependencies.
