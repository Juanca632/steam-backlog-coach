"""FastAPI entry point. Creates the app and wires up the routers."""

from fastapi import FastAPI

app = FastAPI(title="Steam Backlog Coach")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Phase 2/3: include routers
# from app.api import library, recommend
# app.include_router(library.router)
# app.include_router(recommend.router)
