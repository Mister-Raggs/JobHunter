"""Tests for cleanup functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from jobhunter.cleanup import cleanup_stale_jobs


class TestCleanup:
    """Test stale job cleanup functionality."""

    def test_cleanup_removes_stale_jobs(self):
        """Verify that jobs older than threshold are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"

            # Create store with jobs at different ages
            now = datetime.now()
            old_date = (now - timedelta(days=10)).isoformat()  # 10 days old
            new_date = (now - timedelta(days=2)).isoformat()   # 2 days old

            store = {
                "roles": {
                    "company1|source:1": {
                        "current": {
                            "company": "company1",
                            "title": "old job",
                            "location": "remote",
                            "url": "https://example.com/1",
                            "source": "source",
                            "source_id": "1",
                            "created_at": old_date,
                        }
                    },
                    "company2|source:2": {
                        "current": {
                            "company": "company2",
                            "title": "new job",
                            "location": "remote",
                            "url": "https://example.com/2",
                            "source": "source",
                            "source_id": "2",
                            "created_at": new_date,
                        }
                    },
                }
            }

            with open(store_path, "w") as f:
                json.dump(store, f)

            # Run cleanup
            before, after = cleanup_stale_jobs(store_path, days=7)

            # Verify results
            assert before == 2
            assert after == 1

            # Verify the old job was removed and new one remains
            with open(store_path, "r") as f:
                cleaned_store = json.load(f)

            assert len(cleaned_store["roles"]) == 1
            assert "company2|source:2" in cleaned_store["roles"]
            assert "company1|source:1" not in cleaned_store["roles"]

    def test_cleanup_initializes_missing_timestamps(self):
        """Verify that jobs without created_at get initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"

            # Create store with jobs missing created_at
            store = {
                "roles": {
                    "company1|source:1": {
                        "current": {
                            "company": "company1",
                            "title": "job without timestamp",
                            "location": "remote",
                            "url": "https://example.com/1",
                            "source": "source",
                            "source_id": "1",
                        }
                    },
                }
            }

            with open(store_path, "w") as f:
                json.dump(store, f)

            # Run cleanup
            before, after = cleanup_stale_jobs(store_path, days=7)

            # Verify timestamp was added
            with open(store_path, "r") as f:
                cleaned_store = json.load(f)

            assert "created_at" in cleaned_store["roles"]["company1|source:1"]["current"]
            assert before == after  # No jobs removed

    def test_cleanup_handles_missing_store(self):
        """Verify cleanup handles missing store file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "nonexistent.json"

            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 0
            assert after == 0

    def test_cleanup_handles_empty_store(self):
        """Verify cleanup handles empty store file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"
            store_path.write_text("")

            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 0
            assert after == 0

    def test_cleanup_preserves_new_jobs(self):
        """Verify that recently created jobs are always preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"

            # Create store with jobs at current time
            now = datetime.now().isoformat()

            store = {
                "roles": {
                    f"company{i}|source:{i}": {
                        "current": {
                            "company": f"company{i}",
                            "title": f"job {i}",
                            "location": "remote",
                            "url": f"https://example.com/{i}",
                            "source": "source",
                            "source_id": str(i),
                            "created_at": now,
                        }
                    }
                    for i in range(5)
                }
            }

            with open(store_path, "w") as f:
                json.dump(store, f)

            # Run cleanup
            before, after = cleanup_stale_jobs(store_path, days=7)

            assert before == 5
            assert after == 5  # All jobs should be preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
