from typing import List, Optional
import os
import requests

from .logger import get_logger
from .retry import exponential_backoff

logger = get_logger()
GOOGLE_CUSTOM_SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def _date_restrict(days: Optional[int]) -> Optional[str]:
    """
    Convert days into Google Custom Search dateRestrict parameter.
    Supported formats: d[number], w[number], m[number], y[number]
    """
    if days is None:
        return None
    if days <= 1:
        return "d1"  # past day
    if days <= 7:
        return f"d{days}"  # past N days
    if days <= 30:
        return "m1"  # past month
    return "y1"  # past year


@exponential_backoff(max_retries=3, base_delay=1.0, exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError))
def _fetch_with_retry(url: str, params: dict):
    """Fetch with exponential backoff retry logic."""
    return requests.get(url, params=params, timeout=20)


def fetch_google_links(query: str, api_key: Optional[str] = None, cse_id: Optional[str] = None, num: int = 10, days: Optional[int] = None, site_search: Optional[str] = None) -> List[str]:
    """
    Fetch Google search results via Google Custom Search JSON API and return list of result links.

    Args:
        query: Search query string
        api_key: Google API key (or read from GOOGLE_API_KEY env var)
        cse_id: Custom Search Engine ID (or read from GOOGLE_CSE_ID env var)
        num: Number of results (max 10 per request; default 10)
        days: Optional recency filter in days
        site_search: Optional site to restrict results to (e.g., "greenhouse.io")

    Returns:
        List of result URLs from the search
    """
    key = api_key or os.getenv("GOOGLE_API_KEY")
    cx = cse_id or os.getenv("GOOGLE_CSE_ID")

    if not key:
        logger.error("Missing GOOGLE_API_KEY")
        raise ValueError("Missing GOOGLE_API_KEY. Set env var or pass api_key.")
    if not cx:
        logger.error("Missing GOOGLE_CSE_ID")
        raise ValueError("Missing GOOGLE_CSE_ID. Set env var or pass cse_id.")

    # Google Custom Search API max results per request is 10
    num = min(num, 10)

    params = {
        "key": key,
        "cx": cx,
        "q": query,
        "num": num,
    }

    if site_search:
        params["siteSearch"] = site_search
        params["siteSearchFilter"] = "i"  # "i" = include, "e" = exclude

    date_restrict = _date_restrict(days)
    if date_restrict:
        params["dateRestrict"] = date_restrict

    logger.record_api_call()
    logger.debug("Calling Google Custom Search API", extra={"query": query, "num": num, "site_search": site_search})

    try:
        r = _fetch_with_retry(GOOGLE_CUSTOM_SEARCH_ENDPOINT, params)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.error("Google API HTTP error", extra={"status": status, "query": query})
        raise
    except requests.exceptions.Timeout:
        logger.error("Google API request timeout", extra={"query": query})
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Google API request error", extra={"error": str(e), "query": query})
        raise

    try:
        data = r.json()
    except ValueError as e:
        logger.error("Failed to parse Google API JSON response", extra={"error": str(e)})
        raise ValueError(f"Invalid JSON response from Google API: {e}")

    results = []
    for item in data.get("items", []):
        link = item.get("link")
        if link:
            results.append(link)

    logger.info("Google Custom Search API returned results", extra={"query": query, "count": len(results)})
    return results


def filter_ats_links(urls: List[str]) -> List[str]:
    ats_hosts = ("greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "apply.workable.com")
    seen = set()
    filtered = []
    for u in urls:
        if any(h in u for h in ats_hosts):
            if u not in seen:
                seen.add(u)
                filtered.append(u)
    return filtered
