# JobHunter

Track new job postings from specific companies. Pulls listings directly from company job boards, stores them in SQLite, and notifies you about new openings.

Currently tracking: **DoorDash**, **Nuro**, **Otter.ai**, **CoreWeave**, **Glean** (Greenhouse), **Apple** (careers page), **Uber** (careers API), **Baseten**, **Braintrust** (Ashby), **Netflix** (Eightfold), **CVS Health** (Phenom), **Salesforce** (XML feed), and **Qualcomm** (Playwright + Eightfold API).

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

Email is sent via [Resend](https://resend.com) (free tier: 3,000 emails/month). Add credentials to `.env`:

```
RESEND_API_KEY=re_xxxxxxxxxxxx   # API key from resend.com
FROM_EMAIL=you@yourdomain.com    # Must be a verified sender in Resend
TO_EMAIL=you@gmail.com           # Where to receive alerts
```

## Automation (VPS Deployment)

For reliable 24/7 scheduling, deploy to a VPS (Hetzner, DigitalOcean, etc. — ~$4/mo).

### First-time VPS setup

```bash
# On the VPS
git clone https://github.com/your-username/JobHunter.git
cd JobHunter
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/playwright install chromium
.venv/bin/playwright install-deps chromium  # Ubuntu system deps

# Copy credentials from local machine (run this locally)
scp .env user@your-vps-ip:~/JobHunter/.env

# Install the cron job (on VPS)
bash scripts/setup_cron.sh
```

The cron job runs `jobhunter check --auto` every 30 minutes between 6am–8pm. It emails new jobs automatically and marks them so you only get notified once.

### Credentials (.env)

```
RESEND_API_KEY=re_xxxxxxxxxxxx
FROM_EMAIL=you@yourdomain.com
TO_EMAIL=you@gmail.com
```

The `.env` file lives only on the VPS — never commit it.

### Deploying updates

After adding a new company or making changes locally:

```bash
git push origin main
bash scripts/deploy.sh user@your-vps-ip
```

### Validating before deploying

```bash
# Test the new company locally first
jobhunter check -c <new_company_key>

# Run twice — second run should show 0 new jobs (dedup check)
jobhunter check -c <new_company_key>

# Test email manually
jobhunter check -c <new_company_key> -e you@email.com
```

## Testing

```bash
pip install -e ".[dev]"

# Unit tests — no network, runs instantly
pytest tests/test_database.py -v

# Integration tests — hits live APIs (~30s)
pytest tests/test_scrapers.py -v -m "not slow"

# All tests including slow ones (Netflix Eightfold)
pytest -v
```

## Project Structure

```
jobhunter/
  app.py              CLI entry point
  config.py           Company definitions
  database.py         SQLite storage + deduplication
  logger.py           Structured logging setup
  notifier.py         Email notifications (Resend)
  scrapers/
    greenhouse.py     Greenhouse JSON API (DoorDash, Glean, etc.)
    apple.py          Apple careers page scraper
    ashby.py          Ashby posting API (Baseten, Braintrust)
    eightfold.py      Eightfold careers API (Netflix)
    phenom.py         Phenom People careers (CVS Health)
    qualcomm.py       Qualcomm (Playwright + pcsx API)
    salesforce.py     Salesforce XML feed
    uber.py           Uber careers API
scripts/
  setup_cron.sh       Install cron job on VPS
  remove_cron.sh      Remove cron job
  deploy.sh           Deploy latest changes to VPS
tests/
  test_database.py    Unit tests for DB layer
  test_scrapers.py    Integration tests for scrapers
```

## Supported Scrapers

| Scraper | Method | Works For |
|---------|--------|-----------|
| `greenhouse` | Public JSON API | Any company on Greenhouse (DoorDash, Cloudflare, Discord, Figma, etc.) |
| `apple` | HTML hydration data | Apple |
| `ashby` | Public posting API | Any company on Ashby (Baseten, etc.) |
| `eightfold` | Public search API | Companies on Eightfold with open API (Netflix, etc.) |
| `phenom` | HTML-embedded JSON (DDO) | Companies on Phenom People (CVS Health, etc.) |
| `salesforce` | Public XML feed | Salesforce |
| `uber` | Internal careers API | Uber |

## Disclaimer

This project is for personal and educational use only. It accesses publicly available job listing data from company careers pages — the same information visible to any browser visitor.

This tool is not affiliated with, endorsed by, or sponsored by any of the companies listed. All company names and trademarks are the property of their respective owners.

Users are solely responsible for ensuring their use of this tool complies with the terms of service of any website they access, as well as applicable local laws and regulations. The author assumes no liability for any misuse or any consequences arising from use of this software.

This software is provided "as is", without warranty of any kind.
