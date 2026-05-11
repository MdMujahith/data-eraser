"""Database engine, session factory, and lifecycle management."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.db.models import Base

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(database_url: str | None = None) -> Engine:
    """Initialise the SQLAlchemy engine and create all tables.

    Args:
        database_url: Override; defaults to ``settings.database_url``.

    Returns:
        The configured :class:`~sqlalchemy.engine.Engine`.
    """
    global _engine, _SessionLocal

    if database_url is None:
        from privacy_toolkit.config.settings import get_settings
        database_url = get_settings().database_url

    # Ensure parent directory exists for SQLite
    if database_url.startswith("sqlite:///"):
        db_path = Path(database_url[len("sqlite:///"):])
        db_path.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        echo=False,
    )

    # Enable WAL mode and foreign keys for SQLite
    if "sqlite" in database_url:
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn: object, _: object) -> None:
            cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    logger.info("Database initialised: %s", database_url)
    return _engine


def get_engine() -> Engine:
    """Return the active engine, initialising if needed."""
    global _engine
    if _engine is None:
        _engine = init_db()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory, initialising if needed."""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager yielding a database session with auto-commit/rollback.

    Usage::

        with get_db() as db:
            db.add(some_model)
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def health_check() -> bool:
    """Return ``True`` if the database is reachable."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return False


def reset_db(database_url: str | None = None) -> None:
    """Drop and recreate all tables — **destructive**, for tests only."""
    global _engine, _SessionLocal
    if _engine:
        Base.metadata.drop_all(_engine)
        _engine = None
        _SessionLocal = None
    init_db(database_url)
