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

To enable email alerts, add SMTP credentials to `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
```

For Gmail, generate an [app password](https://myaccount.google.com/apppasswords) instead of using your account password.

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
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password   # Gmail: generate at myaccount.google.com/apppasswords
TO_EMAIL=you@gmail.com        # Where to send job alerts
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
| `salesforce` | Public XML feed | Salesforce |
| `uber` | Internal careers API | Uber |

## Disclaimer

This project is for personal and educational use only. It accesses publicly available job listing data from company careers pages — the same information visible to any browser visitor.

This tool is not affiliated with, endorsed by, or sponsored by any of the companies listed. All company names and trademarks are the property of their respective owners.

Users are solely responsible for ensuring their use of this tool complies with the terms of service of any website they access, as well as applicable local laws and regulations. The author assumes no liability for any misuse or any consequences arising from use of this software.

This software is provided "as is", without warranty of any kind.
