"""Qualcomm careers scraper.

Qualcomm's Eightfold-powered site requires a browser session cookie to access
the search API. We use Playwright to load the page once (which sets the
required cookies), then use those cookies with fast requests calls for pagination.

API: GET /api/pcsx/search?domain=qualcomm.com&query=&location=united+states&start=N&sort_by=timestamp
"""

import requests
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://careers.qualcomm.com/careers"
API_URL = "https://careers.qualcomm.com/api/pcsx/search"
JOB_BASE_URL = "https://careers.qualcomm.com/careers/apply"

PAGE_SIZE = 50
MAX_PAGES = 30


class QualcommScraper:
    def fetch_jobs(self, slug: str = "qualcomm", max_pages: int = MAX_PAGES, known_ids: set[str] | None = None) -> list[dict]:
        """Fetch all open US jobs from Qualcomm's careers site."""
        # Step 1: get session cookies via a real browser load
        cookies = self._get_session_cookies()

        # Step 2: paginate the API with those cookies
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": SEARCH_URL,
            }
        )

        all_jobs: list[dict] = []
        start = 0
        total = None

        while start // PAGE_SIZE < max_pages:
            resp = session.get(
                API_URL,
                params={
                    "domain": "qualcomm.com",
                    "query": "",
                    "location": "united states",
                    "start": start,
                    "num": PAGE_SIZE,
                    "sort_by": "timestamp",
                },
                timeout=30,
            )
            resp.raise_for_status()
            inner = resp.json().get("data", {})

            positions = inner.get("positions", [])
            if not positions:
                break

            if total is None:
                total = inner.get("count", 0)

            done = False
            for item in positions:
                job_id = str(item["id"])
                if known_ids and job_id in known_ids:
                    done = True
                    break
                locs = item.get("locations", [])
                location = locs[0] if locs else ""
                raw_url = item.get("positionUrl", f"/careers/apply?pid={job_id}")
                url = raw_url if raw_url.startswith("http") else f"https://careers.qualcomm.com{raw_url}"
                all_jobs.append(
                    {
                        "external_id": job_id,
                        "title": item.get("name", ""),
                        "location": location,
                        "url": url,
                        "posted_at": str(item.get("postedTs", "")),
                    }
                )
            if done:
                break

            start += PAGE_SIZE
            if total and len(all_jobs) >= total:
                break

        return all_jobs

    def _get_session_cookies(self) -> dict:
        """Launch a headless browser to get valid session cookies."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.goto(SEARCH_URL + "?sort_by=timestamp&location=united+states", timeout=30000)
            page.wait_for_timeout(3000)
            cookies = {c["name"]: c["value"] for c in context.cookies()}
            browser.close()
            return cookies
