"""Pydantic models for API responses (what the frontend consumes)."""

from pydantic import BaseModel

from app.backlog.classifier import BacklogState


class GameSummary(BaseModel):
    """One owned game as the frontend needs it: identity, playtime, backlog state."""

    appid: int
    name: str
    playtime_forever_minutes: int
    state: BacklogState
    header_image: str


class GenreGroup(BaseModel):
    """Every owned game that lists this genre among its (possibly several) genres."""

    genre: str
    games: list[GameSummary]


class LibraryResponse(BaseModel):
    genres: list[GenreGroup]


class StateCounts(BaseModel):
    untouched: int = 0
    in_progress: int = 0
    finished: int = 0


class GenreStats(BaseModel):
    genre: str
    counts: StateCounts


class StatsResponse(BaseModel):
    total: StateCounts
    by_genre: list[GenreStats]
