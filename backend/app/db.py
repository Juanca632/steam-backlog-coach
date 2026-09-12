"""SQLAlchemy engine and session over SQLite.

`Base` is the declarative base every table in `models.py` inherits from.
`get_db()` is a FastAPI dependency: it yields a session and always closes it,
even if the request raises.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite forbids sharing a connection across threads by default; FastAPI's
# threadpool means requests can land on a different thread than the one
# that created the connection, so this flag is required.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
