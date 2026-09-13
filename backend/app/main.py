"""FastAPI entry point. Creates the app and wires up the routers."""

from fastapi import FastAPI

from app.api import library, recommend

app = FastAPI(title="Steam Backlog Coach")
app.include_router(library.router)
app.include_router(recommend.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
