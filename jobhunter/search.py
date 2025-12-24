from datetime import datetime, timedelta
from urllib.parse import quote_plus

DEFAULT_SITES = [
    "site:greenhouse.io",
    "site:jobs.lever.co",
    "site:jobs.ashbyhq.com",
    "site:apply.workable.com",
]


def build_query(
    roles: list[str],
    remote_only: bool = False,
    days: int | None = None,
    after: str | None = None,
    sites: list[str] | None = None,
) -> list[str]:
    """
    Returns a list of Google query strings (one per site) to paste.
    roles: list of role keywords (e.g., ["data scientist", "ml engineer"]).
    remote_only: include "\"Remote\"" in query.
    days: recency window; if provided, computes after:YYYY-MM-DD.
    after: explicit after date (YYYY-MM-DD); overrides days.
    sites: list of site: filters; defaults to greenhouse + lever.
    Note: We do not exclude seniorities by default; filtering is handled by users.
    """
    site_filters = sites or DEFAULT_SITES
    if after is None and days is not None:
        d = datetime.utcnow() - timedelta(days=days)
        after = d.strftime("%Y-%m-%d")

    role_part = "(" + " OR ".join([f'"{r}"' for r in roles]) + ")" if roles else ""
    remote_part = '"Remote"' if remote_only else ""
    after_part = f"after:{after}" if after else ""
    exclude_part = ""  # No seniority exclusion by default

    queries: list[str] = []
    for s in site_filters:
        terms = " ".join(t for t in [s, role_part, remote_part, after_part, exclude_part] if t)
        queries.append(terms)
    return queries


def build_query_urls(queries: list[str]) -> list[str]:
    base = "https://www.google.com/search?q="
    return [base + quote_plus(q) for q in queries]
