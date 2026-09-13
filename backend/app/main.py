"""FastAPI entry point. Creates the app and wires up the routers."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import library, recommend

app = FastAPI(title="Steam Backlog Coach")

# Single-user local dashboard: the frontend is the only client, always the
# Vite dev server on localhost. No wildcard, but no real access-control need
# either — see CLAUDE.md's scope note (no auth, no hosting concerns).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(library.router)
app.include_router(recommend.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
