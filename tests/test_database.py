"""
Tests for database.py - SQLite database operations.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.exc import IntegrityError

from jobhunter.database import Job, init_database, get_session


class TestDatabaseInit:
    """Test database initialization."""

    def test_init_creates_database_file(self, tmp_path):
        """Test that init_database creates the database file."""
        db_path = tmp_path / "test.db"
        assert not db_path.exists()

        init_database(db_path)

        assert db_path.exists()

    def test_init_creates_tables(self, tmp_path):
        """Test that init_database creates the jobs table."""
        db_path = tmp_path / "test.db"
        init_database(db_path)

        session = get_session(db_path)
        # Should not raise error if table exists
        result = session.query(Job).count()
        assert result == 0
        session.close()

    def test_init_creates_parent_directories(self, tmp_path):
        """Test that init_database creates parent directories if missing."""
        db_path = tmp_path / "nested" / "dir" / "test.db"
        assert not db_path.parent.exists()

        init_database(db_path)

        assert db_path.exists()
        assert db_path.parent.exists()


class TestJobCRUD:
    """Test CRUD operations on Job model."""

    @pytest.fixture
    def db_session(self, tmp_path):
        """Create a temporary database and return a session."""
        db_path = tmp_path / "test.db"
        init_database(db_path)
        session = get_session(db_path)
        yield session
        session.close()

    @pytest.fixture
    def sample_job(self):
        """Return sample job data."""
        return Job(
            role_id="acme|greenhouse:12345",
            company="acme",
            title="software engineer",
            location="san francisco, ca",
            url="https://boards.greenhouse.io/acme/jobs/12345",
            source="greenhouse",
            source_id="12345",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_create_job(self, db_session, sample_job):
        """Test creating a new job."""
        db_session.add(sample_job)
        db_session.commit()

        result = db_session.query(Job).filter_by(role_id="acme|greenhouse:12345").first()
        assert result is not None
        assert result.company == "acme"
        assert result.title == "software engineer"

    def test_create_job_without_required_fields_fails(self, db_session):
        """Test that creating a job without required fields fails."""
        job = Job(role_id="test|greenhouse:99999")
        db_session.add(job)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_read_job_by_role_id(self, db_session, sample_job):
        """Test querying a job by role_id."""
        db_session.add(sample_job)
        db_session.commit()

        result = db_session.query(Job).filter_by(role_id="acme|greenhouse:12345").first()
        assert result.role_id == "acme|greenhouse:12345"

    def test_read_all_jobs(self, db_session, sample_job):
        """Test querying all jobs."""
        # Add multiple jobs
        job2 = Job(
            role_id="beta|lever:67890",
            company="beta",
            title="product manager",
            location="remote",
            url="https://jobs.lever.co/beta/67890",
            source="lever",
            source_id="67890",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db_session.add(sample_job)
        db_session.add(job2)
        db_session.commit()

        results = db_session.query(Job).all()
        assert len(results) == 2

    def test_read_jobs_by_company(self, db_session, sample_job):
        """Test querying jobs by company."""
        job2 = Job(
            role_id="acme|lever:11111",
            company="acme",
            title="data scientist",
            location="new york, ny",
            url="https://jobs.lever.co/acme/11111",
            source="lever",
            source_id="11111",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db_session.add(sample_job)
        db_session.add(job2)
        db_session.commit()

        results = db_session.query(Job).filter_by(company="acme").all()
        assert len(results) == 2

    def test_read_jobs_by_source(self, db_session):
        """Test querying jobs by source platform."""
        job1 = Job(
            role_id="alpha|greenhouse:1",
            company="alpha",
            title="engineer",
            location="remote",
            url="https://boards.greenhouse.io/alpha/jobs/1",
            source="greenhouse",
            source_id="1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        job2 = Job(
            role_id="beta|lever:2",
            company="beta",
            title="engineer",
            location="remote",
            url="https://jobs.lever.co/beta/2",
            source="lever",
            source_id="2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db_session.add(job1)
        db_session.add(job2)
        db_session.commit()

        greenhouse_jobs = db_session.query(Job).filter_by(source="greenhouse").all()
        lever_jobs = db_session.query(Job).filter_by(source="lever").all()

        assert len(greenhouse_jobs) == 1
        assert len(lever_jobs) == 1

    def test_update_job(self, db_session, sample_job):
        """Test updating a job's fields."""
        db_session.add(sample_job)
        db_session.commit()

        # Update job
        job = db_session.query(Job).filter_by(role_id="acme|greenhouse:12345").first()
        job.title = "senior software engineer"
        job.location = "remote"
        db_session.commit()

        # Verify update
        updated_job = db_session.query(Job).filter_by(role_id="acme|greenhouse:12345").first()
        assert updated_job.title == "senior software engineer"
        assert updated_job.location == "remote"

    def test_delete_job(self, db_session, sample_job):
        """Test deleting a job."""
        db_session.add(sample_job)
        db_session.commit()

        assert db_session.query(Job).count() == 1

        # Delete job
        job = db_session.query(Job).filter_by(role_id="acme|greenhouse:12345").first()
        db_session.delete(job)
        db_session.commit()

        assert db_session.query(Job).count() == 0

    def test_duplicate_role_id_fails(self, db_session, sample_job):
        """Test that duplicate role_id raises an error."""
        db_session.add(sample_job)
        db_session.commit()

        # Try to add duplicate
        duplicate = Job(
            role_id="acme|greenhouse:12345",  # Same role_id
            company="different",
            title="different title",
            location="different location",
            url="https://different.com",
            source="greenhouse",
            source_id="12345",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(duplicate)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestJobTimestamps:
    """Test timestamp handling."""

    @pytest.fixture
    def db_session(self, tmp_path):
        """Create a temporary database and return a session."""
        db_path = tmp_path / "test.db"
        init_database(db_path)
        session = get_session(db_path)
        yield session
        session.close()

    def test_created_at_set_on_insert(self, db_session):
        """Test that created_at is set when job is created."""
        before = datetime.now()

        job = Job(
            role_id="test|greenhouse:1",
            company="test",
            title="engineer",
            location="remote",
            url="https://test.com",
            source="greenhouse",
            source_id="1",
        )
        db_session.add(job)
        db_session.commit()

        after = datetime.now()

        saved_job = db_session.query(Job).filter_by(role_id="test|greenhouse:1").first()
        assert saved_job.created_at is not None
        assert before <= saved_job.created_at <= after

    def test_updated_at_set_on_insert(self, db_session):
        """Test that updated_at is set when job is created."""
        job = Job(
            role_id="test|greenhouse:1",
            company="test",
            title="engineer",
            location="remote",
            url="https://test.com",
            source="greenhouse",
            source_id="1",
        )
        db_session.add(job)
        db_session.commit()

        saved_job = db_session.query(Job).filter_by(role_id="test|greenhouse:1").first()
        assert saved_job.updated_at is not None
        # Timestamps should be within 1 second of each other (microsecond precision varies)
        assert abs((saved_job.created_at - saved_job.updated_at).total_seconds()) < 1

    def test_query_jobs_by_date_range(self, db_session):
        """Test querying jobs within a date range."""
        now = datetime.now()
        old_date = now - timedelta(days=10)

        old_job = Job(
            role_id="old|greenhouse:1",
            company="old",
            title="engineer",
            location="remote",
            url="https://old.com",
            source="greenhouse",
            source_id="1",
            created_at=old_date,
            updated_at=old_date,
        )
        new_job = Job(
            role_id="new|greenhouse:2",
            company="new",
            title="engineer",
            location="remote",
            url="https://new.com",
            source="greenhouse",
            source_id="2",
            created_at=now,
            updated_at=now,
        )

        db_session.add(old_job)
        db_session.add(new_job)
        db_session.commit()

        # Query jobs created in last 5 days
        cutoff = now - timedelta(days=5)
        recent_jobs = db_session.query(Job).filter(Job.created_at >= cutoff).all()

        assert len(recent_jobs) == 1
        assert recent_jobs[0].role_id == "new|greenhouse:2"
