"""
Pytest configuration and shared fixtures.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_greenhouse_html() -> str:
    """Sample Greenhouse job page HTML."""
    return """
    <html>
    <head><title>Software Engineer at Acme Corp</title></head>
    <body>
        <div class="app-wrapper">
            <h1>Software Engineer</h1>
            <div class="location">San Francisco, CA</div>
            <div class="content">
                <p>We are looking for a talented software engineer...</p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_lever_html() -> str:
    """Sample Lever job page HTML."""
    return """
    <html>
    <head><title>Product Manager - Acme</title></head>
    <body>
        <div class="posting">
            <h2>Product Manager</h2>
            <div class="posting-categories">
                <div class="location">Remote</div>
            </div>
            <div class="content">
                <p>Join our product team...</p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def valid_job_posting() -> Dict[str, Any]:
    """Valid job posting data."""
    return {
        "company": "acme corp",
        "title": "software engineer",
        "location": "san francisco, ca",
        "url": "https://boards.greenhouse.io/acme/jobs/12345",
        "source": "greenhouse",
        "source_id": "12345",
    }


@pytest.fixture
def invalid_job_posting() -> Dict[str, Any]:
    """Invalid job posting (missing required fields)."""
    return {
        "company": "acme",
        # Missing title
        "location": "remote",
    }


@pytest.fixture
def temp_store_file(tmp_path) -> Path:
    """Create a temporary store file."""
    store_file = tmp_path / "test_store.json"
    store_file.write_text(json.dumps({"roles": {}}))
    return store_file


@pytest.fixture
def populated_store(tmp_path) -> Path:
    """Create a store with sample data."""
    store_file = tmp_path / "test_store.json"
    data = {
        "roles": {
            "acme|greenhouse:12345": {
                "current": {
                    "company": "acme",
                    "title": "software engineer",
                    "location": "remote",
                    "url": "https://boards.greenhouse.io/acme/jobs/12345",
                    "source": "greenhouse",
                    "source_id": "12345",
                }
            },
            "beta|lever:67890": {
                "current": {
                    "company": "beta",
                    "title": "product manager",
                    "location": "new york, ny",
                    "url": "https://jobs.lever.co/beta/67890",
                    "source": "lever",
                    "source_id": "67890",
                }
            }
        }
    }
    store_file.write_text(json.dumps(data, indent=2))
    return store_file
