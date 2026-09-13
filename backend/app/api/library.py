"""Library read endpoints.

- GET /library -> games grouped by genre, with their backlog state.
- GET /stats   -> "debt" numbers: totals per state and per genre.

A game with several genres (e.g. "Action, RPG") appears in every matching
group; a game with no genre info at all (AppDetails missing, or Store API
reported it as unavailable) falls into a single "Uncategorized" bucket
rather than being dropped.
"""

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backlog.classifier import BacklogState, classify
from app.db import get_db
from app.models import AppDetails, Game
from app.schemas import (
    GameSummary,
    GenreGroup,
    GenreStats,
    LibraryResponse,
    StateCounts,
    StatsResponse,
)

router = APIRouter()

UNCATEGORIZED = "Uncategorized"


@router.get("/library", response_model=LibraryResponse)
def get_library(db: Session = Depends(get_db)) -> LibraryResponse:
    by_genre: dict[str, list[GameSummary]] = defaultdict(list)

    for game in _owned_games(db):
        summary = GameSummary(
            appid=game.appid,
            name=game.name,
            playtime_forever_minutes=game.owned.playtime_forever_minutes,
            state=classify(game.owned, game.details, game.achievements),
        )
        for genre in _genre_names(game.details):
            by_genre[genre].append(summary)

    groups = [
        GenreGroup(genre=genre, games=games) for genre, games in sorted(by_genre.items())
    ]
    return LibraryResponse(genres=groups)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total = StateCounts()
    by_genre: dict[str, StateCounts] = {}

    for game in _owned_games(db):
        state = classify(game.owned, game.details, game.achievements)
        _increment(total, state)

        for genre in _genre_names(game.details):
            _increment(by_genre.setdefault(genre, StateCounts()), state)

    genre_stats = [
        GenreStats(genre=genre, counts=counts) for genre, counts in sorted(by_genre.items())
    ]
    return StatsResponse(total=total, by_genre=genre_stats)


def _owned_games(db: Session) -> list[Game]:
    """Every Game that's actually owned (has an OwnedGame row)."""
    return [game for game in db.query(Game).all() if game.owned is not None]


def _genre_names(details: AppDetails | None) -> list[str]:
    """Split the comma-separated genre string; falls back to a single bucket."""
    if details is None or not details.genres:
        return [UNCATEGORIZED]
    return [g.strip() for g in details.genres.split(",")]


def _increment(counts: StateCounts, state: BacklogState) -> None:
    setattr(counts, state, getattr(counts, state) + 1)
