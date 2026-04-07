"""Integration tests for scrapers — hits live APIs, requires network.

Run with:
    pytest tests/test_scrapers.py -v

Skip slow tests:
    pytest tests/test_scrapers.py -v -m "not slow"
"""

import pytest

from jobhunter.scrapers.ashby import AshbyScraper
from jobhunter.scrapers.eightfold import EightfoldScraper
from jobhunter.scrapers.greenhouse import GreenhouseScraper
from jobhunter.scrapers.salesforce import SalesforceScraper
from jobhunter.scrapers.uber import UberScraper


REQUIRED_FIELDS = {"external_id", "title", "url"}


def _assert_valid_jobs(jobs: list[dict], min_count: int = 1) -> None:
    assert len(jobs) >= min_count, f"Expected at least {min_count} job(s), got {len(jobs)}"
    for job in jobs:
        for field in REQUIRED_FIELDS:
            assert field in job, f"Missing field '{field}' in job: {job}"
            assert job[field], f"Empty field '{field}' in job: {job}"
        assert job["url"].startswith("http"), f"Invalid URL: {job['url']}"


# --- Greenhouse ---

def test_greenhouse_doordash():
    jobs = GreenhouseScraper().fetch_jobs("doordashusa")
    _assert_valid_jobs(jobs)


def test_greenhouse_nuro():
    jobs = GreenhouseScraper().fetch_jobs("nuro")
    _assert_valid_jobs(jobs)


def test_greenhouse_coreweave():
    jobs = GreenhouseScraper().fetch_jobs("coreweave")
    _assert_valid_jobs(jobs)


# --- Ashby ---

def test_ashby_baseten():
    jobs = AshbyScraper().fetch_jobs("baseten")
    _assert_valid_jobs(jobs)


def test_ashby_braintrust():
    jobs = AshbyScraper().fetch_jobs("braintrust")
    _assert_valid_jobs(jobs)


# --- Eightfold ---

@pytest.mark.slow
def test_eightfold_netflix():
    jobs = EightfoldScraper().fetch_jobs("netflix")
    _assert_valid_jobs(jobs)


@pytest.mark.slow
def test_eightfold_early_exit():
    """With all page-1 jobs marked known, second fetch should return 0."""
    scraper = EightfoldScraper()
    first_page = scraper.fetch_jobs("netflix", max_pages=1)
    known_ids = {j["external_id"] for j in first_page}
    second = scraper.fetch_jobs("netflix", max_pages=1, known_ids=known_ids)
    assert len(second) == 0, f"Expected 0 new jobs, got {len(second)}"


# --- Uber ---

def test_uber():
    jobs = UberScraper().fetch_jobs("uber")
    _assert_valid_jobs(jobs)


def test_uber_early_exit():
    """With all page-1 jobs marked known, second fetch should return 0."""
    scraper = UberScraper()
    first_page = scraper.fetch_jobs("uber", max_pages=1)
    known_ids = {j["external_id"] for j in first_page}
    second = scraper.fetch_jobs("uber", max_pages=1, known_ids=known_ids)
    assert len(second) == 0


# --- Salesforce ---

def test_salesforce():
    jobs = SalesforceScraper().fetch_jobs()
    _assert_valid_jobs(jobs)