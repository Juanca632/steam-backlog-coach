from sqlalchemy.orm import Session

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


def test_library_groups_by_genre_and_reports_state(client, db_session: Session):
    _add_game(db_session, 1, "Hollow Knight", minutes=0, genres="Action, Metroidvania")
    _add_game(db_session, 2, "Baldur's Gate 3", minutes=3000, genres="RPG")

    response = client.get("/library")
    assert response.status_code == 200
    body = response.json()

    genres = {group["genre"]: group["games"] for group in body["genres"]}
    assert set(genres) == {"Action", "Metroidvania", "RPG"}
    assert genres["Action"][0]["state"] == "untouched"
    assert genres["RPG"][0]["state"] == "finished"


def test_library_uses_uncategorized_bucket_when_no_genre_data(client, db_session: Session):
    _add_game(db_session, 1, "Unknown Game", minutes=30)

    response = client.get("/library")
    body = response.json()

    assert len(body["genres"]) == 1
    assert body["genres"][0]["genre"] == "Uncategorized"


def test_stats_totals_and_per_genre_counts(client, db_session: Session):
    _add_game(db_session, 1, "Untouched Game", minutes=0, genres="Indie")
    _add_game(db_session, 2, "Finished Game", minutes=10, genres="Indie", achievements=(9, 10))
    _add_game(db_session, 3, "In Progress RPG", minutes=100, genres="RPG")

    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()

    assert body["total"] == {"untouched": 1, "in_progress": 1, "finished": 1}

    by_genre = {entry["genre"]: entry["counts"] for entry in body["by_genre"]}
    assert by_genre["Indie"] == {"untouched": 1, "in_progress": 0, "finished": 1}
    assert by_genre["RPG"] == {"untouched": 0, "in_progress": 1, "finished": 0}


def test_ignores_games_with_no_owned_row(client, db_session: Session):
    db_session.add(Game(appid=99, name="Not actually owned"))
    db_session.commit()

    response = client.get("/library")
    assert response.json()["genres"] == []
