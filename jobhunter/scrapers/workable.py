"""Workable job board scraper.

Uses the public Workable API — no auth needed.
Works for any company that hosts their jobs on Workable.
"""

import requests

API_BASE = "https://apply.workable.com/api/v3/accounts"


class WorkableScraper:
    def fetch_jobs(self, slug: str, known_ids: set[str] | None = None) -> list[dict]:
        """Fetch all published jobs for a Workable company slug."""
        resp = requests.post(
            f"{API_BASE}/{slug}/jobs",
            json={"query": "", "location": [], "department": [], "worktype": [], "remote": []},
            timeout=30,
        )
        resp.raise_for_status()

        jobs = []
        for item in resp.json().get("results", []):
            if item.get("state") != "published":
                continue
            job_id = item.get("shortcode", "")
            if known_ids and job_id in known_ids:
                continue
            loc = item.get("location", {})
            location = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
            jobs.append(
                {
                    "external_id": job_id,
                    "title": item.get("title", ""),
                    "location": location,
                    "url": f"https://apply.workable.com/{slug}/j/{job_id}",
                    "posted_at": item.get("published", ""),
                }
            )
        return jobs