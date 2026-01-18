# Job Hunter: Implementation Tracker

**Last Updated**: January 18, 2026

---

## Project Vision & Goals

**What We Built**: A minimal CLI tool that automates job searching across multiple ATS (Applicant Tracking System) platforms using Google Custom Search API, with built-in deduplication and local storage.

**Core Problem Solved**: Instead of manually visiting each company's job board on different ATS platforms (Greenhouse, Lever, Ashby, Workable), you run one command and get all matching jobs scraped, normalized, and deduplicated.

---

## Implementation Journey

### Phase 1: Clean Slate & MVP Architecture

**Starting Point**: Over-engineered legacy codebase with too many abstractions. Archived and started fresh with a product-first mindset.

**Key Decision**: Build for immediate utility, not future scalability. No ORMs, no complex state machines—just Python + JSON + requests.

**Initial Structure**:
```
jobhunter/
  app.py           # CLI with argparse
  normalize.py     # Field canonicalization
  storage.py       # JSON store (load/save)
  schema.py        # Validation
```

### Phase 2: Core Data Pipeline

**Normalization Layer** (`normalize.py`):
- `normalize_text()`: Lowercase, strip, collapse whitespace
- `normalize_company()`: Standardize company names
- `normalize_title()`: Clean job titles
- `normalize_location()`: Handle remote/hybrid/onsite variants
- `canonical_url()`: Strip query params for deduplication
- `compute_role_id()`: Generate unique ID: `company|source:source_id`

**Deduplication Strategy**:
- Each job gets a role_id based on company + ATS platform + platform's job ID
- Prevents duplicates from same platform
- Doesn't yet merge same job posted on multiple platforms (planned next step)

**Storage** (`storage.py`):
```json
{
  "roles": {
    "acme|greenhouse:12345": {
      "current": {
        "company": "acme",
        "title": "software engineer",
        "location": "remote",
        "url": "https://...",
        "source": "greenhouse",
        "source_id": "12345"
      }
    }
  }
}
```

Initially included history tracking and diffs, but simplified to just store current state for MVP.

### Phase 3: Multi-Platform Scrapers

**Implemented 4 ATS Platform Scrapers**:

1. **Greenhouse** (`scrapers/greenhouse.py`):
   - URL pattern: `https://boards.greenhouse.io/{company}/jobs/{id}`
   - Extracts: Title from `<h1>`, location from class containing "location"
   - Handles: 404s, timeouts, network errors gracefully

2. **Lever** (`scrapers/lever.py`):
   - URL pattern: `https://jobs.lever.co/{company}/{slug}`
   - Similar HTML parsing strategy

3. **AshbyHQ** (`scrapers/ashby.py`):
   - URL pattern: `https://jobs.ashbyhq.com/{company}/{id}`
   - Newer platform, cleaner HTML structure

4. **Workable** (`scrapers/workable.py`):
   - URL pattern: `https://apply.workable.com/{company}/{id}`
   - Sometimes includes subdomain variations

**Scraping Approach**:
- BeautifulSoup4 for HTML parsing
- Heuristic-based extraction (look for `<h1>`, location classes, etc.)
- Returns normalized dict, not raw HTML
- Each scraper has `parse(url)` and `list_company_posting_urls(company_slug)`

**Error Handling Philosophy**:
- Don't crash on individual failures
- Log and skip problematic URLs
- Return user-friendly error messages (not stack traces)

### Phase 4: Google Search Integration

**Initial Approach**: Built `search.py` to generate manual Google search URLs:
```python
build_query(roles, remote_only, days, after, sites)
# Returns: ["site:greenhouse.io software engineer Remote", ...]
```

**API Evolution**:
1. **First attempt**: SearchAPI (searchapi.io) - user had existing key
2. **Pivot**: User wanted Google's official Custom Search JSON API instead
3. **Final implementation**: Google Custom Search API with `siteSearch` parameter filtering

**Google Custom Search Implementation** (`google_results.py`):

