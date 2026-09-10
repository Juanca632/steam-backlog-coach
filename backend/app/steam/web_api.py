"""Steam Web API client (official, uses an API key).

- get_owned_games(steam_id)                -> IPlayerService/GetOwnedGames
- get_player_achievements(steam_id, appid)  -> ISteamUserStats/GetPlayerAchievements

Returns raw dicts; mapping to models is done in sync.py.
"""
