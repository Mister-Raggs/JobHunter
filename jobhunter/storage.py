"""
Storage layer for job postings using SQLite database.

This module provides a clean interface for job persistence using SQLAlchemy.
The JSON-based storage has been replaced with database operations.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from .database import Job, init_database, get_session
from .logger import get_logger

logger = get_logger()

# Default database path
DEFAULT_DB_PATH = Path("data/jobs.db")


def ensure_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Ensure database exists and is initialized."""
    if not db_path.exists():
        logger.info("Initializing new database", extra={"path": str(db_path)})
        init_database(db_path)


def get_job(role_id: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Get a single job by role_id.

    Args:
        role_id: Unique job identifier (company|source:source_id)
        db_path: Path to database file

    Returns:
        Job dict or None if not found
    """
    ensure_database(db_path)
    session = get_session(db_path)
    try:
        job = session.query(Job).filter_by(role_id=role_id).first()
        if job:
            return {
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "url": job.url,
                "source": job.source,
                "source_id": job.source_id,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            }
        return None
    finally:
        session.close()


def get_all_jobs(db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Get all jobs from database.

    Args:
        db_path: Path to database file

    Returns:
        List of job dicts
    """
    ensure_database(db_path)
    session = get_session(db_path)
    try:
        jobs = session.query(Job).all()
        return [
            {
                "role_id": job.role_id,
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "url": job.url,
                "source": job.source,
                "source_id": job.source_id,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            }
            for job in jobs
        ]
    finally:
        session.close()


def upsert_job(role_id: str, job_data: Dict[str, Any], db_path: Path = DEFAULT_DB_PATH) -> Dict[str, str]:
    """
    Insert or update a job in the database.

    Args:
        role_id: Unique job identifier
        job_data: Job fields (company, title, location, url, source, source_id)
        db_path: Path to database file

    Returns:
        Dict with 'status': 'new', 'updated', or 'no-change'
    """
    ensure_database(db_path)
    session = get_session(db_path)
    try:
        existing = session.query(Job).filter_by(role_id=role_id).first()

        if existing is None:
            # New job
            job = Job(
                role_id=role_id,
                company=job_data["company"],
                title=job_data["title"],
                location=job_data["location"],
                url=job_data["url"],
                source=job_data["source"],
                source_id=job_data["source_id"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(job)
            session.commit()
            logger.debug("Inserted new job", extra={"role_id": role_id})
            return {"status": "new"}

        # Check if anything changed
        changed = False
        for field in ["company", "title", "location", "url", "source", "source_id"]:
            if getattr(existing, field) != job_data.get(field):
                changed = True
                setattr(existing, field, job_data[field])

        if changed:
            existing.updated_at = datetime.now()
            session.commit()
            logger.debug("Updated existing job", extra={"role_id": role_id})
            return {"status": "updated"}

        logger.debug("Job unchanged", extra={"role_id": role_id})
        return {"status": "no-change"}

    except Exception as e:
        session.rollback()
        logger.error("Failed to upsert job", extra={"role_id": role_id, "error": str(e)})
        raise
    finally:
        session.close()


def delete_stale_jobs(days: int = 7, db_path: Path = DEFAULT_DB_PATH) -> tuple[int, int]:
    """
    Delete jobs older than specified days.

    Args:
        days: Age threshold in days
        db_path: Path to database file

    Returns:
        Tuple of (jobs_before, jobs_after)
    """
    ensure_database(db_path)
    session = get_session(db_path)
    try:
        count_before = session.query(Job).count()
        cutoff = datetime.now() - timedelta(days=days)

        deleted = session.query(Job).filter(Job.created_at < cutoff).delete()
        session.commit()

        count_after = session.query(Job).count()

        if deleted > 0:
            logger.info(f"Deleted {deleted} stale jobs", extra={"days": days, "before": count_before, "after": count_after})

        return (count_before, count_after)

    except Exception as e:
        session.rollback()
        logger.error("Failed to delete stale jobs", extra={"error": str(e)})
        raise
    finally:
        session.close()

