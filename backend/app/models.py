"""Data models (SQLAlchemy).

Tables:

- Game        -> catalog: appid, name. A game that exists on Steam.
- OwnedGame   -> your relation to the game: playtime, last played.
- AppDetails  -> Store API metadata (genre, description). Permanent cache.
- PlayerAchievements -> achievement summary per game (unlocked / total).
- SyncState   -> progress of the last sync, so it can be resumed.

Single user: there is no `user_id` anywhere. Each table has at most one row
per `appid`, since "owning" a game only ever means "the one Steam account
this project points at owns it".
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Game(Base):
    """A game that exists on Steam: the catalog entry, not the ownership relation.

    Populated from `GetOwnedGames` (appid + name come back together), and
    referenced by every other table via `appid`.
    """

    __tablename__ = "games"

    appid: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)

    owned: Mapped["OwnedGame"] = relationship(
        back_populates="game", uselist=False, cascade="all, delete-orphan"
    )
    details: Mapped["AppDetails"] = relationship(
        back_populates="game", uselist=False, cascade="all, delete-orphan"
    )
    achievements: Mapped["PlayerAchievements"] = relationship(
        back_populates="game", uselist=False, cascade="all, delete-orphan"
    )


class OwnedGame(Base):
    """Your relation to a game: playtime and when you last played it.

    Comes from `GetOwnedGames`, refreshed on every sync.
    """

    __tablename__ = "owned_games"

    appid: Mapped[int] = mapped_column(ForeignKey("games.appid"), primary_key=True)
    playtime_forever_minutes: Mapped[int] = mapped_column(default=0)
    playtime_2weeks_minutes: Mapped[int | None] = mapped_column(default=None)
    last_played_at: Mapped[datetime | None] = mapped_column(default=None)
    synced_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="owned")


class AppDetails(Base):
    """Store API `appdetails` metadata: genre + description.

    Genre and description don't change once a game is released, so this
    table is a **permanent cache** — `sync.py` must check for an existing
    row before ever calling the Store API for a given appid again.

    `genres` is stored as a comma-separated string rather than a normalized
    many-to-many table: a single user's library never needs to query "all
    games in genre X" at a scale where that indirection pays for itself.
    """

    __tablename__ = "app_details"

    appid: Mapped[int] = mapped_column(ForeignKey("games.appid"), primary_key=True)
    genres: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="details")


class PlayerAchievements(Base):
    """Achievement summary per game, from `GetPlayerAchievements`.

    Not every game has achievements at all; games without any simply have
    no row here.
    """

    __tablename__ = "player_achievements"

    appid: Mapped[int] = mapped_column(ForeignKey("games.appid"), primary_key=True)
    unlocked: Mapped[int] = mapped_column(default=0)
    total: Mapped[int] = mapped_column(default=0)
    synced_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="achievements")


class SyncState(Base):
    """Key/value progress tracker so `sync.py` can resume after being killed.

    Each sync step owns its own key (e.g. `owned_games_synced_at`,
    `achievements_synced_at`) instead of one big blob, so a partial run
    leaves an accurate, inspectable record of what actually finished. The
    slow, rate-limited `appdetails` step doesn't need a key here: its
    resumability comes from checking `AppDetails` for an existing row per
    appid, which this table's design intentionally leaves it to do.
    """

    __tablename__ = "sync_state"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str | None] = mapped_column(default=None)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
