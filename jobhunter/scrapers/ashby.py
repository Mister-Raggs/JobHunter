from typing import Dict, Any, List
from urllib.parse import urlparse
import re

from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url
from ..logger import get_logger
from .common import fetch_with_error_handling, deduplicate_urls

logger = get_logger()


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
    resp = fetch_with_error_handling(u, "ashby")        title = h1.get_text(strip=True)
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

    resp = fetch_with_error_handling(board_url, "ashby")
    soup = BeautifulSoup(resp.text, "html.parser")

    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"/" + company_slug + "/" in href:
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://jobs.ashbyhq.com{href}"))

    # Filter out '/jobs/' segments and deduplicate
    return [u for u in deduplicate_urls(links) if "/jobs/" not in u]
