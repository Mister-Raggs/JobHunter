from typing import Dict, Any, List
from urllib.parse import urlparse
import re

import requests
from bs4 import BeautifulSoup

from ..normalize import normalize_company, normalize_title, normalize_location, canonical_url


def parse(url: str) -> Dict[str, Any]:
    """Parse a Lever posting page and return a posting dict.

    Raises ValueError with a user-friendly message on HTTP errors.
    """
    u = canonical_url(url)
    p = urlparse(u)
    path_parts = [x for x in p.path.split("/") if x]
    company_slug = path_parts[0] if len(path_parts) > 0 else ""
    source_id = path_parts[1] if len(path_parts) > 1 else None

    try:
        resp = requests.get(u, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            raise ValueError(f"Lever URL not found (404): {u}")
        raise ValueError(f"Lever request failed ({status}): {u}")
    except requests.exceptions.Timeout:
        raise ValueError("Lever request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Lever request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title heuristics
    title = None
    h2 = soup.find("h2")
    if h2 and h2.get_text(strip=True):
        title = h2.get_text(strip=True)
    if not title:
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
    loc_el = soup.find(class_=re.compile("location|posting-categories"))
    if loc_el and loc_el.get_text(strip=True):
        loc_text = loc_el.get_text(" ", strip=True)
        # Lever often shows multiple categories; attempt to pick location-like token
        candidates = [x for x in re.split(r"[,|/]", loc_text) if x.strip()]
        loc = candidates[0] if candidates else loc_text

    return {
        "source": "lever",
        "source_id": source_id,
        "company": normalize_company(company_slug),
        "title": normalize_title(title or ""),
        "location": normalize_location(loc or ""),
        "url": u,
    }


def list_company_posting_urls(company_slug: str) -> List[str]:
    """List posting URLs from the company's Lever board page."""
    board_url = f"https://jobs.lever.co/{company_slug}"
    try:
        resp = requests.get(board_url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "HTTPError"
        if status == 404:
            raise ValueError(f"Lever board not found (404): {board_url}")
        raise ValueError(f"Lever board request failed ({status}): {board_url}")
    except requests.exceptions.Timeout:
        raise ValueError("Lever board request timed out. Try again later.")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Lever board request error: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Link patterns can be absolute or relative; target company slug
        if company_slug in href and (href.endswith("/apply") is False):
            if href.startswith("http"):
                links.append(canonical_url(href))
            else:
                links.append(canonical_url(f"https://jobs.lever.co{href}"))
    # dedupe while preserving order
    seen = set()
    result = []
    for u in links:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