```python
def fetch_google_links(query, api_key, cse_id, num=10, days=None, site_search=None):
    params = {
        "key": api_key,           # Google API key
        "cx": cse_id,             # Custom Search Engine ID
        "q": query,               # Search terms
        "num": num,               # Results (max 10 per request)
        "siteSearch": site_search, # Filter to specific domain
        "siteSearchFilter": "i"   # Include only this site
    }
    if days:
        params["dateRestrict"] = f"d{days}"  # e.g., "d1" = past day

    r = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    # Extract URLs from response['items']
```

**Critical CSE Setup**:
- Must configure CSE to "Search the entire web" (not restricted sites)
- Uses `siteSearch` API parameter to filter at query time
- This approach avoids needing to pre-configure ATS sites in CSE

### Phase 5: End-to-End Automation

**Query-Scrape Pipeline** (`cmd_query_scrape` in `app.py`):

1. **Parse role keywords**: Split comma-separated roles
2. **Build base query**: `("software engineer") "Remote"`
3. **Search each ATS site**: 4 parallel Google searches with `siteSearch` filter
4. **Collect all URLs**: Aggregate results (max 10 per site = 40 total)
5. **Scrape each URL**: Route to appropriate platform scraper based on hostname
6. **Ingest & deduplicate**: Compute role_id, check if exists, update or insert
7. **Report results**: Count new/updated/no-change/skipped

**CLI Command**:
```bash
python -m jobhunter.app query-scrape \
  --roles "software engineer,data scientist" \
  --remote \
  --days 1 \
  --num 5 \
  --store data/store.json
```

### Phase 6: Robustness & Polish

**Issues We Solved**:

1. **Empty store.json causes JSON parse error**:
   - Fixed: `load_store()` now checks for empty file, returns default `{"roles": {}}`

2. **Missing optional fields crashed validation**:
   - Made `location` optional in schema
   - Changed validation to return error status instead of raising SystemExit
   - Query-scrape continues on validation errors (logs and skips)

3. **API quota preservation**:
   - Don't exit entire batch on single URL failure
   - Log errors, increment skip counter, continue

4. **Dependency management**:
   - BeautifulSoup4 was missing → added to requirements.txt
   - Used `python -m pip install` to ensure correct environment

5. **CSE configuration debugging**:
   - Discovered user's CSE was restricted to google.com only
   - Guided through reconfiguring to "Search the entire web"
   - Tested `siteSearch` parameter approach

**Environment Setup** (`.env`):
```bash
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

Auto-loaded via `python-dotenv` with fallback manual parser.

---

## Current Status (✅ = Done, 🔄 = In Progress, ⏳ = Planned)

### Core Features
- ✅ Multi-platform scraping (Greenhouse, Lever, Ashby, Workable)
- ✅ Google Custom Search API integration
- ✅ Field normalization and canonicalization
- ✅ Single-platform deduplication
- ✅ JSON-based local storage
- ✅ CLI with multiple commands
- ✅ Error handling and graceful degradation
- ✅ Environment-based configuration
- ✅ Structured logging with metrics
- ✅ Retry logic with exponential backoff
- ✅ Circuit breaker pattern implementation

### Robustness Features (Phase 1)
- ✅ Comprehensive logging across all scrapers
- ✅ Exponential backoff retry on transient failures
- ✅ Platform-level success rate tracking
- ✅ Error categorization and context logging
- ✅ Full test coverage (36 tests passing)
- ✅ Google API call logging and retry

### Commands Available
- ✅ `query-scrape`: Automated search + scrape workflow
- ✅ `query`: Generate Google search URLs
- ✅ `scrape`: Single URL scraping
- ✅ `scrape-board`: Company board crawling
- ✅ `scrape-file`: Batch URL processing
- ✅ `list`: View stored jobs
- ✅ `validate`: Check posting JSON
- ✅ `ingest`: Manual posting ingestion

### Performance Metrics (Latest Run - January 6, 2026)
- **4 ATS sites queried** (Greenhouse, Lever, Ashby, Workable)
- **20 job URLs found** in ~2 seconds
- **15 unique jobs ingested** after deduplication
- **5 errors handled gracefully** (403s, timeouts, 404s)
- **Detailed metrics available** (per-platform success rates, error logs)
```

---

## Technical Architecture

