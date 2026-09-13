# frontend

Vite + React + TypeScript. Scaffolded with:

```bash
npm create vite@latest . -- --template react-ts
```

## Running

```bash
npm install
npm run dev      # dev server on :5173
npm run build    # type-check + production build
npm run lint     # oxlint
```

Talks to the FastAPI backend on `http://localhost:8000` by default (override
with `VITE_API_BASE_URL`). The backend must have CORS open for
`http://localhost:5173` (already configured in `app/main.py`).

## Structure

Single page (`App.tsx`):

- `pages/WhatToPlay.tsx` — mood (free text) + available time, shows the
  recommendation as a Steam/Netflix-style grid of cards with cover art. Each
  card is either from your own backlog or a "New for you" discovery pick —
  both are real, verified Steam appids (see `app/api/recommend.py` on the
  backend for how discovery picks get checked against the real Steam
  catalog before ever reaching this page).
- `pages/LibraryDashboard.tsx` — backlog debt grouped by genre, below the
  recommendation section on the same page.

`api/client.ts` talks to the FastAPI backend (`/library`, `/stats`,
`/recommend`) — its types mirror `app/schemas.py` and `app/api/recommend.py`
on the backend by hand (no shared schema generation yet).
