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


def test_recommend_returns_the_game_the_llm_picks(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(monkeypatch, '{"appid": 1, "reason": "Short runs fit your time."}')

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    body = response.json()
    assert body == {"appid": 1, "name": "Hades", "reason": "Short runs fit your time."}


def test_recommend_retries_once_on_invalid_appid(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"appid": 999, "reason": "made up game"}',
        '{"appid": 1, "reason": "Correcting to the real one."}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    assert response.json()["appid"] == 1


def test_recommend_retries_once_on_malformed_json(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        "not json at all",
        '{"appid": 1, "reason": "Here you go."}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 200
    assert response.json()["appid"] == 1


def test_recommend_fails_after_exhausting_retries(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Hades", minutes=60, genres="Roguelike")
    _mock_complete(
        monkeypatch,
        '{"appid": 999, "reason": "made up"}',
        '{"appid": 998, "reason": "still made up"}',
    )

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 502


def test_recommend_excludes_finished_games_from_candidates(client, db_session, monkeypatch):
    _add_game(db_session, 1, "Finished Game", minutes=50, genres="Indie", achievements=(10, 10))
    _mock_complete(monkeypatch, '{"appid": 1, "reason": "should not be reached"}')

    response = client.post("/recommend", json={"available_time_min": 30, "mood": "relaxed"})

    assert response.status_code == 404
