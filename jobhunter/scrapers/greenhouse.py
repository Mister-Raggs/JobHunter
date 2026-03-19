"""Greenhouse boards API scraper.

Uses the public JSON API at boards-api.greenhouse.io — no API key needed.
Works for any company that hosts their job board on Greenhouse
(DoorDash, Cloudflare, Discord, etc.).
"""

import requests

API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper:
    def fetch_jobs(self, slug: str) -> list[dict]:
        """Fetch all open jobs for a Greenhouse board slug."""
        url = f"{API_BASE}/{slug}/jobs"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for item in data.get("jobs", []):
            location = ""
            if item.get("location"):
                location = item["location"].get("name", "")

            jobs.append(
                {
                    "external_id": str(item["id"]),
                    "title": item["title"],
                    "location": location,
                    "url": item["absolute_url"],
                    "posted_at": item.get("updated_at", ""),
                }
            )
        return jobs
