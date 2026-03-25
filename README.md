# JobHunter

Track new job postings from specific companies. Pulls listings directly from company job boards, stores them in SQLite, and notifies you about new openings.

Currently tracking: **DoorDash**, **Nuro**, **Otter.ai** (Greenhouse), **Apple** (careers page), **Uber** (careers API), **Baseten** (Ashby), **Netflix** (Eightfold), and **CVS Health** (Phenom).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Check all companies for new jobs
python -m jobhunter check

# Check a specific company
python -m jobhunter check -c doordash

# Check and send email notification
python -m jobhunter check -e you@gmail.com

# List all tracked jobs
python -m jobhunter list

# Filter by company
python -m jobhunter list --company apple

# Show configured companies
python -m jobhunter companies

# Show tracking stats
python -m jobhunter stats
```

## Adding a Company

Edit `jobhunter/config.py`:

```python
COMPANIES = {
    "doordash": CompanyConfig(name="DoorDash", scraper="greenhouse", slug="doordashusa"),
    "apple":    CompanyConfig(name="Apple",    scraper="apple",      slug="apple"),
    # Add any Greenhouse-hosted company by slug:
    "discord":  CompanyConfig(name="Discord",  scraper="greenhouse", slug="discord"),
}
```

The `slug` is the company identifier in their job board URL (e.g., `https://job-boards.greenhouse.io/{slug}`).

## Email Notifications

To enable email alerts, add SMTP credentials to `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
```

For Gmail, generate an [app password](https://myaccount.google.com/apppasswords) instead of using your account password.

## Automation

Run on a schedule with cron to get notified about new postings:

```bash
# Check every hour and email new jobs
0 * * * * cd /path/to/JobHunter && .venv/bin/python -m jobhunter check -e you@gmail.com
```

## Project Structure

```
jobhunter/
  app.py              CLI entry point
  config.py           Company definitions
  database.py         SQLite storage + deduplication
  notifier.py         Email notifications
  scrapers/
    greenhouse.py     Greenhouse JSON API (DoorDash, Discord, etc.)
    apple.py          Apple careers page scraper
    ashby.py          Ashby posting API (Baseten, etc.)
    eightfold.py      Eightfold careers API (Netflix, etc.)
    phenom.py         Phenom People careers (CVS Health, etc.)
    uber.py           Uber careers API
```

## Supported Scrapers

| Scraper | Method | Works For |
|---------|--------|-----------|
| `greenhouse` | Public JSON API | Any company on Greenhouse (DoorDash, Cloudflare, Discord, Figma, etc.) |
| `apple` | HTML hydration data | Apple |
| `ashby` | Public posting API | Any company on Ashby (Baseten, etc.) |
| `eightfold` | Public search API | Companies on Eightfold with open API (Netflix, etc.) |
| `phenom` | HTML-embedded JSON (DDO) | Companies on Phenom People (CVS Health, etc.) |
| `uber` | Internal careers API | Uber |
