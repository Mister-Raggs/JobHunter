"""CLI entry point for JobHunter."""

import argparse

from dotenv import load_dotenv

from . import __version__
from .config import COMPANIES
from .database import add_jobs, get_all_jobs, job_count
from .notifier import send_email
from .scrapers import get_scraper


def cmd_check(args: argparse.Namespace) -> None:
    """Check configured companies for new job postings."""
    keys = [k.strip() for k in args.companies.split(",")] if args.companies else list(COMPANIES)

    all_new: list[dict] = []

    for key in keys:
        config = COMPANIES.get(key)
        if not config:
            print(f"Unknown company: {key}")
            continue

        print(f"\nChecking {config.name}...")
        scraper = get_scraper(config.scraper)

        try:
            jobs = scraper.fetch_jobs(config.slug)
            print(f"  {len(jobs)} open listings")

            new_jobs = add_jobs(jobs, key)
            if new_jobs:
                print(f"  {len(new_jobs)} NEW:")
                for job in new_jobs:
                    print(f"    {job['title']}")
                    print(f"    {job.get('location', '')}  {job['url']}")
                all_new.extend([{**j, "company": config.name} for j in new_jobs])
            else:
                print("  No new jobs")
        except Exception as e:
            print(f"  Error: {e}")

    # Summary
    print(f"\n--- {len(all_new)} new job(s) found ---")

    if all_new and args.email:
        print(f"Sending email to {args.email}...")
        if send_email(all_new, args.email):
            print("Email sent!")


def cmd_list(args: argparse.Namespace) -> None:
    """List all tracked jobs."""
    company = args.company if args.company else None
    jobs = get_all_jobs(company)

    if not jobs:
        print("No jobs tracked yet. Run 'check' first.")
        return

    print(f"\n{len(jobs)} tracked job(s):\n")
    current_company = None
    for job in jobs:
        if job.company != current_company:
            current_company = job.company
            display_name = COMPANIES[job.company].name if job.company in COMPANIES else job.company
            print(f"  [{display_name}]")
        print(f"    {job.title}")
        print(f"    {job.location}  |  {job.url}")
        print()


def cmd_companies(args: argparse.Namespace) -> None:
    """List configured companies."""
    print("\nConfigured companies:\n")
    for key, config in COMPANIES.items():
        count = job_count(key)
        print(f"  {key:15s}  {config.name:15s}  scraper={config.scraper:12s}  jobs={count}")


def cmd_stats(args: argparse.Namespace) -> None:
    """Show job tracking statistics."""
    total = job_count()
    print(f"\nTotal tracked jobs: {total}")
    for key, config in COMPANIES.items():
        c = job_count(key)
        print(f"  {config.name}: {c}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="jobhunter",
        description="JobHunter — track new job postings from target companies",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    # check
    p_check = sub.add_parser("check", help="Check for new job postings")
    p_check.add_argument("-c", "--companies", help="Comma-separated company keys (default: all)")
    p_check.add_argument("-e", "--email", help="Email address for notifications")
    p_check.set_defaults(func=cmd_check)

    # list
    p_list = sub.add_parser("list", help="List all tracked jobs")
    p_list.add_argument("--company", help="Filter by company key")
    p_list.set_defaults(func=cmd_list)

    # companies
    p_co = sub.add_parser("companies", help="List configured companies")
    p_co.set_defaults(func=cmd_companies)

    # stats
    p_stats = sub.add_parser("stats", help="Show tracking statistics")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
