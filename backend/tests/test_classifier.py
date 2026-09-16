from app.backlog.classifier import classify
from app.models import AppDetails, OwnedGame, PlayerAchievements


def _owned(minutes: int) -> OwnedGame:
    return OwnedGame(appid=1, playtime_forever_minutes=minutes)


def _details(genres: str) -> AppDetails:
    return AppDetails(appid=1, genres=genres)


def _achievements(unlocked: int, total: int) -> PlayerAchievements:
    return PlayerAchievements(appid=1, unlocked=unlocked, total=total)


def test_zero_playtime_is_untouched():
    assert classify(_owned(0), None, None) == "untouched"


def test_zero_playtime_is_untouched_even_with_genre_and_achievements():
    assert classify(_owned(0), _details("RPG"), _achievements(0, 40)) == "untouched"


def test_no_genre_no_achievements_below_default_threshold_is_in_progress():
    assert classify(_owned(60), None, None) == "in_progress"


def test_no_genre_no_achievements_above_default_threshold_is_finished():
    assert classify(_owned(900), None, None) == "finished"


def test_roguelike_short_playtime_counts_as_finished():
    assert classify(_owned(150), _details("Roguelike"), None) == "finished"


def test_rpg_same_playtime_is_still_in_progress():
    assert classify(_owned(150), _details("RPG"), None) == "in_progress"


def test_rpg_long_playtime_is_finished():
    assert classify(_owned(2400), _details("Action, RPG"), None) == "finished"


def test_high_achievement_ratio_is_finished_regardless_of_playtime():
    assert classify(_owned(30), _details("RPG"), _achievements(18, 20)) == "finished"


def test_low_achievement_ratio_is_in_progress_even_with_long_playtime():
    assert classify(_owned(3000), _details("RPG"), _achievements(2, 20)) == "in_progress"


def test_achievements_with_zero_total_falls_back_to_playtime():
    assert classify(_owned(900), None, _achievements(0, 0)) == "finished"


def test_live_service_game_never_finishes_on_playtime_alone():
    assert (
        classify(_owned(100_000), _details("Action, Casual, Massively Multiplayer"), None)
        == "in_progress"
    )


def test_live_service_game_can_still_finish_via_achievements():
    assert (
        classify(_owned(100), _details("Massively Multiplayer"), _achievements(9, 10))
        == "finished"
    )
