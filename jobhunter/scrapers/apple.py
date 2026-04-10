"""Apple careers scraper.

Apple's job site embeds search results as JSON hydration data in the HTML.
We fetch the search page sorted by newest and extract jobs from the embedded data.
Pagination uses the ?page= query parameter (20 results per page).
"""

import json
import re

import requests

SEARCH_URL = "https://jobs.apple.com/en-us/search"
JOB_BASE_URL = "https://jobs.apple.com/en-us/details"

HYDRATION_RE = re.compile(
    r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.+?)"\);',
    re.DOTALL,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

MAX_PAGES = 10  # safety cap — 20 results/page = 200 jobs max


class AppleScraper:
    def fetch_jobs(self, slug: str = "apple", max_pages: int = MAX_PAGES, known_ids: set[str] | None = None) -> list[dict]:
        """Fetch recent job postings from Apple's careers site."""
        session = requests.Session()
        session.headers.update(HEADERS)

        all_jobs: list[dict] = []
        page = 1
        total_records = None

        while page <= max_pages:
            resp = session.get(
                SEARCH_URL,
                params={"sort": "newest", "page": page, "location": "united-states-USA"},
                timeout=30,
            )
            resp.raise_for_status()

            match = HYDRATION_RE.search(resp.text)
            if not match:
                break

            unescaped = match.group(1).encode().decode("unicode_escape")
            data = json.loads(unescaped)

            search_data = data.get("loaderData", {}).get("search", {})
            results = search_data.get("searchResults", [])
            if not results:
                break

            if total_records is None:
                total_records = search_data.get("totalRecords", 0)

            page_new = 0
            for item in results:
                position_id = str(item.get("positionId", item.get("id", "")))
                if known_ids and position_id in known_ids:
                    continue
                title = item.get("postingTitle", "")
                locations = item.get("locations", [])
                location = locations[0].get("name", "") if locations else ""
                posted_date = item.get("postingDate", "")
                transformed = item.get("transformedPostingTitle", "")
                url = (
                    f"{JOB_BASE_URL}/{position_id}/{transformed}"
                    if transformed
                    else f"{JOB_BASE_URL}/{position_id}"
                )
                all_jobs.append(
                    {
                        "external_id": position_id,
                        "title": title,
                        "location": location,
                        "url": url,
                        "posted_at": posted_date,
                    }
                )
                page_new += 1
            if known_ids and page_new == 0:
                break

            if total_records and len(all_jobs) >= total_records:
                break
            page += 1

        return all_jobs
