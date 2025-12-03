"""Database initialization script."""
from backend.config.database import init_db, engine
from backend.database.base import Base
from backend.models import User, Session, Quote, QuoteItem


def create_tables():
    """Create all database tables."""
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    create_tables()

