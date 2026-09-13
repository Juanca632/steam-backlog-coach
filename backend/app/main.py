"""FastAPI entry point. Creates the app and wires up the routers."""

from fastapi import FastAPI

from app.api import library

app = FastAPI(title="Steam Backlog Coach")
app.include_router(library.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Phase 3: from app.api import recommend; app.include_router(recommend.router)
