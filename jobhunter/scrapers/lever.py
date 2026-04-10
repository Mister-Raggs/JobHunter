"""Lever public posting API scraper.

Lever exposes all published jobs at a single endpoint — no pagination needed.
Works for any company that hosts their board on Lever.
"""

import requests

API_BASE = "https://api.lever.co/v0/postings"


class LeverScraper:
    def fetch_jobs(self, slug: str, known_ids: set[str] | None = None) -> list[dict]:
        """Fetch all open jobs for a Lever board slug."""
        resp = requests.get(
            f"{API_BASE}/{slug}",
            params={"mode": "json", "state": "published"},
            timeout=30,
        )
        resp.raise_for_status()

        jobs = []
        for item in resp.json():
            job_id = item.get("id", "")
            if known_ids and job_id in known_ids:
                continue
            categories = item.get("categories", {})
            location = categories.get("location", "") or ", ".join(
                categories.get("allLocations", [])
            )
            jobs.append(
                {
                    "external_id": job_id,
                    "title": item.get("text", ""),
                    "location": location,
                    "url": item.get("hostedUrl", ""),
                    "posted_at": "",
                }
            )
        return jobs