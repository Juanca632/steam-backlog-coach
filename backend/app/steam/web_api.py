"""Steam Web API client (official, uses an API key).

- get_owned_games(steam_id)                -> IPlayerService/GetOwnedGames
- get_player_achievements(steam_id, appid)  -> ISteamUserStats/GetPlayerAchievements

Returns raw dicts; mapping to models is done in sync.py.
"""

import httpx

from app.config import settings

BASE_URL = "https://api.steampowered.com"
TIMEOUT = 10.0


def get_owned_games(steam_id: str) -> list[dict]:
    """Return the raw `games` list from IPlayerService/GetOwnedGames.

    Each item has at least `appid`, `name`, `playtime_forever` (minutes),
    and `playtime_2weeks` (minutes, present only if played in the last 2
    weeks).
    """
    response = httpx.get(
        f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/",
        params={
            "key": settings.steam_api_key,
            "steamid": steam_id,
            "include_appinfo": True,
            "include_played_free_games": True,
            "format": "json",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("response", {}).get("games", [])


def get_player_achievements(steam_id: str, appid: int) -> dict | None:
    """Return the raw `playerstats` dict from ISteamUserStats/GetPlayerAchievements.

    Returns `None` when there's nothing usable to report, instead of a
    normal `success: true` body:
    - HTTP 400: the game has no achievements schema at all.
    - HTTP 403: "game details" privacy for that title blocks the API from
      seeing achievements, even though the game itself is public.
    """
    try:
        response = httpx.get(
            f"{BASE_URL}/ISteamUserStats/GetPlayerAchievements/v0001/",
            params={
                "key": settings.steam_api_key,
                "steamid": steam_id,
                "appid": appid,
                "format": "json",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (400, 403):
            return None
        raise

    stats = response.json().get("playerstats", {})
    return stats if stats.get("success") else None
