"""SQLAlchemy configuration, declarative base, and request-scoped session."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all REVIVE domain models."""


@lru_cache
def get_engine() -> Engine:
    """Create the configured PostgreSQL engine on first use."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory on first use."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session.

    The caller is responsible for committing any changes.  The session is
    always closed when the request finishes, regardless of success or failure.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
