import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import os
from .env import load_env

from . import __version__
from .logger import get_logger
from .cleanup import cleanup_stale_jobs
from .normalize import (
    normalize_title,
    normalize_company,
    normalize_location,
    canonical_url,
    compute_role_id,
)
from .storage import upsert_job, get_all_jobs
from .schema import validate_posting
from .search import build_query, build_query_urls
from .google_results import fetch_google_links, filter_ats_links

logger = get_logger()


def get_scraper_for_url(url: str):
    """
    Get the appropriate scraper module for a job posting URL.

    Args:
        url: Job posting URL

    Returns:
        Scraper module with parse() function

    Raises:
        ValueError: If URL host is not a supported ATS platform
    """
    host = urlparse(url).netloc

    if "greenhouse.io" in host:
        from .scrapers import greenhouse
        return greenhouse
    elif "lever.co" in host:
        from .scrapers import lever
        return lever
    elif "jobs.ashbyhq.com" in host:
        from .scrapers import ashby
        return ashby
    elif "apply.workable.com" in host or host.endswith("workable.com"):
        from .scrapers import workable
        return workable
    else:
        raise ValueError(f"Unsupported ATS platform: {host}")


def get_scraper_by_platform(platform: str):
    """
    Get scraper module by platform name.

    Args:
        platform: Platform name (greenhouse, lever, ashby, workable)

    Returns:
        Scraper module

    Raises:
        ValueError: If platform is not supported
    """
    if platform == "greenhouse":
        from .scrapers import greenhouse
        return greenhouse
    elif platform == "lever":
        from .scrapers import lever
        return lever
    elif platform == "ashby":
        from .scrapers import ashby
        return ashby
    elif platform == "workable":
        from .scrapers import workable
        return workable
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def parse_roles(roles_str: str) -> list:
    """Parse comma-separated roles string into list."""
    if not roles_str:
        return []
    return [r.strip() for r in roles_str.split(",") if r.strip()]


def ingest_posting(posting: dict, store_path: Path) -> dict:
    errors = validate_posting(posting)
    if errors:
        # Log but don't crash - return error status
        return {"role_id": None, "status": "validation_error", "errors": errors}

    company = posting.get("company", "")
    title = posting.get("title", "")
    location = posting.get("location", "") or "unknown"  # Default if empty
    source = posting.get("source")
    source_id = posting.get("source_id")
    url = posting.get("url")

    normalized = {
        "company": normalize_company(company),
        "title": normalize_title(title),
        "location": normalize_location(location),
        "url": canonical_url(url) if url else None,
        "source": source,
        "source_id": source_id,
    }

    role_id = compute_role_id(company, source, source_id, url)

    # Derive database path from store path
    db_path = store_path.parent / "jobs.db"
    result = upsert_job(role_id, normalized, db_path)

    return {"role_id": role_id, **result}


