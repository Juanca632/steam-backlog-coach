from app.llm.prompt import Candidate, build_prompt
from app.llm.validate import validate_recommendation


def test_build_prompt_lists_every_candidate_appid():
    candidates = [
        Candidate(appid=10, name="Hades", genre="Roguelike", playtime_minutes=120, state="in_progress"),
        Candidate(appid=20, name="Celeste", genre="Platformer", playtime_minutes=0, state="untouched"),
    ]

    prompt = build_prompt(candidates, available_time_min=30, mood="relaxed")

    assert "appid=10" in prompt
    assert "Hades" in prompt
    assert "appid=20" in prompt
    assert "Celeste" in prompt
    assert "30 minutes" in prompt
    assert "relaxed" in prompt


def test_build_prompt_handles_missing_genre():
    candidates = [
        Candidate(appid=1, name="Mystery Game", genre="", playtime_minutes=5, state="untouched")
    ]

    prompt = build_prompt(candidates, available_time_min=10, mood="curious")

    assert "genre: unknown" in prompt


def test_validate_recommendation_splits_valid_and_invalid():
    valid, invalid = validate_recommendation([1, 2, 999], known_appids={1, 2, 3})

    assert valid == [1, 2]
    assert invalid == [999]


def test_validate_recommendation_all_invalid():
    valid, invalid = validate_recommendation([999], known_appids={1, 2, 3})

    assert valid == []
    assert invalid == [999]
