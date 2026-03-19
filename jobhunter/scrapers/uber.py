"""Uber careers API scraper.

Uber uses a custom careers portal at uber.com/us/en/careers/.
Job listings are fetched via a POST endpoint that returns paginated results.
"""

import requests

SEARCH_URL = "https://www.uber.com/api/loadSearchJobsResults"
JOB_BASE_URL = "https://www.uber.com/us/en/careers/list"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-csrf-token": "x",
}

PAGE_SIZE = 50
MAX_PAGES = 30  # safety cap — 50 * 30 = 1500 jobs max


class UberScraper:
    def fetch_jobs(self, slug: str = "uber", max_pages: int = MAX_PAGES) -> list[dict]:
        """Fetch all open jobs from Uber's careers portal."""
        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers["Referer"] = "https://www.uber.com/us/en/careers/list/"

        all_jobs: list[dict] = []
        page = 1
        total = None

        while page <= max_pages:
            payload = {
                "params": {"location": [], "department": [], "team": []},
                "page": page,
                "limit": PAGE_SIZE,
            }
            resp = session.post(SEARCH_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("data", {}).get("results", [])
            if not results:
                break

            if total is None:
                total_obj = data.get("data", {}).get("totalResults", {})
                total = total_obj.get("low", 0) if isinstance(total_obj, dict) else int(total_obj)

            for item in results:
                job_id = str(item["id"])
                loc = item.get("location", "")
                if isinstance(loc, dict):
                    parts = [loc.get("city", ""), loc.get("region", ""), loc.get("countryName", "")]
                    loc = ", ".join(p for p in parts if p)

                all_jobs.append(
                    {
                        "external_id": job_id,
                        "title": item["title"],
                        "location": loc,
                        "url": f"{JOB_BASE_URL}/{job_id}",
                        "posted_at": item.get("creationDate", ""),
                    }
                )

            if total and len(all_jobs) >= total:
                break
            page += 1

        return all_jobs
