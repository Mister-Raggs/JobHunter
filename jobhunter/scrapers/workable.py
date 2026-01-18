from typing import Dict, Any, List
from urllib.parse import urlparse
import re

from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url
from ..logger import get_logger
from .common import fetch_with_error_handling, deduplicate_urls

logger = get_logger()


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

    resp = fetch_with_error_handling(u, "workable")
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

    resp = fetch_with_error_handling(board_url, "workable")
    soup = BeautifulSoup(resp.text, "html.parser")

    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if company_slug in href:
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://apply.workable.com{href}"))

    result = deduplicate_urls(links)
    logger.info("Fetched Workable job listings", extra={"company": company_slug, "count": len(result)})
    return result
