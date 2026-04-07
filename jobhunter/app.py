"""CLI entry point for JobHunter."""

import argparse
import time
import traceback

from dotenv import load_dotenv

from . import __version__
from .config import COMPANIES
from .database import add_jobs, get_all_jobs, get_known_ids, get_unnotified_jobs, job_count, mark_notified
from .logger import get_logger
from .notifier import send_email
from .scrapers import get_scraper


def cmd_check(args: argparse.Namespace) -> None:
    """Check configured companies for new job postings."""
    log = get_logger()
    keys = [k.strip() for k in args.companies.split(",")] if args.companies else list(COMPANIES)
    auto = getattr(args, "auto", False)

    all_new: list[dict] = []
    run_start = time.monotonic()
    errors: list[str] = []

    log.info("run_start companies=%d", len(keys))

    for key in keys:
        config = COMPANIES.get(key)
        if not config:
            log.warning("unknown_company key=%s", key)
            if not auto:
                print(f"Unknown company: {key}")
            continue

        if not auto:
            print(f"\nChecking {config.name}...")

        scraper = get_scraper(config.scraper)
        t0 = time.monotonic()

        try:
            known_ids = get_known_ids(key)
            jobs = scraper.fetch_jobs(config.slug, known_ids=known_ids)
            duration = time.monotonic() - t0

            new_jobs = add_jobs(jobs, key)
            log.info(
                "company=%s scraper=%s duration=%.2fs fetched=%d new=%d",
                key, config.scraper, duration, len(jobs), len(new_jobs),
            )

            if not auto:
                print(f"  {len(jobs)} open listings")
            if new_jobs:
                if not auto:
                    print(f"  {len(new_jobs)} NEW:")
                    for job in new_jobs:
                        print(f"    {job['title']}")
                        print(f"    {job.get('location', '')}  {job['url']}")
                all_new.extend([{**j, "company": config.name} for j in new_jobs])
            elif not auto:
                print("  No new jobs")

        except Exception as e:
            duration = time.monotonic() - t0
            log.error(
                "company=%s scraper=%s duration=%.2fs error=%s",
                key, config.scraper, duration, e,
            )
            log.debug(traceback.format_exc())
            errors.append(f"{config.name}: {e}")
            if not auto:
                print(f"  Error: {e}")

    total_duration = time.monotonic() - run_start

    if not auto:
        print(f"\n--- {len(all_new)} new job(s) found ---")

    if auto:
        unnotified = get_unnotified_jobs()
        if unnotified:
            jobs_to_send = [
                {"company": COMPANIES[j.company].name if j.company in COMPANIES else j.company,
                 "title": j.title, "location": j.location, "url": j.url}
                for j in unnotified
            ]
            emailed = send_email(jobs_to_send)
            if emailed:
                mark_notified([j.id for j in unnotified])
            log.info(
                "run_end duration=%.2fs total_new=%d emailed=%d email_sent=%s errors=%d",
                total_duration, len(all_new), len(unnotified), emailed, len(errors),
            )
        else:
            log.info(
                "run_end duration=%.2fs total_new=0 emailed=0 email_sent=false errors=%d",
                total_duration, len(errors),
            )
    else:
        log.info("run_end duration=%.2fs total_new=%d errors=%d", total_duration, len(all_new), len(errors))
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
    p_check.add_argument("--auto", action="store_true", help="Silent mode: email new jobs automatically (for cron)")
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
