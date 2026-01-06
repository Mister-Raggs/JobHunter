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
    """Parse a Workable job posting page and return a posting dict.

    Common URL: https://apply.workable.com/<company>/<job-id-or-slug>
    """
    logger.debug("Parsing Workable URL", url=url)
    u = canonical_url(url)
    p = urlparse(u)
    parts = [x for x in p.path.split("/") if x]
    # apply.workable.com/<company>/<id>
    company_slug = parts[0] if parts else ""
    source_id = parts[1] if len(parts) > 1 else None

    try:
        logger.record_scrape_attempt("workable")
        resp = _fetch_with_retry(u)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.record_scrape_failure("workable", f"HTTPError_{status}")
        if status == 404:
            logger.warning("Workable URL not found", url=u, status=404)
            raise ValueError(f"Workable URL not found (404): {u}")
        logger.error("Workable request failed", url=u, status=status)
        raise ValueError(f"Workable request failed ({status}): {u}")
    except requests.exceptions.Timeout:
        logger.record_scrape_failure("workable", "Timeout")
        logger.warning("Workable request timed out", url=u)
        raise ValueError("Workable request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.record_scrape_failure("workable", "RequestException")
        logger.error("Workable request error", url=u, error=str(e))
        raise ValueError(f"Workable request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

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

    loc = None
    loc_el = soup.find(class_=re.compile("location|job-location", re.I))
    if loc_el and loc_el.get_text(strip=True):
        loc = loc_el.get_text(" ", strip=True)

    logger.record_scrape_success("workable")
    logger.debug("Successfully parsed Workable job", extra={"company": company_slug, "title": title or ""})

    return {
        "source": "workable",
        "source_id": source_id,
        "company": normalize_company(company_slug),
        "title": normalize_title(title or ""),
        "location": normalize_location(loc or ""),
        "url": u,
    }


def list_company_posting_urls(company_slug: str) -> List[str]:
    """List posting URLs from the company's Workable board page."""
    board_url = f"https://apply.workable.com/{company_slug}"
    logger.debug("Fetching Workable job board", extra={"company": company_slug, "url": board_url})

    try:
        resp = _fetch_with_retry(board_url)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        logger.error("Workable board HTTP error", extra={"company": company_slug, "status": status, "url": board_url})
        if status == 404:
            raise ValueError(f"Workable board not found (404): {board_url}")
        raise ValueError(f"Workable board request failed ({status}): {board_url}")
    except requests.exceptions.Timeout:
        logger.error("Workable board request timeout", extra={"company": company_slug, "url": board_url})
        raise ValueError("Workable board request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        logger.error("Workable board request error", extra={"company": company_slug, "error": str(e), "url": board_url})
        raise ValueError(f"Workable board request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if company_slug in href:
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://apply.workable.com{href}"))
    seen = set()
    result = []
    for u in links:
        if u not in seen:
            seen.add(u)
            result.append(u)

    logger.info("Fetched Workable job listings", extra={"company": company_slug, "count": len(result)})
    return result
