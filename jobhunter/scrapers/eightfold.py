"""Eightfold careers API scraper.

Eightfold hosts career pages for many companies (Netflix, Qualcomm, etc.).
The public search API at {host}/api/apply/v2/jobs returns paginated results.

Each company has its own Eightfold subdomain/host. Configure via the slug
which maps to the Eightfold host in EIGHTFOLD_HOSTS.
"""

import requests

# Map company slug -> (eightfold host, domain param, job URL base)
EIGHTFOLD_HOSTS: dict[str, tuple[str, str, str]] = {
    "netflix": (
        "https://explore.jobs.netflix.net",
        "netflix.com",
        "https://explore.jobs.netflix.net/careers/job",
    ),
}

PAGE_SIZE = 100
MAX_PAGES = 20  # safety cap


class EightfoldScraper:
    def fetch_jobs(self, slug: str, max_pages: int = MAX_PAGES, known_ids: set[str] | None = None) -> list[dict]:
        """Fetch all open jobs from an Eightfold-hosted career site."""
        host, domain, job_base_url = EIGHTFOLD_HOSTS[slug]

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

        all_jobs: list[dict] = []
        start = 0
        total = None

        while start // PAGE_SIZE < max_pages:
            resp = session.get(
                f"{host}/api/apply/v2/jobs",
                params={
                    "domain": domain,
                    "start": start,
                    "num": PAGE_SIZE,
                    "sort_by": "timestamp",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            positions = data.get("positions", [])
            if not positions:
                break

            if total is None:
                total = data.get("count", 0)

            done = False
            for item in positions:
                job_id = str(item["id"])
                if known_ids and job_id in known_ids:
                    done = True
                    break
                loc = item.get("location", "")
                all_jobs.append(
                    {
                        "external_id": job_id,
                        "title": item.get("name", item.get("posting_name", "")),
                        "location": loc,
                        "url": item.get("canonicalPositionUrl", f"{job_base_url}/{job_id}"),
                        "posted_at": "",
                    }
                )
            if done:
                break

            start += PAGE_SIZE
            if total and len(all_jobs) >= total:
                break

        return all_jobs