### Technology Stack
- **Language**: Python 3.10+
- **HTTP**: `requests` library
- **HTML Parsing**: `beautifulsoup4`
- **CLI**: `argparse` (stdlib)
- **Config**: `python-dotenv` (env var management)
- **Storage**: JSON (stdlib)
- **Packaging**: `setuptools` with `pyproject.toml`

### File Structure
```
JobHunter/
├── jobhunter/
│   ├── __init__.py         # Version: 0.0.1
│   ├── app.py              # CLI entry point (~393 lines)
│   ├── env.py              # .env loader
│   ├── google_results.py   # Google Custom Search client
│   ├── normalize.py        # Field canonicalization
│   ├── schema.py           # Validation rules
│   ├── search.py           # Query builder (legacy, now simplified)
│   ├── storage.py          # JSON persistence
│   └── scrapers/
│       ├── greenhouse.py
│       ├── lever.py
│       ├── ashby.py
│       └── workable.py
├── data/
│   └── store.json          # Job database
├── .env                     # User credentials (gitignored)
├── .env.example             # Template
├── requirements.txt
├── pyproject.toml
├── README.md
└── TRACKER.md              # This file
```

### Data Flow
```
User Input
  ↓
Query Builder (search.py)
  ↓
Google Custom Search API (google_results.py)
  ↓
[URL, URL, URL, ...] (filtered by ATS domain)
  ↓
Platform Detection (app.py)
  ↓
Platform Scraper (scrapers/*.py)
  ↓
Normalization (normalize.py)
  ↓
Validation (schema.py)
  ↓
Deduplication & Storage (storage.py)
  ↓
data/store.json
```

### Key Design Decisions

1. **JSON over Database**:
   - Simpler deployment (no DB setup)
   - Human-readable/debuggable
   - Git-friendly for tracking changes
   - Easy to export/import

2. **CLI First**:
   - No web server needed
   - Easy to automate (cron jobs)
   - Composable with Unix tools
   - Lower barrier to entry

3. **HTML Scraping over APIs**:
   - Most ATS platforms don't have public APIs
   - Job boards are public HTML pages
   - BeautifulSoup4 handles structure variations well

4. **Normalization Before Storage**:
   - Consistent data format
   - Easier deduplication
   - Better for future features (search, filtering)

5. **Fail-Soft Philosophy**:
   - Log errors, don't crash
   - Preserve API quota on failures
   - Return partial results better than no results

---

## Phase 1 Robustness: Complete ✅ (January 6, 2026)

**What We Implemented**:
- **Structured Logging** (`jobhunter/logger.py`): Centralized logging with metrics tracking (API calls, success rates by platform, error categorization)
- **Retry Logic** (`jobhunter/retry.py`): Exponential backoff decorator, circuit breaker pattern, transient error detection
- **Enhanced Validation** (`jobhunter/schema.py`): Stricter field length bounds, suspicious pattern detection
- **Comprehensive Test Suite** (`tests/`): 36 tests covering logger, retry, and schema validation (100% passing)
- **Full Scraper Integration**: Logging + retry deployed across all 4 ATS scrapers (Greenhouse, Lever, Ashby, Workable)
- **Google API Integration**: Exponential backoff retry on Google Custom Search API calls

**Results**:
```
Test Summary:
- 36 tests passed (logger, retry, validation)
- 41 test cases total
- Exit code: 0

Integration Test (query-scrape):
- 15 new jobs ingested from 20 URLs
- 75% overall success rate
- Platform breakdown:
  * Greenhouse: 1/5 (20%) - some 403s and timeouts
  * Lever: 4/5 (80%) - one 404
  * Ashby: 5/5 (100%)
  * Workable: 5/5 (100%)

Metrics Visible:
- API Calls: 4 (Google Custom Search)
- Scrape attempts tracked per platform
- Detailed error context in logs
```

**Key Files Modified**:
- `jobhunter/scrapers/{greenhouse,lever,ashby,workable}.py`: Added logger, retry decorator, metrics tracking
- `jobhunter/google_results.py`: Added API call logging, retry wrapper, JSON parse error handling
- `jobhunter/app.py`: Already had logger integration and metrics summary output
- `tests/`: Full test suite with fixtures, edge cases, and integration scenarios

