"""Builds the recommendation prompt.

build_prompt(candidates, available_time_min, mood) -> str

Asks for two things in one JSON reply:
- backlog_pick: one appid from the player's own backlog — the only field
  where the model is constrained to a fixed list (validated in
  llm/validate.py, retried on a miss).
- discovery_picks: a few real Steam games the player does NOT own, picked
  by genre affinity with their backlog. These are titles, not appids —
  app/steam/store_search.py resolves each one against the real Steam
  catalog before it ever reaches the user, so an unrecognized title is
  dropped rather than shown as if it were real.
"""

from dataclasses import dataclass

DISCOVERY_COUNT = 3


@dataclass
class Candidate:
    """One backlog game as the LLM sees it: enough to reason about a pick."""

    appid: int
    name: str
    genre: str
    playtime_minutes: int
    state: str


def build_prompt(candidates: list[Candidate], available_time_min: int, mood: str) -> str:
    """Build the recommendation prompt."""
    lines = "\n".join(
        f"- appid={c.appid} | {c.name} | genre: {c.genre or 'unknown'} | "
        f"playtime: {c.playtime_minutes}min | status: {c.state}"
        for c in candidates
    )
    return f"""You are a game recommendation coach.

Available time: {available_time_min} minutes
Mood: {mood}

The player's own backlog (their complete list of owned, unfinished games):
{lines}

Reply with ONLY a JSON object, no other text, in this exact shape:
{{
  "backlog_pick": {{"appid": <int>, "reason": "<one sentence>"}},
  "discovery_picks": [
    {{"title": "<exact official Steam game title>", "reason": "<one sentence>"}}
  ]
}}

Rules:
- "backlog_pick.appid" MUST be one of the appids listed above. Do not invent one.
- "discovery_picks" should have {DISCOVERY_COUNT} real, existing Steam games the
  player does NOT already own, chosen because they fit the available time,
  mood, and resemble genres from the backlog above. Use exact, correctly
  spelled official titles — each one will be looked up in the Steam store
  catalog, and a misspelled or made-up title will be dropped.
"""
