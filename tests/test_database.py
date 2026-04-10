"""Unit tests for database.py — uses a temp SQLite DB, no network."""

import pytest

from jobhunter.database import (
    add_jobs,
    get_known_ids,
    get_notified_jobs,
    get_unnotified_jobs,
    job_count,
    mark_notified,
)

SAMPLE_JOBS = [
    {"external_id": "1", "title": "Software Engineer", "location": "SF", "url": "https://example.com/1", "posted_at": "2026-01-01"},
    {"external_id": "2", "title": "ML Engineer", "location": "Remote", "url": "https://example.com/2", "posted_at": "2026-01-02"},
    {"external_id": "3", "title": "Data Scientist", "location": "NYC", "url": "https://example.com/3", "posted_at": "2026-01-03"},
]


@pytest.fixture
def db(tmp_path):
    """Temp DB path — fresh for each test."""
    return tmp_path / "test_jobs.db"


def test_add_jobs_inserts_new(db):
    new = add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    assert len(new) == 3


def test_add_jobs_deduplicates(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    new = add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    assert len(new) == 0


def test_add_jobs_returns_only_new(db):
    add_jobs(SAMPLE_JOBS[:2], "testco", db_path=db)
    new = add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    assert len(new) == 1
    assert new[0]["external_id"] == "3"


def test_add_jobs_isolated_by_company(db):
    add_jobs(SAMPLE_JOBS, "company_a", db_path=db)
    new = add_jobs(SAMPLE_JOBS, "company_b", db_path=db)
    assert len(new) == 3


def test_get_known_ids(db):
    add_jobs(SAMPLE_JOBS[:2], "testco", db_path=db)
    known = get_known_ids("testco", db_path=db)
    assert known == {"1", "2"}


def test_get_known_ids_empty(db):
    known = get_known_ids("testco", db_path=db)
    assert known == set()


def test_job_count(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    assert job_count("testco", db_path=db) == 3


def test_job_count_all_companies(db):
    add_jobs(SAMPLE_JOBS[:2], "company_a", db_path=db)
    add_jobs(SAMPLE_JOBS[2:], "company_b", db_path=db)
    assert job_count(db_path=db) == 3


def test_get_unnotified_jobs(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    unnotified = get_unnotified_jobs(db_path=db)
    assert len(unnotified) == 3


def test_mark_notified(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    unnotified = get_unnotified_jobs(db_path=db)
    ids = [j.id for j in unnotified]

    mark_notified(ids, db_path=db)

    assert get_unnotified_jobs(db_path=db) == []


def test_mark_notified_partial(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    unnotified = get_unnotified_jobs(db_path=db)

    mark_notified([unnotified[0].id], db_path=db)

    remaining = get_unnotified_jobs(db_path=db)
    assert len(remaining) == 2


def test_mark_notified_empty_list(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    mark_notified([], db_path=db)
    assert len(get_unnotified_jobs(db_path=db)) == 3


def test_get_notified_jobs_empty(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    assert get_notified_jobs(db_path=db) == []


def test_get_notified_jobs_after_mark(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    unnotified = get_unnotified_jobs(db_path=db)
    marked_id = unnotified[0].external_id
    mark_notified([unnotified[0].id], db_path=db)

    notified = get_notified_jobs(db_path=db)
    assert len(notified) == 1
    assert notified[0].external_id == marked_id


def test_get_notified_jobs_all(db):
    add_jobs(SAMPLE_JOBS, "testco", db_path=db)
    unnotified = get_unnotified_jobs(db_path=db)
    mark_notified([j.id for j in unnotified], db_path=db)

    assert len(get_notified_jobs(db_path=db)) == 3
    assert get_unnotified_jobs(db_path=db) == []