**Error Handling Improvements**:
- Timeouts are now retried automatically with exponential backoff
- Transient HTTP errors (5xx) trigger retries
- Permanent failures (404, 403) fail fast with clear logging
- JSON parse errors caught and logged with context

---

## Phase 2: Stale Job Cleanup: Complete ✅ (January 6, 2026)

**Problem Solved**: Job store was accumulating old job postings. Need automatic cleanup to keep only recent relevant jobs.

**What We Implemented**:
- **Stale Job Detection** (`jobhunter/cleanup.py`): Removes jobs older than 7 days (configurable)
- **Timestamp Tracking** (`jobhunter/storage.py`): All new jobs get `created_at` timestamp, preserved on updates
- **Backward Compatibility**: Existing 99 jobs initialized with current timestamp on first run
- **Integration into Pipeline**: Cleanup runs automatically after `query-scrape`
- **Comprehensive Logging**: Detailed metrics (jobs_initialized, jobs_removed, etc.)
- **Test Coverage**: 5 tests covering removal, initialization, edge cases (100% passing)

**How It Works**:
```python
# Every query-scrape run:
1. Scrape new jobs and add to store
2. All jobs get created_at timestamp
3. Cleanup removes jobs older than 7 days
4. User sees removal summary
5. Metrics logged and displayed
```

**Test Results**:
```
Cleanup Test Suite: 5 tests, 100% passing
- Removes stale jobs (>7 days old)
- Initializes missing timestamps
- Handles missing/empty store files
- Preserves recent jobs

Integration Test Results:
- 12 new jobs scraped
- 99 existing jobs initialized with timestamp
- 0 jobs removed (all < 7 days old)
- 111 total jobs in store
- Cleanup metrics logged successfully
```

**Benefits**:
- Store stays clean and focused on relevant jobs
- No manual cleanup needed
- Timestamps enable future filtering/sorting features
- Automatic & transparent process

---

## Phase 3: Code Quality & Refactoring ✅ (January 18, 2026)

**Goal**: Simplify codebase to make it more approachable and maintainable before adding more features.

### Round 1: Extracted Helper Functions in `app.py`
**Problem**: Command functions had duplicated scraper selection logic (~60 lines across 5 functions)

**Solution**:
- Added `get_scraper_for_url(url)`: Single source of truth for URL→scraper mapping
- Added `get_scraper_by_platform(platform)`: Platform name→scraper mapping  
- Added `parse_roles(roles_str)`: Comma-separated role parsing

**Impact**: Eliminated duplication in `cmd_query_scrape`, `cmd_scrape`, `cmd_scrape_file`, `cmd_scrape_board`, and `cmd_query`

### Round 2: Shared Utilities for Scrapers
**Problem**: All 4 scrapers (Greenhouse, Lever, Ashby, Workable) had ~40 lines of identical HTTP error handling code per scraper, appearing twice in each (in `parse()` and `list_company_posting_urls()`). Total duplication: ~320 lines.

**Solution**: Created `jobhunter/scrapers/common.py` with shared utilities:
- `fetch_with_error_handling(url, platform)`: Standardized HTTP request with logging, retry, and error handling
- `deduplicate_urls(urls)`: Order-preserving URL deduplication
- Centralized `_fetch_with_retry()` with exponential backoff

