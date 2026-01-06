from typing import Dict, Any, List
from urllib.parse import urlparse
import re

import requests
from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url
from ..logger import get_logger
from ..retry import exponential_backoff

logger = get_logger()


@exponential_backoff(max_retries=3, base_delay=1.0, exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError))
def _fetch_with_retry(url: str):
    """Fetch URL with automatic retry on transient errors."""
    return requests.get(url, timeout=15)


def parse(url: str) -> Dict[str, Any]:
    """Parse an Ashby job posting page and return a posting dict.

    URL shape: https://jobs.ashbyhq.com/<company>/<job-id-or-slug>
    """
    logger.debug("Parsing Ashby URL", url=url)
    u = canonical_url(url)
    p = urlparse(u)
    parts = [x for x in p.path.split("/") if x]
    company_slug = parts[0] if parts else ""
    source_id = parts[1] if len(parts) > 1 else None

    try:
        logger.record_scrape_attempt("ashby")
        resp = _fetch_with_retry(u)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.record_scrape_failure("ashby", f"HTTPError_{status}")
        if status == 404:
            logger.warning("Ashby URL not found", url=u, status=404)
            raise ValueError(f"Ashby URL not found (404): {u}")
        logger.error("Ashby request failed", url=u, status=status)
        raise ValueError(f"Ashby request failed ({status}): {u}")
    except requests.exceptions.Timeout:
        logger.record_scrape_failure("ashby", "Timeout")
        logger.warning("Ashby request timed out", url=u)
        raise ValueError("Ashby request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.record_scrape_failure("ashby", "RequestException")
        logger.error("Ashby request error", url=u, error=str(e))
        raise ValueError(f"Ashby request error: {e}")

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
    if title and " - " in title:
        title = title.split(" - ")[0].strip()

    # Location heuristics
    loc = None
    # Ashby often uses data-test or class names with 'location'
    loc_el = soup.find(class_=re.compile("location", re.I))
    if loc_el and loc_el.get_text(strip=True):
        loc = loc_el.get_text(" ", strip=True)

    result = {
        "source": "ashby",
        "source_id": source_id,
        "company": normalize_company(company_slug),
        "title": normalize_title(title or ""),
        "location": normalize_location(loc or ""),
        "url": u,
    }

    logger.record_scrape_success("ashby")
    logger.debug("Successfully parsed Ashby job", company=company_slug, title=title)
    return result


def list_company_posting_urls(company_slug: str) -> List[str]:
    """List posting URLs from the company's Ashby board page."""
    board_url = f"https://jobs.ashbyhq.com/{company_slug}"
    try:
        resp = requests.get(board_url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            raise ValueError(f"Ashby board not found (404): {board_url}")
        raise ValueError(f"Ashby board request failed ({status}): {board_url}")
    except requests.exceptions.Timeout:
        raise ValueError("Ashby board request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Ashby board request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"/" + company_slug + "/" in href:
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://jobs.ashbyhq.com{href}"))
    seen = set()
    result = []
    for u in links:
        if u not in seen and "/jobs/" not in u:  # Ashby URLs generally without '/jobs/' segment
            seen.add(u)
            result.append(u)
    return result
