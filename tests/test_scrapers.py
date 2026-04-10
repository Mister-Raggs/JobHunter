"""Integration tests for scrapers — hits live APIs, requires network.

Run with:
    pytest tests/test_scrapers.py -v

Skip slow tests:
    pytest tests/test_scrapers.py -v -m "not slow"
"""

import pytest

from jobhunter.scrapers.apple import AppleScraper
from jobhunter.scrapers.ashby import AshbyScraper
from jobhunter.scrapers.eightfold import EightfoldScraper
from jobhunter.scrapers.greenhouse import GreenhouseScraper
from jobhunter.scrapers.lever import LeverScraper
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


# --- Apple ---

def test_apple_us_only():
    """All returned jobs should be US locations (not international retail)."""
    jobs = AppleScraper().fetch_jobs(max_pages=1)
    _assert_valid_jobs(jobs)
    for job in jobs:
        assert job["url"].startswith("https://jobs.apple.com"), f"Unexpected URL: {job['url']}"


def test_apple_no_international_retail(tmp_path):
    """Page 1 should not be dominated by international Specialist retail roles."""
    jobs = AppleScraper().fetch_jobs(max_pages=1)
    # With US filter, titles like 'IN-Specialist' or 'TR-Specialist' should not appear
    intl_retail = [j for j in jobs if j["title"].startswith(("IN-", "TR-", "UAE-", "DE-", "FR-", "JP-"))]
    assert len(intl_retail) == 0, f"International retail jobs leaked through: {[j['title'] for j in intl_retail]}"


def test_apple_page_level_early_exit():
    """Page-level early exit: known page should return 0, not break mid-page."""
    scraper = AppleScraper()
    first_page = scraper.fetch_jobs(max_pages=1)
    known_ids = {j["external_id"] for j in first_page}
    # Second fetch with all page-1 IDs known should return 0
    second = scraper.fetch_jobs(max_pages=1, known_ids=known_ids)
    assert len(second) == 0


# --- Lever ---

def test_lever_zilliz():
    jobs = LeverScraper().fetch_jobs("zilliz")
    _assert_valid_jobs(jobs)


def test_lever_early_exit():
    """With all jobs marked known, fetch should return 0."""
    scraper = LeverScraper()
    jobs = scraper.fetch_jobs("zilliz")
    known_ids = {j["external_id"] for j in jobs}
    second = scraper.fetch_jobs("zilliz", known_ids=known_ids)
    assert len(second) == 0


# --- New companies ---

def test_greenhouse_anthropic():
    jobs = GreenhouseScraper().fetch_jobs("anthropic")
    _assert_valid_jobs(jobs, min_count=10)


def test_greenhouse_xai():
    jobs = GreenhouseScraper().fetch_jobs("xai")
    _assert_valid_jobs(jobs, min_count=5)


def test_greenhouse_singlestore():
    jobs = GreenhouseScraper().fetch_jobs("singlestore")
    _assert_valid_jobs(jobs)


def test_ashby_weaviate():
    jobs = AshbyScraper().fetch_jobs("weaviate")
    _assert_valid_jobs(jobs)