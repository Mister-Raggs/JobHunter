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


def _is_non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _valid_url(v: str) -> bool:
    try:
        p = urlparse(v)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False


def validate_posting(data: Dict[str, Any]) -> List[str]:
    """
    Returns a list of validation error messages. Empty list means valid.
    Minimal, dependency-free checks for the MVP.
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

    # URL shape if present
    if isinstance(data.get("url"), str) and data["url"].strip():
        if not _valid_url(data["url"]):
            errors.append("Field 'url' must be a valid absolute URL (scheme + host)")

    return errors