**Changes**:
- Refactored all 4 scrapers to use shared utilities
- Fixed missing `jobhunter/scrapers/__init__.py` (scrapers weren't importable as package)
- Updated test execution to use `PYTHONPATH=.` for imports

**Results**:
```
Before → After (line counts):
- greenhouse.py: 128 → 98 lines (-30)
- lever.py:      129 → 104 lines (-25)
- ashby.py:      121 → 79 lines (-42)
- workable.py:   125 → 78 lines (-47)
- common.py:     NEW → 60 lines (shared code)

Net reduction: ~144 lines eliminated
Test status: All 41 tests passing
```

**Benefits**:
- **Single source of truth**: Change error handling once, affects all scrapers
- **Easier maintenance**: Adding new scrapers is simpler with utilities
- **Better readability**: Scrapers now focus on parsing logic, not error handling
- **No functionality lost**: All tests pass, same behavior guaranteed

---

## Roadmap: What's Next

### Phase 4: Database Migration (SQL with Prisma)

**Next Steps**:
1. Set up Prisma schema with SQLite (or PostgreSQL)
2. Migrate 111+ jobs from JSON to database
3. Update storage.py to use Prisma instead of JSON
4. Same cleanup logic but with SQL queries

### Phase 5: Web UI

**Next Steps**:
1. Build FastAPI backend for REST endpoints
2. Create responsive HTML/CSS/JS frontend
3. Features: search, filter by company/location/platform, sort by date
4. Add `ui` command to launch web server

---

## Updated Strategy (January 3, 2026): Reality-Based Custom Site Scraping

After analyzing actual custom career pages (Meta, Apple, etc.), we discovered that initial assumptions about JSON-LD and simple HTML parsing were incorrect. Modern career sites use:
- **React SPAs** with client-side rendering (Meta)
- **Internal APIs** (GraphQL/REST) that aren't publicly documented
- **Obfuscated class names** and dynamic content

**New Approach - 4-Tier Fallback Strategy**:
1. **API Direct**: Try to discover public APIs first (fastest, most reliable)
2. **API Intercept**: Use headless browser to capture network calls and extract data
3. **HTML SSR**: Parse server-side rendered content (for simpler sites)
4. **Browser Render**: Full automation with element extraction (slowest, last resort)

Each company's successful strategy will be learned and cached to optimize future scrapes. This pragmatic approach acknowledges that custom sites require investigation before implementation.

---

### Priority 1: Cross-Platform Deduplication

**Problem**: Same job posted on Greenhouse + Lever is stored as 2 separate entries.

**Solution**:
- Fuzzy matching on `company + title + location`
- Link related postings: `{"role_id": "acme|primary", "related": ["acme|greenhouse:123", "acme|lever:456"]}`
- Show as single job with multiple application links

**Implementation**:
- Add `find_similar_roles(store, posting)` in `storage.py`
- Use string similarity (Levenshtein distance) or embeddings
- Merge strategy: keep newest posting as primary, link others

**Effort**: Medium (2-3 days)

### Priority 2: Automated Cron Jobs

**Problem**: Currently requires manual `query-scrape` runs.

**Solution**:
- Add `schedule.py` with configurable intervals
- Store last run timestamp
- Support different schedules per role query

**Implementation Options**:
```python
# Option A: Built-in scheduler
python -m jobhunter.app daemon --interval 3600  # Run every hour

# Option B: System cron
0 */3 * * * cd /path && python -m jobhunter.app query-scrape ...

# Option C: GitHub Actions (CI/CD)
# Run on schedule, commit store.json changes
```

**Features**:
- Configurable queries in config file
- Email/Slack notifications on new jobs
- Error alerting if scraping fails

**Effort**: Small-Medium (1-2 days)

### Priority 3: Web UI

**Problem**: CLI is powerful but not browsable. Hard to explore jobs visually.

**Solution**: Simple web dashboard for browsing stored jobs.

**Tech Stack Options**:
- **Minimal**: Flask + Jinja templates
- **Modern**: FastAPI + React/Vue
- **Fastest**: Static site generator (Hugo/Jekyll) from store.json

**Features**:
- Table view with sortable columns
- Filters: company, location, date added, platform
- Search: full-text across title/description
- Detail view: full job posting with apply link
- Export: CSV, markdown, email digest

**UI Mockup**:
```
┌─────────────────────────────────────────────────┐
│ Job Hunter                    🔍 [search box]   │
├─────────────────────────────────────────────────┤
│ Filters: [All Platforms ▼] [Remote ☑] [+More]  │
├─────────────────────────────────────────────────┤
│ Company         │ Title              │ Location │
├─────────────────┼────────────────────┼──────────┤
│ Acme Corp       │ Senior SWE         │ Remote   │
│ Beta Inc        │ ML Engineer        │ NYC      │
│ ...                                              │
└─────────────────────────────────────────────────┘
```

**Effort**: Medium-Large (3-5 days)

### Priority 4: Recommendation System

**Problem**: All jobs shown equally, no relevance ranking.

**Solution**: Score/rank jobs by fit based on user profile.

**Scoring Factors**:
- **Skills match**: Parse job description, compare with user's skill set
- **Seniority match**: Junior/Mid/Senior in title vs. user level
- **Location preference**: Remote > hybrid > onsite priority
- **Company quality**: Glassdoor rating, funding stage, growth rate
- **Salary estimate**: Infer from title/location/company
- **Freshness**: Newer postings ranked higher
- **Application velocity**: How fast position is being filled

**Implementation Approach**:
```python
def score_job(job: dict, user_profile: dict) -> float:
    score = 0.0

    # Skills match (TF-IDF or embedding similarity)
    if job_description:
        skills_score = compute_skill_overlap(job_description, user_profile['skills'])
        score += skills_score * 0.4

    # Seniority match
    job_level = extract_seniority(job['title'])
    if job_level == user_profile['target_level']:
        score += 0.2

    # Location preference
    if 'remote' in job['location'].lower() and user_profile['remote_only']:
        score += 0.2

    # Recency (decay over time)
    days_old = (now - job['first_seen']).days
    recency_score = 1.0 / (1 + days_old/7)
    score += recency_score * 0.2

    return score
```

**User Profile** (new file: `profile.yaml`):
```yaml
skills:
  - Python
  - Machine Learning
  - AWS
target_level: senior
remote_only: true
locations:
  - San Francisco
  - Remote
excluded_companies:
  - company_to_avoid
```

**UI Integration**:
- Jobs sorted by score by default
- "Why this job?" explanation (which factors contributed)
- Feedback loop: "Not interested" → improve future rankings

**Effort**: Large (5-7 days)

### Priority 5: Additional Enhancements

**Job Descriptions** (⏳):
- Currently not stored (save HTML or extract text)
- Enables full-text search and better skill matching
- Effort: Small (1 day)

**Change Tracking** (⏳):
- Detect when job title/location/description changes
- Alert if job becomes remote or salary range increases
- Effort: Small (1 day)

**Application Tracking** (⏳):
- Mark jobs as "applied", "interviewing", "rejected"
- Integrate with email to auto-track application status
- Effort: Medium (2-3 days)

**Multi-User Support** (⏳):
- Each user has own store.json + profile
- Share job discoveries within team
- Effort: Medium (2-3 days)

**More ATS Platforms** (⏳):
- SmartRecruiters
- Workday
- BambooHR
- JazzHR
- Breezy HR
- Effort: Small per platform (0.5 days each)

**Export Options** (⏳):
- Weekly email digest of new jobs
- Slack/Discord bot integration
- RSS feed generation
- Zapier webhook on new jobs
- Effort: Small-Medium (1-2 days)

---

## API Quotas & Costs

**Google Custom Search API**:
- **Free tier**: 100 queries/day
- **Paid tier**: $5/1000 queries (max 10,000/day)

**Usage Calculation**:
- Each `query-scrape` run = 4 queries (one per ATS site)
- Running 3x/day = 12 queries/day (well within free tier)
- Running hourly = 96 queries/day (still within free tier)
- More aggressive schedules require paid tier

**Cost Optimization Ideas**:
- Cache results for short period (1 hour)
- Only re-query sites with new postings
- Use `start` parameter to paginate beyond 10 results per site

---

## Development Workflow

**Current Process**:
1. Edit code in `jobhunter/`
2. Test with `python -m jobhunter.app ...`
3. Check `data/store.json` for results
4. Git commit changes
5. Git push to remote

**Testing Strategy**:
- Manual testing via CLI (no automated tests yet)
- Validate scrapers against live URLs
- Check store.json structure after runs

**Suggested Improvements**:
- Add `tests/` directory with pytest
- Mock HTTP requests for scraper tests
- CI/CD pipeline to run tests on push
- Pre-commit hooks for code formatting (black, isort)

---

## Known Issues & Limitations

### Current Limitations

1. **No cross-platform deduplication**: Same job on multiple ATS platforms creates duplicates
2. **Missing job descriptions**: Only title, location, company stored (no full text)
3. **No change history**: Overwrites job data on updates (no timeline)
4. **CLI only**: No web interface for browsing
5. **Manual execution**: Requires running commands manually (no automation)
6. **No filtering after retrieval**: Can't filter stored jobs without re-running query
7. **No application tracking**: Can't mark jobs as applied/rejected
8. **Google API dependency**: Requires CSE setup + API key

### Known Bugs

- ✅ Empty store.json causes JSON parse error (FIXED)
- ✅ Missing location field crashes validation (FIXED)
- ✅ Validation errors exit entire batch (FIXED)
- Workable source_id extraction sometimes gets "j" instead of actual ID (minor)
- Lever timeout occasionally prevents results (transient network issue)

### Technical Debt

- `search.py` still has legacy `build_query()` function (could simplify)
- No unit tests (all manual testing)
- No logging framework (just print statements)
- No configuration file (all CLI args)
- Scrapers have duplicate code (could extract common patterns)

---

## Success Metrics

### Current Performance
- **Query time**: ~2 seconds per ATS site (8 seconds total)
- **Scraping speed**: ~0.5 seconds per URL
- **Storage size**: ~2KB per job (~26KB for 13 jobs)
- **Error rate**: <5% (mostly timeouts/network issues)

### Target Goals
- **Coverage**: 80%+ of relevant jobs found (vs manual search)
- **Accuracy**: 95%+ of scraped data correct
- **Freshness**: Jobs appear within 1 hour of posting (with hourly cron)
- **Deduplication**: <2% false negatives (same job marked as different)

---

## Learning & Takeaways

### What Worked Well
- Starting with minimal scope and iterating
- JSON storage for rapid prototyping
- Graceful error handling from day 1
- Google Custom Search API (reliable, well-documented)
- BeautifulSoup for HTML parsing (flexible, forgiving)

### What Was Challenging
- CSE configuration confusion (restricted vs. entire web)
- API evolution (SearchAPI → Google Custom Search)
- Empty file edge cases (JSON parsing)
- Scraper heuristics (every ATS has slightly different HTML)

### Key Lessons
1. **Start simple, iterate**: Don't over-engineer upfront
2. **Graceful degradation > perfection**: Log and skip errors
3. **User-guided tech choices**: Use existing resources (API keys)
4. **Good errors = good UX**: Clear messages > stack traces
5. **Documentation matters**: Future you will thank present you

---

## Next Milestone Decision Points

**Option A - Automation Focus**:
1. Set up cron job to run query-scrape daily
2. Add email notifications for new jobs
3. Deploy to always-on server (DigitalOcean, Heroku, etc.)

**Option B - Intelligence Focus**:
1. Implement cross-platform deduplication
2. Build basic recommendation scoring
3. Add user profile support

**Option C - UI Focus**:
1. Build simple Flask web UI
2. Add filtering and search
3. Deploy as web app for easier access

**Recommended Next Steps**: Start with **Option B** (Intelligence Focus) to improve data quality, then move to **Option A** (Automation) for convenience, and finally **Option C** (UI) for accessibility.

---

## Changelog

### v0.0.1 - Initial Release (December 24, 2025)
- ✅ Core CLI with 8 commands
- ✅ 4 ATS platform scrapers (Greenhouse, Lever, Ashby, Workable)
- ✅ Google Custom Search API integration
- ✅ JSON-based storage with deduplication
- ✅ Field normalization and validation
- ✅ Error handling and graceful degradation
- ✅ Environment-based configuration

### v0.0.2 - Robustness Improvements (January 3, 2026)
- ✅ Fixed empty store.json parsing error
- ✅ Made location field optional in schema
- ✅ Changed validation to non-blocking (returns error status)
- ✅ Improved error messages for user clarity
- ✅ Added detailed documentation (README + TRACKER)

### Future Versions
- v0.1.0: Cross-platform deduplication
- v0.2.0: Cron job automation + notifications
- v0.3.0: Web UI (Flask/FastAPI)
- v0.4.0: Recommendation system + user profiles
- v1.0.0: Production-ready with all core features

---

**End of Tracker** | Last updated: January 3, 2026
