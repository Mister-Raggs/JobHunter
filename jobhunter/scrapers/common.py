"""Shared utilities for all ATS scrapers."""

import requests
from ..logger import get_logger
from ..retry import exponential_backoff

logger = get_logger()


@exponential_backoff(max_retries=3, base_delay=1.0, exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError))
def _fetch_with_retry(url: str):
    """Fetch URL with automatic retry on transient errors."""
    return requests.get(url, timeout=15)


def fetch_with_error_handling(url: str, platform: str):
    """Fetch URL with standardized error handling and logging.

    Args:
        url: The URL to fetch
        platform: The platform name for logging (e.g., 'greenhouse', 'lever')

    Returns:
        Response object on success

    Raises:
        ValueError: On any HTTP error, timeout, or request failure
    """
    logger.record_scrape_attempt(platform)
    try:
        resp = _fetch_with_retry(url)
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.record_scrape_failure(platform, f"HTTPError_{status}")
        if status == 404:
            logger.warning(f"{platform.capitalize()} URL not found", url=url, status=404)
            raise ValueError(f"{platform.capitalize()} URL not found (404): {url}")
        logger.error(f"{platform.capitalize()} request failed", url=url, status=status)
        raise ValueError(f"{platform.capitalize()} request failed ({status}): {url}")
    except requests.exceptions.Timeout:
        logger.record_scrape_failure(platform, "Timeout")
        logger.warning(f"{platform.capitalize()} request timed out", url=url)
        raise ValueError(f"{platform.capitalize()} request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.record_scrape_failure(platform, "RequestException")
        logger.error(f"{platform.capitalize()} request error", url=url, error=str(e))
        raise ValueError(f"{platform.capitalize()} request error: {e}")


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Deduplicate URLs while preserving order."""
    seen = set()
    result = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
