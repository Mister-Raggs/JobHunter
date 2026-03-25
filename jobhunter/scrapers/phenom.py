"""Phenom People careers scraper.

Phenom-hosted career sites embed job search results as JSON inside a
`phApp.ddo` JavaScript object in the server-rendered HTML.

Works for any company on Phenom (CVS Health, etc.).
"""

import json
import re

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

DDO_RE = re.compile(r"phApp\.ddo\s*=\s*(\{.*?\});", re.DOTALL)

# Map slug -> (search results URL, job detail base URL)
PHENOM_HOSTS: dict[str, tuple[str, str]] = {
    "cvshealth": (
        "https://jobs.cvshealth.com/us/en/search-results",
        "https://jobs.cvshealth.com/us/en/job",
    ),
}

MAX_PAGES = 20  # safety cap
PAGE_SIZE = 100


class PhenomScraper:
    def fetch_jobs(self, slug: str, max_pages: int = MAX_PAGES) -> list[dict]:
        """Fetch all open jobs from a Phenom-hosted career site."""
        search_url, job_base_url = PHENOM_HOSTS[slug]

        session = requests.Session()
        session.headers.update(HEADERS)

        all_jobs: list[dict] = []
        page = 1
        total = None

        while page <= max_pages:
            resp = session.get(
                search_url,
                params={"from": (page - 1) * PAGE_SIZE, "s": PAGE_SIZE, "sortBy": "Most recent"},
                timeout=30,
            )
            resp.raise_for_status()

            match = DDO_RE.search(resp.text)
            if not match:
                break

            ddo = json.loads(match.group(1))
            search_data = ddo.get("eagerLoadRefineSearch", {})
            jobs = search_data.get("data", {}).get("jobs", [])
            if not jobs:
                break

            if total is None:
                total = search_data.get("totalHits", 0)

            for item in jobs:
                job_id = str(item.get("jobId", item.get("reqId", "")))
                all_jobs.append(
                    {
                        "external_id": job_id,
                        "title": item.get("title", ""),
                        "location": item.get("location", item.get("cityStateCountry", "")),
                        "url": item.get("applyUrl", f"{job_base_url}/{job_id}"),
                        "posted_at": item.get("postedDate", item.get("dateCreated", "")),
                    }
                )

            if total and len(all_jobs) >= total:
                break
            page += 1

        return all_jobs
