"""Database configuration and connection management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from backend.config.settings import FLASK_ENV, FLASK_DEBUG

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///osc_finops.db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "0") == "1"  # SQL logging

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite with Flask
        poolclass=StaticPool,  # SQLite doesn't support connection pooling
        echo=DATABASE_ECHO
    )
else:
    # PostgreSQL/other database configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        echo=DATABASE_ECHO
    )

# Session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))


def get_db():
    """
    Get database session.
    Use as dependency injection in route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    from backend.database.base import Base
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections."""
    SessionLocal.remove()

