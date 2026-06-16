"""
Mailwatcher database module - standalone for Docker build.
Provides Base and session utilities without depending on api package.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/opendataremoval")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    """Get a database session."""
    return SessionLocal()
