"""Orchestrates the full library sync. Must be RESUMABLE.

Steps:
  1. GetOwnedGames         -> upsert Game + OwnedGame
  2. appdetails per appid   -> upsert AppDetails (skip already-cached)
  3. GetPlayerAchievements  -> upsert PlayerAchievements
  4. update SyncState after each step so it can resume if interrupted

Invoked by scripts/sync.py.
"""
