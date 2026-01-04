"""
Tests for schema validation.
"""

import pytest
from jobhunter.schema import validate_posting, validate_posting_strict


class TestValidatePosting:
    """Test basic validation function."""

    def test_valid_posting_minimal(self, valid_job_posting):
        """Valid posting should have no errors."""
        errors = validate_posting(valid_job_posting)
        assert errors == []

    def test_missing_required_field(self):
        """Missing required field should error."""
        data = {"company": "acme"}  # Missing title
        errors = validate_posting(data)
        assert len(errors) > 0
        assert any("title" in err.lower() for err in errors)

    def test_empty_string_field(self):
        """Empty required field should error."""
        data = {"company": "acme", "title": "   "}
        errors = validate_posting(data)
        assert len(errors) > 0

    def test_invalid_url(self):
        """Invalid URL format should error."""
        data = {
            "company": "acme",
            "title": "engineer",
            "url": "not-a-url"
        }
        errors = validate_posting(data)
        assert any("url" in err.lower() for err in errors)

    def test_valid_url_formats(self):
        """Valid URL formats should pass."""
        valid_urls = [
            "https://boards.greenhouse.io/acme/jobs/123",
            "http://jobs.lever.co/company/job",
        ]
        for url in valid_urls:
            data = {
                "company": "acme",
                "title": "engineer",
                "url": url
            }
            errors = validate_posting(data)
            assert not any("url" in err.lower() for err in errors)

    def test_title_too_short(self):
        """Title that's too short should warn."""
        data = {
            "company": "acme",
            "title": "AB"  # Only 2 chars
        }
        errors = validate_posting(data)
        assert any("title" in err.lower() and "length" in err.lower() for err in errors)

    def test_title_too_long(self):
        """Title that's too long should warn."""
        data = {
            "company": "acme",
            "title": "A" * 250  # Way too long
        }
        errors = validate_posting(data)
        assert any("title" in err.lower() and "length" in err.lower() for err in errors)

    def test_company_too_short(self):
        """Company name too short should warn."""
        data = {
            "company": "A",  # Only 1 char
            "title": "engineer"
        }
        errors = validate_posting(data)
        assert any("company" in err.lower() and "length" in err.lower() for err in errors)

    def test_optional_fields(self):
        """Optional fields can be omitted."""
        data = {
            "company": "acme",
            "title": "engineer",
            # No location, source, etc.
        }
        errors = validate_posting(data)
        # Should only check required fields
        assert all("location" not in err.lower() for err in errors)


class TestValidatePostingStrict:
    """Test strict validation function."""

    def test_valid_posting_strict(self, valid_job_posting):
        """Valid posting passes strict validation."""
        is_valid, errors = validate_posting_strict(valid_job_posting)
        assert is_valid
        assert errors == []

    def test_unknown_source_strict(self):
        """Unknown source platform should fail strict validation."""
        data = {
            "company": "acme",
            "title": "engineer",
            "source": "unknown_platform"
        }
        is_valid, errors = validate_posting_strict(data)
        assert not is_valid
        assert any("source" in err.lower() for err in errors)

    def test_known_sources_strict(self):
        """Known ATS platforms should pass."""
        known_sources = ["greenhouse", "lever", "ashby", "workable"]

        for source in known_sources:
            data = {
                "company": "acme",
                "title": "engineer",
                "source": source
            }
            is_valid, errors = validate_posting_strict(data)
            assert is_valid, f"Source {source} should be valid"
