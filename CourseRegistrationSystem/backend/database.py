"""
database.py
-----------
SQLAlchemy database configuration for the Course Registration System.

By default the app uses a local SQLite database so it runs out-of-the-box.
For production, set the DATABASE_URL environment variable to your Supabase
PostgreSQL connection string and the app will use that instead.

Example (Supabase):
    DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Read the database URL from the environment.
# Falls back to a local SQLite file so the project runs without any setup.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./course_registration.db")

# SQLite needs a special flag when used with FastAPI's threaded server.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL / Supabase. pool_pre_ping keeps cloud connections healthy.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory used to talk to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models inherit from.
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
