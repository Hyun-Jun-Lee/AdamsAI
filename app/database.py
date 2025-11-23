"""
Database connection and session management.
Provides functional interfaces for database access.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.config import get_settings

# Create declarative base for models
Base = declarative_base()

# Global engine and session maker
_engine: Engine = None
_SessionLocal: sessionmaker = None


def get_engine() -> Engine:
    """
    Get or create database engine (singleton pattern).

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
            echo=False,  # Set to True for SQL query logging
        )

        # Enable foreign key constraints for SQLite
        if "sqlite" in settings.database_url:
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_maker() -> sessionmaker:
    """
    Get or create session maker (singleton pattern).

    Returns:
        sessionmaker: SQLAlchemy session maker
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for FastAPI dependency injection.

    Yields:
        Session: Database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get database session as context manager for standalone operations.

    Yields:
        Session: Database session

    Example:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should be called once at application startup.
    """
    from app.models import Video, Audio, Transcript, Summary, PromptTemplate  # Import here to avoid circular dependency

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def drop_db() -> None:
    """
    Drop all database tables.
    WARNING: This will delete all data! Use only for testing/development.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")
