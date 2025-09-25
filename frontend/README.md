# Frontend (Vite + React)

This frontend is built with Vite and React (TypeScript). It is served by the backend in production (bundled into `app/static` during Docker image build) and can be run independently in development.

For end-to-end setup instructions, follow the root [README](../README.md) and [QUICKSTART](../QUICKSTART.md). The notes below focus on frontend-only tasks.

## Scripts

- `npm run dev` — start Vite dev server on `http://localhost:3000` (see `vite.config.ts`).
- `npm run build` — production build to `frontend/dist` and copy assets to `app/static` using `copy-build`.
- `npm run preview` — preview a production build locally.

## Development

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

The backend API typically runs at `http://localhost:8000`. The app uses relative URLs when served by the backend. For separate dev servers, configure the API base if needed.

## API base (dev-only, optional)

When running the frontend and backend on different origins, set a base URL for API calls and enable CORS on the backend:

```env
# example: frontend/.env.local
VITE_API_BASE=http://localhost:8000
```

Then ensure the backend has `CORS_ALLOW_ORIGINS=http://localhost:3000` in `.env` (or start both on the same origin via the backend).

## Build

```bash
cd frontend
npm run build
# copies dist/index.html + assets into app/static
```

In Docker, the multi-stage build performs the Vite build and copies the generated assets into the image automatically.

## Notes

- The dev server port is configured in `vite.config.ts` (`port: 3000`).
- In production, assets are served from `/static` on the backend.
- Admin UI uses Bearer tokens in `localStorage`; login happens via `/auth/login`.
