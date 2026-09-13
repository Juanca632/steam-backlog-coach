import pytest
from sqlalchemy.orm import Session

from app.api import recommend as recommend_module
from app.models import AppDetails, Game, OwnedGame, PlayerAchievements


def _add_game(
    db: Session,
    appid: int,
    name: str,
    minutes: int,
    genres: str = "",
    achievements: tuple[int, int] | None = None,
) -> None:
    db.add(Game(appid=appid, name=name))
    db.add(OwnedGame(appid=appid, playtime_forever_minutes=minutes))
    if genres:
        db.add(AppDetails(appid=appid, genres=genres))
    if achievements is not None:
        unlocked, total = achievements
        db.add(PlayerAchievements(appid=appid, unlocked=unlocked, total=total))
    db.commit()


def _mock_complete(monkeypatch: pytest.MonkeyPatch, *replies: str) -> None:
    responses = iter(replies)
    monkeypatch.setattr(recommend_module.llm_client, "complete", lambda _prompt: next(responses))


def _mock_store_search(monkeypatch: pytest.MonkeyPatch, results: dict[str, dict | None]) -> None:
    monkeypatch.setattr(
        recommend_module.store_search, "find_game_by_title", lambda title: results.get(title)
    )


def test_recommend_returns_the_backlog_pick_the_llm_chose(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"backlog_pick": {"appid": 1, "reason": "Short runs fit your time."}, '
        '"discovery_picks": []}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    picks = response.json()["picks"]
    assert len(picks) == 1
    assert picks[0]["appid"] == 1
    assert picks[0]["name"] == "Hades"
    assert picks[0]["source"] == "library"
    assert "1/header.jpg" in picks[0]["header_image"]


def test_recommend_includes_resolved_discovery_picks(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"backlog_pick": {"appid": 1, "reason": "fits"}, '
        '"discovery_picks": ['
        '{"title": "Dead Cells", "reason": "similar vibe"}, '
        '{"title": "Not A Real Game Xyzzy", "reason": "made up"}'
        "]}",
    )
    _mock_store_search(
        monkeypatch,
        {"Dead Cells": {"appid": 588650, "name": "Dead Cells"}, "Not A Real Game Xyzzy": None},
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    picks = response.json()["picks"]
    assert len(picks) == 2
    assert picks[0]["source"] == "library"
    assert picks[1] == {
        "appid": 588650,
        "name": "Dead Cells",
        "reason": "similar vibe",
        "source": "discovery",
        "header_image": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg",
    }


def test_recommend_retries_once_on_invalid_backlog_appid(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"backlog_pick": {"appid": 999, "reason": "made up game"}, "discovery_picks": []}',
        '{"backlog_pick": {"appid": 1, "reason": "Correcting to the real one."}, '
        '"discovery_picks": []}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    assert response.json()["picks"][0]["appid"] == 1


def test_recommend_retries_once_on_malformed_json(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        "not json at all",
        '{"backlog_pick": {"appid": 1, "reason": "Here you go."}, "discovery_picks": []}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    assert response.json()["picks"][0]["appid"] == 1


def test_recommend_fails_after_exhausting_retries(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"backlog_pick": {"appid": 999, "reason": "made up"}, "discovery_picks": []}',
        '{"backlog_pick": {"appid": 998, "reason": "still made up"}, "discovery_picks": []}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 502


def test_recommend_excludes_finished_games_from_candidates(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Finished Game", minutes=50, genres="Indie", achievements=(10, 10))
    _mock_complete(
        monkeypatch,
        '{"backlog_pick": {"appid": 1, "reason": "should not be reached"}, '
        '"discovery_picks": []}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 404
