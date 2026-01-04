from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

REQUIRED_STR_FIELDS = ["company", "title"]
OPTIONAL_STR_FIELDS = [
    "location",
    "source",
    "source_id",
    "url",
    "description",
]

# Data quality bounds
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_COMPANY_LENGTH = 2
MAX_COMPANY_LENGTH = 100
MAX_LOCATION_LENGTH = 100


def _is_non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _valid_url(v: str) -> bool:
    try:
        p = urlparse(v)
        # Require HTTPS for job boards (more secure)
        return bool(p.scheme in ('http', 'https') and p.netloc)
    except Exception:
        return False


def _is_suspicious_length(text: str, min_len: int, max_len: int) -> bool:
    """Check if text length is outside reasonable bounds."""
    length = len(text.strip())
    return length < min_len or length > max_len


def validate_posting(data: Dict[str, Any]) -> List[str]:
    """
    Returns a list of validation error messages. Empty list means valid.
    Enhanced validation with data quality checks.
    """
    errors: List[str] = []

    # Required string fields
    for f in REQUIRED_STR_FIELDS:
        if f not in data:
            errors.append(f"Missing required field: {f}")
        elif not _is_non_empty_str(data[f]):
            errors.append(f"Field '{f}' must be a non-empty string")

    # Optional strings: if present, must be strings (non-empty allowed to fail)
    for f in OPTIONAL_STR_FIELDS:
        if f in data and not isinstance(data[f], str):
            errors.append(f"Field '{f}' must be a string if provided")

    # URL validation
    if isinstance(data.get("url"), str) and data["url"].strip():
        if not _valid_url(data["url"]):
            errors.append("Field 'url' must be a valid absolute URL (scheme + host)")

    # Data quality checks
    if "title" in data and isinstance(data["title"], str):
        if _is_suspicious_length(data["title"], MIN_TITLE_LENGTH, MAX_TITLE_LENGTH):
            errors.append(
                f"Field 'title' length ({len(data['title'])}) outside reasonable bounds "
                f"({MIN_TITLE_LENGTH}-{MAX_TITLE_LENGTH})"
            )

    if "company" in data and isinstance(data["company"], str):
        if _is_suspicious_length(data["company"], MIN_COMPANY_LENGTH, MAX_COMPANY_LENGTH):
            errors.append(
                f"Field 'company' length ({len(data['company'])}) outside reasonable bounds "
                f"({MIN_COMPANY_LENGTH}-{MAX_COMPANY_LENGTH})"
            )

    if "location" in data and isinstance(data["location"], str) and data["location"]:
        if len(data["location"]) > MAX_LOCATION_LENGTH:
            errors.append(
                f"Field 'location' too long ({len(data['location'])} > {MAX_LOCATION_LENGTH})"
            )

    # Either location OR remote indicator should exist
    has_location = data.get("location") and isinstance(data["location"], str) and data["location"].strip()
    if not has_location:
        # This is now a warning, not an error - some jobs might not specify location
        pass

    return errors


def validate_posting_strict(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Strict validation that returns (is_valid, errors).
    Use for critical data quality checks.
    """
    errors = validate_posting(data)

    # Additional strict checks
    if "source" in data and data["source"] not in [
        "greenhouse", "lever", "ashby", "workable", "custom",
        "smartrecruiters", "workday", "jazzhr", "breezyhr", "bamboohr"
    ]:
        errors.append(f"Unknown source: {data.get('source')}")

    return (len(errors) == 0, errors)
