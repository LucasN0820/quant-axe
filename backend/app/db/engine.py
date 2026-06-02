"""SQLAlchemy engine and session lifecycle helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.services.config import POSTGRES_DSN


def sqlalchemy_database_url(dsn: str = POSTGRES_DSN) -> str:
    """Select SQLAlchemy's psycopg 3 dialect for legacy PostgreSQL DSNs."""

    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    return dsn


engine: Engine = create_engine(
    sqlalchemy_database_url(),
    pool_pre_ping=True,
)
SESSION_FACTORY = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional ORM session."""

    with SESSION_FACTORY.begin() as session:  # pylint: disable=no-member
        yield session
