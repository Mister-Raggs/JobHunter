# Job Hunter (MVP Reset)

Clean slate to rebuild Job Hunter with minimal, iterative steps.

## Quick Start

Run the minimal CLI:

```bash
python -m jobhunter.app --version
python -m jobhunter.app
```

## Environment Setup (.env)

Copy the example file and add your Google Custom Search API credentials:

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY and GOOGLE_CSE_ID
```

To get these credentials:
1. **GOOGLE_API_KEY**: Create a project in [Google Cloud Console](https://console.cloud.google.com), enable the Custom Search API, and create an API key.
2. **GOOGLE_CSE_ID**: Create a Custom Search Engine at [https://programmablesearchengine.google.com/](https://programmablesearchengine.google.com/). This is a public search engine that you configure to search specific sites (e.g., Greenhouse, Lever, etc.).

The CLI loads `.env` automatically at startup. Alternatively, you can set env vars in your shell.

## Build Google Search URLs (Dedup-first)

Generate ready-to-paste Google queries targeting ATS job boards:

```bash
python -m jobhunter.app query --roles "data scientist,ml engineer,ai engineer" --remote --days 14
```

This prints one URL per site (default: Greenhouse + Lever + AshbyHQ + Workable). Open them to scan fresh postings fast.

## Fully Automated: Query + Scrape via Google Custom Search

If you want the CLI to fetch Google results and scrape ATS pages automatically, set your Google Custom Search API key and CSE ID, then run:

```bash
export GOOGLE_API_KEY=your_api_key_here
export GOOGLE_CSE_ID=your_cse_id_here
python -m jobhunter.app query-scrape --roles "software engineer,data scientist,machine learning engineer,ai engineer" --remote --days 1 --store data/store.json
```

Or pass them as arguments:

```bash
python -m jobhunter.app query-scrape --roles "software engineer,data scientist,machine learning engineer" --remote --days 1 --api-key YOUR_KEY --cse-id YOUR_CSE_ID --store data/store.json
```

Notes:
- Uses Google Custom Search API (googleapis.com) for Google results.
- Filters for ATS results (Greenhouse/Lever/AshbyHQ/Workable) and ingests them dedup-aware.
- `--days 1` sets Google's date filter to past day.
- Results are capped at 10 per request (Google Custom Search API max).

## Scrape a Single Posting (Greenhouse/Lever/AshbyHQ/Workable)

Parse a posting page and ingest directly:

```bash
python -m jobhunter.app scrape --url "https://boards.greenhouse.io/<company>/jobs/<id>" --store data/store.json
python -m jobhunter.app scrape --url "https://jobs.lever.co/<company>/<slug>" --store data/store.json
python -m jobhunter.app scrape --url "https://jobs.ashbyhq.com/<company>/<slug-or-id>" --store data/store.json
python -m jobhunter.app scrape --url "https://apply.workable.com/<company>/<slug-or-id>" --store data/store.json
```

Note: Provide real URLs (no placeholders). 404s/timeouts are handled with friendly messages.

## Scrape All Postings from a Company Board

Fetch postings from a company's ATS board page and ingest them (dedup-aware):

```bash
python -m jobhunter.app scrape-board --platform greenhouse --company <company-slug> --store data/store.json
python -m jobhunter.app scrape-board --platform lever --company <company-slug> --store data/store.json
python -m jobhunter.app scrape-board --platform ashby --company <company-slug> --store data/store.json
python -m jobhunter.app scrape-board --platform workable --company <company-slug> --store data/store.json
```

Optional: `--limit 20` to cap volume.

## Batch Scrape from a URL List

Create a text file with one URL per line (Greenhouse/Lever), then:

```bash
python -m jobhunter.app scrape-file --input data/urls.txt --store data/store.json
```

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
