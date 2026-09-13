"""Builds the recommendation prompt.

build_prompt(candidates, available_time_min, mood) -> str

- 'candidates' is the list of backlog games (appid, name, genre, playtime, state)
- the prompt requires the model to return ONLY appids from that list, as JSON
"""

from dataclasses import dataclass


@dataclass
class Candidate:
    """One backlog game as the LLM sees it: enough to reason about a pick."""

    appid: int
    name: str
    genre: str
    playtime_minutes: int
    state: str


def build_prompt(candidates: list[Candidate], available_time_min: int, mood: str) -> str:
    """Build the recommendation prompt.

    Lists every candidate explicitly and requires the model to reply with
    only an appid from that list. This is what makes "it can't invent
    games" enforceable: `validate.py` checks the reply against the same
    appids listed here, never trusting the model's output directly.
    """
    lines = "\n".join(
        f"- appid={c.appid} | {c.name} | genre: {c.genre or 'unknown'} | "
        f"playtime: {c.playtime_minutes}min | status: {c.state}"
        for c in candidates
    )
    return f"""You are recommending ONE game from the player's own Steam backlog.

Available time: {available_time_min} minutes
Mood: {mood}

Candidates (this is the complete list — you may ONLY recommend one of these appids):
{lines}

Reply with ONLY a JSON object, no other text, in this exact shape:
{{"appid": <int>, "reason": "<one sentence>"}}

The appid MUST be one of the appids listed above. Do not invent a game or an appid.
"""
