"""Orchestrates the full library sync. Must be RESUMABLE.

Steps:
  1. GetOwnedGames         -> upsert Game + OwnedGame
  2. appdetails per appid   -> upsert AppDetails (skip already-cached)
  3. GetPlayerAchievements  -> upsert PlayerAchievements
  4. update SyncState after each step so it can resume if interrupted

Invoked by scripts/sync.py.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import Game, OwnedGame, PlayerAchievements, SyncState
from app.steam import store_api, web_api


def run() -> None:
    """Entry point: create tables if needed, run every step, close the session.

    Safe to call again after being killed mid-way: each step either skips
    what's already cached (appdetails) or upserts idempotently (games,
    achievements), so nothing gets duplicated or lost.
    """
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        sync_owned_games(db)
        sync_app_details(db)
        sync_achievements(db)
    finally:
        db.close()


def sync_owned_games(db: Session) -> None:
    """Step 1: upsert Game + OwnedGame for everything GetOwnedGames returns."""
    games = web_api.get_owned_games(settings.steam_id)

    for raw in games:
        appid = raw["appid"]

        game = db.get(Game, appid)
        if game is None:
            game = Game(appid=appid, name=raw["name"])
            db.add(game)
        else:
            game.name = raw["name"]

        owned = db.get(OwnedGame, appid)
        if owned is None:
            owned = OwnedGame(appid=appid)
            db.add(owned)

        last_played = raw.get("rtime_last_played")
        owned.playtime_forever_minutes = raw.get("playtime_forever", 0)
        owned.playtime_2weeks_minutes = raw.get("playtime_2weeks")
        owned.last_played_at = (
            datetime.utcfromtimestamp(last_played) if last_played else None
        )
        owned.synced_at = datetime.utcnow()

    db.commit()
    _mark_step_done(db, "owned_games_synced_at")


def sync_app_details(db: Session) -> None:
    """Step 2: fetch (or reuse) AppDetails for every owned appid.

    `store_api.get_app_details` checks the cache and commits per appid
    itself, so this loop can be killed and re-run at any point — a resume
    only ever pays the network cost for appids that never got cached.
    """
    for (appid,) in db.query(Game.appid).all():
        store_api.get_app_details(db, appid)

    _mark_step_done(db, "app_details_synced_at")


def sync_achievements(db: Session) -> None:
    """Step 3: upsert PlayerAchievements for every owned appid.

    Unlike AppDetails, achievement counts change over time, so this step
    always re-fetches — it's an upsert, not a cache. Games with no
    achievements schema at all get no row (see `web_api.get_player_achievements`).
    """
    for (appid,) in db.query(Game.appid).all():
        stats = web_api.get_player_achievements(settings.steam_id, appid)
        if stats is None:
            continue

        achievements = stats.get("achievements", [])
        record = db.get(PlayerAchievements, appid)
        if record is None:
            record = PlayerAchievements(appid=appid)
            db.add(record)

        record.unlocked = sum(1 for a in achievements if a.get("achieved"))
        record.total = len(achievements)
        record.synced_at = datetime.utcnow()
        db.commit()

    _mark_step_done(db, "achievements_synced_at")


def _mark_step_done(db: Session, key: str) -> None:
    """Record that a sync step finished, so `run()` history is inspectable."""
    now = datetime.utcnow()
    state = db.get(SyncState, key)
    if state is None:
        db.add(SyncState(key=key, value=now.isoformat(), updated_at=now))
    else:
        state.value = now.isoformat()
        state.updated_at = now
    db.commit()
