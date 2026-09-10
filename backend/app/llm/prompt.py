"""Builds the recommendation prompt.

build_prompt(candidates, available_time_min, mood) -> str

- 'candidates' is the list of backlog games (appid, name, genre, playtime, state)
- the prompt requires the model to return ONLY appids from that list, as JSON
"""
