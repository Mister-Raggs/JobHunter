"""
Database schema and connection management.

Uses SQLite with SQLAlchemy for job storage.
"""

from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Job(Base):
    """Job posting model."""

    __tablename__ = "jobs"

    role_id = Column(String, primary_key=True)  # company|source:source_id
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)  # greenhouse, lever, ashby, workable
    source_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


def init_database(db_path: Path) -> None:
    """
    Initialize database and create tables.

    Args:
        db_path: Path to SQLite database file
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)


def get_session(db_path: Path):
    """
    Get database session.

    Args:
        db_path: Path to SQLite database file

    Returns:
        SQLAlchemy session
    """
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    return Session()
