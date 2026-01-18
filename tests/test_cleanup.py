"""Tests for cleanup functionality."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from jobhunter.cleanup import cleanup_stale_jobs
from jobhunter.database import Job, init_database, get_session


class TestCleanup:
    """Test stale job cleanup functionality."""

    def test_cleanup_removes_stale_jobs(self):
        """Verify that jobs older than threshold are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"  # Compatibility - derives db path from this
            db_path = Path(tmpdir) / "jobs.db"

            # Initialize database and add test jobs
            init_database(db_path)
            session = get_session(db_path)

            now = datetime.now()
            old_date = now - timedelta(days=10)  # 10 days old
            new_date = now - timedelta(days=2)   # 2 days old

            old_job = Job(
                role_id="company1|source:1",
                company="company1",
                title="old job",
                location="remote",
                url="https://example.com/1",
                source="source",
                source_id="1",
                created_at=old_date,
                updated_at=old_date,
            )
            new_job = Job(
                role_id="company2|source:2",
                company="company2",
                title="new job",
                location="remote",
                url="https://example.com/2",
                source="source",
                source_id="2",
                created_at=new_date,
                updated_at=new_date,
            )

            session.add(old_job)
            session.add(new_job)
            session.commit()
            session.close()

            # Run cleanup
            before, after = cleanup_stale_jobs(store_path, days=7)

            # Verify results
            assert before == 2
            assert after == 1

            # Verify the old job was removed and new one remains
            session = get_session(db_path)
            remaining_jobs = session.query(Job).all()
            assert len(remaining_jobs) == 1
            assert remaining_jobs[0].role_id == "company2|source:2"
            session.close()

    def test_cleanup_handles_missing_store(self):
        """Verify cleanup handles missing database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "nonexistent.json"
            # Database doesn't exist yet

            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 0
            assert after == 0

    def test_cleanup_handles_empty_database(self):
        """Verify cleanup handles empty database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"
            db_path = Path(tmpdir) / "jobs.db"

            # Initialize empty database
            init_database(db_path)

            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 0
            assert after == 0

    def test_cleanup_preserves_new_jobs(self):
        """Verify that recently created jobs are always preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"
            db_path = Path(tmpdir) / "jobs.db"

            # Initialize database and add recent jobs
            init_database(db_path)
            session = get_session(db_path)

            now = datetime.now()

            for i in range(5):
                job = Job(
                    role_id=f"company{i}|source:{i}",
                    company=f"company{i}",
                    title=f"job {i}",
                    location="remote",
                    url=f"https://example.com/{i}",
                    source="source",
                    source_id=str(i),
                    created_at=now,
                    updated_at=now,
                )
                session.add(job)

            session.commit()
            session.close()

            # Run cleanup
            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 5
            assert after == 5  # All jobs should be preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
