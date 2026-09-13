"""Steam store catalog search (unofficial `storesearch` endpoint).

Used only for discovery recommendations: given an LLM-suggested game
title, confirms a real, existing Steam game and returns its real appid —
the same anti-hallucination principle as llm/validate.py's appid check,
applied to games outside the player's library. A search that fails or
comes up empty just means that suggestion gets dropped, not an error —
discovery picks are a bonus on top of the backlog pick, not the
guarantee the app is built around.
"""

import httpx

BASE_URL = "https://store.steampowered.com/api/storesearch/"
TIMEOUT = 10.0


def find_game_by_title(title: str) -> dict | None:
    """Return {"appid": int, "name": str} for the best match, or None."""
    try:
        response = httpx.get(
            BASE_URL, params={"term": title, "l": "english", "cc": "us"}, timeout=TIMEOUT
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    items = response.json().get("items", [])
    if not items:
        return None

    best = items[0]
    return {"appid": best["id"], "name": best["name"]}