def cmd_ingest(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    store_path = Path(args.store)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        posting = json.load(f)

    outcome = ingest_posting(posting, store_path)
    print(f"Role: {outcome['role_id']}")
    print(f"Status: {outcome['status']}")


def cmd_validate(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    with input_path.open("r", encoding="utf-8") as f:
        posting = json.load(f)
    errors = validate_posting(posting)
    if errors:
        print("Invalid:")
        for e in errors:
            print(f" - {e}")
        raise SystemExit(2)
    print("Valid")


def cmd_query(args: argparse.Namespace) -> None:
    roles = parse_roles(args.roles)
    queries = build_query(
        roles=roles,
        remote_only=args.remote,
        days=args.days,
        after=args.after,
        sites=(args.sites.split(",") if args.sites else None),
    )
    urls = build_query_urls(queries)
    print("Google query URLs:")
    for u in urls:
        print(f" - {u}")


def cmd_query_scrape(args: argparse.Namespace) -> None:
    roles = parse_roles(args.roles)
    if not roles:
        raise SystemExit("No roles specified. Use --roles \"role1,role2\"")

    # Build query terms without site: prefixes (we'll use siteSearch param instead)
    query_terms = " ".join([f'"{role}"' for role in roles])
    if args.remote:
        query_terms += ' "Remote"'
    if args.after:
        query_terms += f' after:{args.after}'

    api_key = args.api_key or os.getenv("GOOGLE_API_KEY")
    cse_id = args.cse_id or os.getenv("GOOGLE_CSE_ID")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY not set. Set env var or pass --api-key.")
    if not cse_id:
        raise SystemExit("GOOGLE_CSE_ID not set. Set env var or pass --cse-id.")

    # Define ATS sites to search
    ats_sites = ["greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "apply.workable.com"]

    print("Fetching Google results via Custom Search API...")
    all_links = []
    for site in ats_sites:
        try:
            links = fetch_google_links(query_terms, api_key=api_key, cse_id=cse_id, num=args.num, days=args.days, site_search=site)
            all_links.extend(links)
        except Exception as e:
            print(f"[warn] site search failed ({site}): {e}")

    if not all_links:
        print("No results found.")
        return
    print(f"Found {len(all_links)} total results. Scraping...")
    store_path = Path(args.store)
    new = upd = same = skip = 0
    for url in all_links:
        try:
            scraper = get_scraper_for_url(url)
            posting = scraper.parse(url)
            outcome = ingest_posting(posting, store_path)
            s = outcome["status"]
            if s == "validation_error":
                print(f"[validation_error] {url} - {outcome.get('errors', [])}")
                skip += 1
                continue
            if s == "new":
                new += 1
            elif s == "updated":
                upd += 1
            else:
                same += 1
            print(f"[{s}] {outcome['role_id']}")
        except Exception as e:
            print(f"[error] {url} -> {e}")
            skip += 1
    print(f"Done. new={new} updated={upd} no-change={same} skipped={skip}")

    # Run cleanup to remove stale jobs (older than 7 days)
    print("\n--- Cleaning up stale jobs (>7 days old) ---")
    before, after = cleanup_stale_jobs(store_path, days=7)
    if before > after:
        removed = before - after
        print(f"Removed {removed} stale job(s). Jobs remaining: {after}")
    else:
        print(f"No stale jobs to remove. Jobs in store: {after}")

    print("\n--- Metrics Summary ---")
    logger.log_metrics_summary()


def cmd_scrape(args: argparse.Namespace) -> None:
    url = args.url
    store_path = Path(args.store)
    # Guard against placeholder URLs used in examples
    if "<" in url or ">" in url:
        raise SystemExit("Provide a real job URL (no <company>/<id> placeholders). Use the 'query' command to generate search links.")

    try:
        scraper = get_scraper_for_url(url)
        posting = scraper.parse(url)
    except ValueError as e:
        raise SystemExit(str(e))

    outcome = ingest_posting(posting, store_path)
    print(f"Role: {outcome['role_id']}")
    print(f"Status: {outcome['status']}")


def cmd_scrape_file(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    store_path = Path(args.store)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    count = 0
    new = 0
    updated = 0
    same = 0
    skipped = 0
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            count += 1
            try:
                scraper = get_scraper_for_url(url)
                posting = scraper.parse(url)
                outcome = ingest_posting(posting, store_path)
                status = outcome["status"]
                if status == "new":
                    new += 1
                elif status == "updated":
                    updated += 1
                else:
                    same += 1
                print(f"[{status}] {outcome['role_id']}")
            except Exception as e:
                print(f"[error] {url} -> {e}")
                skipped += 1
    print(f"Done. total={count} new={new} updated={updated} no-change={same} skipped={skipped}")


def cmd_scrape_board(args: argparse.Namespace) -> None:
    platform = args.platform
    company = args.company
    store_path = Path(args.store)
    limit = args.limit

    try:
        scraper = get_scraper_by_platform(platform)
        urls = scraper.list_company_posting_urls(company)
    except ValueError as e:
        raise SystemExit(str(e))

    if limit is not None:
        urls = urls[:limit]
    if not urls:
        print("No postings found.")
        return
    print(f"Found {len(urls)} postings. Scraping...")
    for url in urls:
        try:
            posting = scraper.parse(url)
            outcome = ingest_posting(posting, store_path)
            print(f"[{outcome['status']}] {outcome['role_id']}")
        except Exception as e:
            print(f"[error] {url} -> {e}")


def cmd_list(args: argparse.Namespace) -> None:
    store_path = Path(args.store)

    # Derive database path from store path
    db_path = store_path.parent / "jobs.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    jobs = get_all_jobs(db_path)

    if not jobs:
        print("No jobs in database.")
        return

    print(f"Found {len(jobs)} jobs in {db_path}:\n")
    for job in jobs:
        print(f"ID: {job['role_id']}")
        print(f"  Company: {job['company']}")
        print(f"  Title: {job['title']}")
        print(f"  Location: {job['location']}")
        print(f"  URL: {job['url']}")
        print(f"  Source: {job['source']}")
        print()


def main():
    # Load .env if present (GOOGLE_API_KEY, GOOGLE_CSE_ID, etc.)
    load_env()
    parser = argparse.ArgumentParser(prog="jobhunter", description="Job Hunter — clean MVP CLI")
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")
    ing = subparsers.add_parser("ingest", help="Ingest a single posting JSON and persist state")
    ing.add_argument("--input", required=True, help="Path to posting JSON input")
    ing.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    ing.set_defaults(func=cmd_ingest)

    val = subparsers.add_parser("validate", help="Validate a posting JSON against the MVP schema")
    val.add_argument("--input", required=True, help="Path to posting JSON input")
    val.set_defaults(func=cmd_validate)

    qry = subparsers.add_parser("query", help="Build Google search URLs for ATS job boards")
    qry.add_argument("--roles", help="Comma-separated role keywords (quoted). Example: \"data scientist\",\"ml engineer\"")
    qry.add_argument("--remote", action="store_true", help="Add 'Remote' filter")
    qry.add_argument("--days", type=int, help="Recency window in days (computes after:)")
    qry.add_argument("--after", help="Explicit after: YYYY-MM-DD (overrides --days)")
    qry.add_argument("--sites", help="Comma-separated site filters. Default: site:greenhouse.io,site:jobs.lever.co,site:jobs.ashbyhq.com,site:apply.workable.com")
    qry.set_defaults(func=cmd_query)

    qrs = subparsers.add_parser("query-scrape", help="Run Google queries via Custom Search API and scrape ATS results")
    qrs.add_argument("--roles", help="Comma-separated role keywords")
    qrs.add_argument("--remote", action="store_true", help="Add 'Remote' filter")
    qrs.add_argument("--days", type=int, help="Recency window in days (sets dateRestrict)")
    qrs.add_argument("--after", help="Explicit after: YYYY-MM-DD (included in query text)")
    qrs.add_argument("--sites", help="Comma-separated site filters (default ATS)")
    qrs.add_argument("--num", type=int, default=10, help="Results per query (default 10, max 10 for CSE)")
    qrs.add_argument("--api-key", help="Google API key (or set GOOGLE_API_KEY)")
    qrs.add_argument("--cse-id", help="Custom Search Engine ID (or set GOOGLE_CSE_ID)")
    qrs.add_argument("--store", default="data/store.json", help="Path to JSON store")
    qrs.set_defaults(func=cmd_query_scrape)

    scr = subparsers.add_parser("scrape", help="Scrape a job posting URL (greenhouse/lever/ashby/workable) and ingest")
    scr.add_argument("--url", required=True, help="Job posting URL from greenhouse/lever/ashby/workable")
    scr.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    scr.set_defaults(func=cmd_scrape)

    scrf = subparsers.add_parser("scrape-file", help="Scrape job posting URLs from a file and ingest")
    scrf.add_argument("--input", required=True, help="Text file with one URL per line")
    scrf.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    scrf.set_defaults(func=cmd_scrape_file)

    scrb = subparsers.add_parser("scrape-board", help="Scrape all postings from a company board (greenhouse/lever/ashby/workable)")
    scrb.add_argument("--platform", required=True, choices=["greenhouse", "lever", "ashby", "workable"], help="ATS platform")
    scrb.add_argument("--company", required=True, help="Company slug on the chosen platform")
    scrb.add_argument("--limit", type=int, help="Optional limit on number of postings to scrape")
    scrb.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    scrb.set_defaults(func=cmd_scrape_board)

    lst = subparsers.add_parser("list", help="List all stored roles")
    lst.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    lst.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if hasattr(args, "func"):
        args.func(args)
        return

    print("Job Hunter reset: ready to build MVP.")


if __name__ == "__main__":
    main()
