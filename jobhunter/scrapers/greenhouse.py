from typing import Dict, Any, List
from urllib.parse import urlparse
import re

import requests
from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url
from ..logger import get_logger
from ..retry import exponential_backoff, is_transient_error

logger = get_logger()


@exponential_backoff(max_retries=3, base_delay=1.0, exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError))
def _fetch_with_retry(url: str):
    """Fetch URL with automatic retry on transient errors."""
    return requests.get(url, timeout=15)


def parse(url: str) -> Dict[str, Any]:
    """Parse a Greenhouse posting page and return a posting dict.

    Raises ValueError with a user-friendly message on HTTP errors.
    """
    logger.debug("Parsing Greenhouse URL", url=url)
    u = canonical_url(url)
    p = urlparse(u)
    path_parts = [x for x in p.path.split("/") if x]
    company_slug = path_parts[0] if len(path_parts) > 0 else ""
    source_id = path_parts[2] if len(path_parts) > 2 and path_parts[1] == "jobs" else None

    try:
        logger.record_scrape_attempt("greenhouse")
        resp = _fetch_with_retry(u)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.record_scrape_failure("greenhouse", f"HTTPError_{status}")
        if status == 404:
            logger.warning("Greenhouse URL not found", url=u, status=404)
            raise ValueError(f"Greenhouse URL not found (404): {u}")
        logger.error("Greenhouse request failed", url=u, status=status)
        raise ValueError(f"Greenhouse request failed ({status}): {u}")
    except requests.exceptions.Timeout:
        logger.record_scrape_failure("greenhouse", "Timeout")
        logger.warning("Greenhouse request timed out", url=u)
        raise ValueError("Greenhouse request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.record_scrape_failure("greenhouse", "RequestException")
        logger.error("Greenhouse request error", url=u, error=str(e))
        raise ValueError(f"Greenhouse request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title heuristics
    title = None
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    if not title:
        t = soup.find("title")
        if t and t.get_text(strip=True):
            title = t.get_text(strip=True)
    # Often includes company name suffix; trim after ' - ' if present
    if title and " - " in title:
        title = title.split(" - ")[0].strip()

    # Location heuristics
    loc = None
    loc_el = soup.find(class_=re.compile("location|opening-location"))
    if loc_el and loc_el.get_text(strip=True):
        loc = loc_el.get_text(strip=True)

    result = {
        "source": "greenhouse",
        "source_id": source_id,
        "company": normalize_company(company_slug),
        "title": normalize_title(title or ""),
        "location": normalize_location(loc or ""),
        "url": u,
    }

    logger.record_scrape_success("greenhouse")
    logger.debug("Successfully parsed Greenhouse job", company=company_slug, title=title)
    return result


def list_company_posting_urls(company_slug: str) -> List[str]:
    """List posting URLs from the company's Greenhouse board page."""
    board_url = f"https://boards.greenhouse.io/{company_slug}"
    logger.debug("Fetching Greenhouse board", company=company_slug, url=board_url)

    try:
        resp = _fetch_with_retry(board_url)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            logger.warning("Greenhouse board not found", company=company_slug, status=404)
            raise ValueError(f"Greenhouse board not found (404): {board_url}")
        logger.error("Greenhouse board request failed", company=company_slug, status=status)
        raise ValueError(f"Greenhouse board request failed ({status}): {board_url}")
    except requests.exceptions.Timeout:
        logger.warning("Greenhouse board request timed out", company=company_slug)
        raise ValueError("Greenhouse board request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.error("Greenhouse board request error", company=company_slug, error=str(e))
        raise ValueError(f"Greenhouse board request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/jobs/" in href and company_slug in href:
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://boards.greenhouse.io{href}"))
    # dedupe while preserving order
    seen = set()
    result = []
    for u in links:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
