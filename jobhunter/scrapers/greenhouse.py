from typing import Dict, Any, List
from urllib.parse import urlparse
import re

import requests
from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url


def parse(url: str) -> Dict[str, Any]:
    """Parse a Greenhouse posting page and return a posting dict.

    Raises ValueError with a user-friendly message on HTTP errors.
    """
    u = canonical_url(url)
    p = urlparse(u)
    path_parts = [x for x in p.path.split("/") if x]
    company_slug = path_parts[0] if len(path_parts) > 0 else ""
    source_id = path_parts[2] if len(path_parts) > 2 and path_parts[1] == "jobs" else None

    try:
        resp = requests.get(u, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            raise ValueError(f"Greenhouse URL not found (404): {u}")
        raise ValueError(f"Greenhouse request failed ({status}): {u}")
    except requests.exceptions.Timeout:
        raise ValueError("Greenhouse request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
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

    return {
        "source": "greenhouse",
        "source_id": source_id,
        "company": normalize_company(company_slug),
        "title": normalize_title(title or ""),
        "location": normalize_location(loc or ""),
        "url": u,
    }


def list_company_posting_urls(company_slug: str) -> List[str]:
    """List posting URLs from the company's Greenhouse board page."""
    board_url = f"https://boards.greenhouse.io/{company_slug}"
    try:
        resp = requests.get(board_url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            raise ValueError(f"Greenhouse board not found (404): {board_url}")
        raise ValueError(f"Greenhouse board request failed ({status}): {board_url}")
    except requests.exceptions.Timeout:
        raise ValueError("Greenhouse board request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
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
