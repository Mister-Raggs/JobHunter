"""Ashby posting API scraper.

Uses the public posting API at api.ashbyhq.com — no API key needed.
Works for any company that hosts their job board on Ashby (Baseten, etc.).
"""

import requests

API_BASE = "https://api.ashbyhq.com/posting-api/job-board"


class AshbyScraper:
    def fetch_jobs(self, slug: str) -> list[dict]:
        """Fetch all open jobs for an Ashby board slug."""
        url = f"{API_BASE}/{slug}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for item in data.get("jobs", []):
            if not item.get("isListed", True):
                continue

            jobs.append(
                {
                    "external_id": str(item["id"]),
                    "title": item["title"],
                    "location": item.get("location", ""),
                    "url": item.get("jobUrl", ""),
                    "posted_at": item.get("publishedAt", ""),
                }
            )
        return jobs
