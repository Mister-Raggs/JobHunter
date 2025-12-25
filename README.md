# Job Hunter

A minimal CLI tool that finds and deduplicates job postings across multiple ATS platforms using Google Custom Search.

## What It Does

Job Hunter searches Google for job postings from 4 major job boards (Greenhouse, Lever, AshbyHQ, Workable), scrapes the posting details, deduplicates them, and stores everything locally in JSON.

Instead of manually checking each job board separately, you run one command and get all fresh postings for your target roles across all platforms at once.

## Quick Start

### 1. Setup Google Custom Search API

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable the "Custom Search API"
3. Create an API key
4. Create a Custom Search Engine at https://programmablesearchengine.google.com/
   - Set it to "Search the entire web" (important!)
5. Note your API key and CSE ID

### 2. Configure Job Hunter

```bash
# Copy the example config
cp .env.example .env

# Edit .env and add your credentials
export GOOGLE_API_KEY=your_api_key_here
export GOOGLE_CSE_ID=your_cse_id_here
```

### 3. Find Jobs

```bash
python -m jobhunter.app query-scrape \
  --roles "software engineer,data scientist" \
  --remote \
  --days 1 \
  --store data/store.json
```

This searches for "software engineer" and "data scientist" roles posted in the last 1 day, filters for remote positions, and saves results to `data/store.json`.

### 4. View Results

```bash
python -m jobhunter.app list --store data/store.json
```

Shows all jobs found with company, title, location, and direct link.

## How It Works

1. **Query Building**: Builds search queries for each role across 4 ATS platforms
2. **Google Search**: Uses Google Custom Search API to find results (no CSE site restrictions needed—filters at API level)
3. **Scraping**: Extracts job title, location, company from each posting's HTML
4. **Deduplication**: Assigns each job a unique ID based on company + source platform + job ID
5. **Storage**: Saves to a simple JSON file; updates on reruns if job details change

## Data Model

Each job is stored with:
- `company`: Normalized company name
- `title`: Job title
- `location`: Work location
- `source`: Which platform (greenhouse, lever, ashby, workable)
- `source_id`: Platform's internal job ID
- `url`: Direct link to the posting

Deduplication prevents the same job from being stored twice, even if found via different searches.

## Limitations & Next Steps

### Current Gaps
- **Cross-platform deduplication**: Same job posted on multiple platforms is stored separately (no merging)
- **No automation**: Requires manual `query-scrape` runs
- **No recommendations**: All jobs listed equally; no ranking by relevance/fit
- **Web interface**: CLI only; no easy browsing interface

### Planned Features
1. **Dedup across platforms**: Detect same job posted on Greenhouse + Lever + etc., merge into one entry
2. **Cron job automation**: Auto-run query-scrape daily/hourly to stay fresh
3. **Web UI**: Simple dashboard to browse jobs, filter by role/company/location
4. **Recommendation system**: Score/rank jobs by fit (skills match, salary, company growth, etc.)
5. **Alerts**: Email/Slack notifications when new jobs matching your profile appear

## Commands

```bash
# Search and scrape (main command)
query-scrape --roles "role1,role2" [--remote] [--days N] [--num RESULTS]

# Just generate search URLs for manual Google searches
query --roles "role1,role2" [--remote] [--days N]

# Scrape a single job URL
scrape --url "https://..."

# Scrape all jobs from a company's board
scrape-board --platform greenhouse --company acme

# View jobs in store
list [--store data/store.json]

# Validate a job posting JSON
validate --input posting.json

# Manually ingest a job posting
ingest --input posting.json
```

## Project Structure

```
jobhunter/
  app.py              # CLI entry point
  google_results.py   # Google Custom Search API client
  normalize.py        # Field canonicalization & dedup logic
  schema.py           # Job posting validation
  storage.py          # JSON store persistence
  search.py           # Query builder
  env.py              # .env loader
  scrapers/           # HTML parsers for each platform
    greenhouse.py
    lever.py
    ashby.py
    workable.py
data/
  store.json          # Local job database (JSON)
```

## API Quotas

Google Custom Search API has a free tier:
- **100 queries/day** (free)
- **10,000 queries/day** (paid)

Each `query-scrape` run makes ~4 queries (one per ATS platform). Plan accordingly or upgrade.


Lines starting with `#` or blank lines are skipped.

## Ingest a Posting from JSON (MVP)

Provide a single JSON posting and persist to a simple store:

```bash
python -m jobhunter.app ingest --input data/sample_posting.json --store data/store.json
```

On first run you'll see `Status: new`. Re-run with changes (e.g., edit `location`), and you'll see `Status: updated` with a list of diffs.

## Validate a Posting

Check a posting JSON against the minimal schema:

```bash
python -m jobhunter.app validate --input data/sample_posting.json
```

If invalid, errors are listed and exit code is non-zero.

## Scrape and Ingest a URL (Greenhouse/Lever)

Parse a posting page and ingest directly:

```bash
python -m jobhunter.app scrape --url "https://boards.greenhouse.io/<company>/jobs/<id>"
python -m jobhunter.app scrape --url "https://jobs.lever.co/<company>/<slug>"
```

Note: This uses simple HTML heuristics; some pages may not parse perfectly yet.

## Next Steps (Short)
- Add ingestion of a single source.
- Normalize a few core fields (title, location).
- Decide role vs posting deterministically for MVP.
- Persist simple state (JSON/SQLite) and show diffs.
