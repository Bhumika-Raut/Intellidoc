from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base. Tables stay dialect-portable for a later PostgreSQL move."""


def _engine_kwargs(url: str) -> dict:
    # SQLite needs check_same_thread=False for FastAPI's thread pool.
    # PostgreSQL URLs should omit this flag.
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import conversation, document, query_log  # noqa: F401

    Base.metadata.create_all(bind=engine)
