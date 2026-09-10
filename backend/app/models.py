"""Data models (SQLAlchemy).

Tables planned for Phase 1:

- Game        -> catalog: appid, name. A game that exists on Steam.
- OwnedGame   -> your relation to the game: playtime, last played.
- AppDetails  -> Store API metadata (genre, description). Permanent cache.
- PlayerAchievements -> achievement summary per game (unlocked / total).
- SyncState   -> state of the last sync so it can be resumed (which appids are left).
"""
