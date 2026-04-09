"""SQLite database for tracking job postings."""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

DB_PATH = Path(__file__).parent.parent / "data" / "jobs.db"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, default="")
    url = Column(String, nullable=False)
    posted_at = Column(String, default="")
    discovered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    notified = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("company", "external_id", name="uq_company_job"),
    )


def _get_session(db_path: Path | None = None):
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add_jobs(jobs: list[dict], company: str, db_path: Path | None = None) -> list[dict]:
    """Insert new jobs into the database. Returns only the newly added ones."""
    session = _get_session(db_path)
    new_jobs = []
    try:
        for job in jobs:
            exists = (
                session.query(Job)
                .filter_by(company=company, external_id=str(job["external_id"]))
                .first()
            )
            if not exists:
                session.add(
                    Job(
                        company=company,
                        external_id=str(job["external_id"]),
                        title=job["title"],
                        location=job.get("location", ""),
                        url=job["url"],
                        posted_at=job.get("posted_at", ""),
                    )
                )
                new_jobs.append(job)
        session.commit()
    finally:
        session.close()
    return new_jobs


def get_all_jobs(company: str | None = None, db_path: Path | None = None) -> list[Job]:
    """Fetch tracked jobs, optionally filtered by company key."""
    session = _get_session(db_path)
    try:
        q = session.query(Job)
        if company:
            q = q.filter_by(company=company)
        return q.order_by(Job.discovered_at.desc()).all()
    finally:
        session.close()


def job_count(company: str | None = None, db_path: Path | None = None) -> int:
    session = _get_session(db_path)
    try:
        q = session.query(Job)
        if company:
            q = q.filter_by(company=company)
        return q.count()
    finally:
        session.close()


def get_known_ids(company: str, db_path: Path | None = None) -> set[str]:
    """Return the set of external_ids already stored for a company."""
    session = _get_session(db_path)
    try:
        rows = session.query(Job.external_id).filter_by(company=company).all()
        return {r[0] for r in rows}
    finally:
        session.close()


def get_unnotified_jobs(db_path: Path | None = None) -> list[Job]:
    """Return all jobs that have not yet been emailed."""
    session = _get_session(db_path)
    try:
        return session.query(Job).filter_by(notified=False).order_by(Job.discovered_at.desc()).all()
    finally:
        session.close()


def get_notified_jobs(db_path: Path | None = None) -> list[Job]:
    """Return all jobs that have already been emailed, ordered newest first."""
    session = _get_session(db_path)
    try:
        return session.query(Job).filter_by(notified=True).order_by(Job.discovered_at.desc()).all()
    finally:
        session.close()


def mark_notified(job_ids: list[int], db_path: Path | None = None) -> None:
    """Mark jobs as notified by their primary key IDs."""
    if not job_ids:
        return
    session = _get_session(db_path)
    try:
        session.query(Job).filter(Job.id.in_(job_ids)).update(
            {Job.notified: True}, synchronize_session=False
        )
        session.commit()
    finally:
        session.close()
