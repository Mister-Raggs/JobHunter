"""Salesforce careers XML feed scraper.

Salesforce exposes a public XML job feed at careers.salesforce.com/en/jobs/xml/
which returns all open positions in a single response.
"""

import re
import xml.etree.ElementTree as ET

import requests

FEED_URL = "https://careers.salesforce.com/en/jobs/xml/?rss=true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Strip CDATA wrappers from XML text
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return _CDATA_RE.sub(r"\1", el.text).strip()


class SalesforceScraper:
    def fetch_jobs(self, slug: str = "salesforce") -> list[dict]:
        """Fetch all open jobs from Salesforce's XML feed."""
        resp = requests.get(FEED_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)

        jobs = []
        for job in root.findall("job"):
            req_id = _text(job.find("requisitionid"))
            city = _text(job.find("city"))
            state = _text(job.find("state"))
            country = _text(job.find("country"))
            location = ", ".join(p for p in [city, state, country] if p)

            jobs.append(
                {
                    "external_id": req_id,
                    "title": _text(job.find("title")),
                    "location": location,
                    "url": _text(job.find("url")),
                    "posted_at": _text(job.find("date")),
                }
            )

        return jobs
