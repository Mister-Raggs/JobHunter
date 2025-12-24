import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import os
from .env import load_env

from . import __version__
from .normalize import (
    normalize_title,
    normalize_company,
    normalize_location,
    canonical_url,
    compute_role_id,
)
from .storage import load_store, save_store, update_role
from .schema import validate_posting
from .search import build_query, build_query_urls
from .google_results import fetch_google_links, filter_ats_links
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
    store = load_store(store_path)
    result = update_role(store, role_id, normalized)
    save_store(store_path, store)
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
    roles = [r.strip() for r in args.roles.split(",") if r.strip()] if args.roles else []
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
    roles = [r.strip() for r in args.roles.split(",") if r.strip()] if args.roles else []
    # Build base query without site: prefixes
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
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
            host = urlparse(url).netloc
            if "greenhouse.io" in host:
                from .scrapers import greenhouse as gh_scraper
                posting = gh_scraper.parse(url)
            elif "lever.co" in host:
                from .scrapers import lever as lever_scraper
                posting = lever_scraper.parse(url)
            elif "jobs.ashbyhq.com" in host:
                from .scrapers import ashby as ashby_scraper
                posting = ashby_scraper.parse(url)
            elif "apply.workable.com" in host or host.endswith("workable.com"):
                from .scrapers import workable as workable_scraper
                posting = workable_scraper.parse(url)
            else:
                skip += 1
                continue
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


def cmd_scrape(args: argparse.Namespace) -> None:
    url = args.url
    store_path = Path(args.store)
    # Guard against placeholder URLs used in examples
    if "<" in url or ">" in url:
        raise SystemExit("Provide a real job URL (no <company>/<id> placeholders). Use the 'query' command to generate search links.")
    host = urlparse(url).netloc
    if "greenhouse.io" in host:
        try:
            from .scrapers import greenhouse as gh_scraper
            posting = gh_scraper.parse(url)
        except ValueError as e:
            raise SystemExit(str(e))
    elif "lever.co" in host:
        try:
            from .scrapers import lever as lever_scraper
            posting = lever_scraper.parse(url)
        except ValueError as e:
            raise SystemExit(str(e))
    elif "jobs.ashbyhq.com" in host:
        try:
            from .scrapers import ashby as ashby_scraper
            posting = ashby_scraper.parse(url)
        except ValueError as e:
            raise SystemExit(str(e))
    elif "apply.workable.com" in host or host.endswith("workable.com"):
        try:
            from .scrapers import workable as workable_scraper
            posting = workable_scraper.parse(url)
        except ValueError as e:
            raise SystemExit(str(e))
    else:
        raise SystemExit("Unsupported URL host. Use greenhouse.io, jobs.lever.co, jobs.ashbyhq.com, or apply.workable.com")
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
                host = urlparse(url).netloc
                if "greenhouse.io" in host:
                    from .scrapers import greenhouse as gh_scraper
                    posting = gh_scraper.parse(url)
                elif "lever.co" in host:
                    from .scrapers import lever as lever_scraper
                    posting = lever_scraper.parse(url)
                else:
                    print(f"Skip unsupported host: {url}")
                    skipped += 1
                    continue
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
        if platform == "greenhouse":
            from .scrapers import greenhouse as gh_scraper
            urls = gh_scraper.list_company_posting_urls(company)
        elif platform == "lever":
            from .scrapers import lever as lever_scraper
            urls = lever_scraper.list_company_posting_urls(company)
        elif platform == "ashby":
            from .scrapers import ashby as ashby_scraper
            urls = ashby_scraper.list_company_posting_urls(company)
        elif platform == "workable":
            from .scrapers import workable as workable_scraper
            urls = workable_scraper.list_company_posting_urls(company)
        else:
            raise SystemExit("Unsupported platform. Use 'greenhouse' or 'lever'.")
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
            if platform == "greenhouse":
                from .scrapers import greenhouse as gh_scraper
                posting = gh_scraper.parse(url)
            elif platform == "lever":
                from .scrapers import lever as lever_scraper
                posting = lever_scraper.parse(url)
            elif platform == "ashby":
                from .scrapers import ashby as ashby_scraper
                posting = ashby_scraper.parse(url)
            else:
                from .scrapers import workable as workable_scraper
                posting = workable_scraper.parse(url)
            outcome = ingest_posting(posting, store_path)
            print(f"[{outcome['status']}] {outcome['role_id']}")
        except Exception as e:
            print(f"[error] {url} -> {e}")


def cmd_list(args: argparse.Namespace) -> None:
    store_path = Path(args.store)
    if not store_path.exists():
        print(f"Store not found: {store_path}")
        return
    store = load_store(store_path)
    roles = store.get("roles", {})
    if not roles:
        print("No roles in store.")
        return
    print(f"Found {len(roles)} roles in {store_path}:\n")
    for role_id, role_data in roles.items():
        current = role_data.get("current", {})
        print(f"ID: {role_id}")
        print(f"  Company: {current.get('company')}")
        print(f"  Title: {current.get('title')}")
        print(f"  Location: {current.get('location')}")
        print(f"  URL: {current.get('url')}")
        print(f"  Source: {current.get('source')}")
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
