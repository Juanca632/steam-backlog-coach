"""Classifies each game in the library into a backlog state.

States: untouched | in_progress | finished

Signals:
- playtime (OwnedGame.playtime)
- achievement ratio (unlocked / total) when the game has achievements
- genre (a different playtime threshold for roguelike vs long RPG)

Achievement ratio wins whenever it's available: it's a direct signal of
completion, not a proxy. Genre-tuned playtime thresholds only come into
play when a game has no achievement schema at all, since that's the only
case where playtime is all we have. This is deliberately genre-tuned rather
than one fixed number: 2h in a roguelike is a normal amount of engagement,
2h in an 80h RPG barely counts as started.

Live-service / "Massively Multiplayer" games (Fall Guys, etc.) have no
completion state at all, so playtime alone can never mark them "finished" -
only a genuine achievement ratio can. Absent achievements, they cap at
"in_progress" no matter how many hours are logged.
"""

from typing import Literal

from app.models import AppDetails, OwnedGame, PlayerAchievements

BacklogState = Literal["untouched", "in_progress", "finished"]

# Genres where "finished" plausibly means dozens of hours, vs. genres where
# a single sitting can be a complete playthrough (or several).
LONG_GENRES = {"rpg", "strategy", "simulation"}
SHORT_GENRES = {"roguelike"}

# Games in these genres have no end state to reach - "Casual" describes
# session length, not a game you can complete, and gets misread as one.
LIVE_SERVICE_GENRES = {"massively multiplayer"}

DEFAULT_SUBSTANTIAL_MINUTES = 900  # 15h
LONG_SUBSTANTIAL_MINUTES = 2400  # 40h
SHORT_SUBSTANTIAL_MINUTES = 120  # 2h

FINISHED_ACHIEVEMENT_RATIO = 0.8


def classify(
    owned: OwnedGame,
    details: AppDetails | None,
    achievements: PlayerAchievements | None,
) -> BacklogState:
    """Return the backlog state for one owned game."""
    if owned.playtime_forever_minutes == 0:
        return "untouched"

    if achievements is not None and achievements.total > 0:
        ratio = achievements.unlocked / achievements.total
        return "finished" if ratio >= FINISHED_ACHIEVEMENT_RATIO else "in_progress"

    if _is_live_service(details):
        return "in_progress"

    threshold = _substantial_minutes(details)
    return "finished" if owned.playtime_forever_minutes >= threshold else "in_progress"


def _is_live_service(details: AppDetails | None) -> bool:
    if details is None or not details.genres:
        return False
    genres = {g.strip().lower() for g in details.genres.split(",")}
    return bool(genres & LIVE_SERVICE_GENRES)


def _substantial_minutes(details: AppDetails | None) -> int:
    """The playtime, in minutes, that counts as "finished" absent achievement data.

    Tuned by genre: a game with no genre info at all falls back to the
    default threshold rather than being treated as either extreme.
    """
    if details is None or not details.genres:
        return DEFAULT_SUBSTANTIAL_MINUTES

    genres = {g.strip().lower() for g in details.genres.split(",")}
    if genres & LONG_GENRES:
        return LONG_SUBSTANTIAL_MINUTES
    if genres & SHORT_GENRES:
        return SHORT_SUBSTANTIAL_MINUTES
    return DEFAULT_SUBSTANTIAL_MINUTES
