# frontend

Scaffolded in Phase 4 with Vite:

```bash
npm create vite@latest . -- --template react-ts
```

Two planned screens:

- `pages/LibraryDashboard.tsx` — backlog debt grouped by genre
- `pages/WhatToPlay.tsx` — time + mood input, shows the recommendation

`api/client.ts` talks to the FastAPI backend (`/library`, `/stats`, `/recommend`).
