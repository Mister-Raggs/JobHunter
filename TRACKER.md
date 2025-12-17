# JobHunter

A comprehensive job tracking and analysis system designed to discover, parse, and manage job postings from various Applicant Tracking Systems (ATS).

## Project Phases

### PHASE 1 — Architecture & Data Modeling (What we're doing now)
- ☑ High-level system architecture
- ☑ Core entities (Job, JobVersion, URL, Company)
- ☐ Finalize database choice (Postgres + pgvector)
- ☐ Define schema (DDL)
- ☐ Decide raw HTML storage strategy (filesystem vs object store)
- ☐ Define data contracts between components

**Deliverable:** Architecture diagram, Schema doc, README "System Overview"

### PHASE 2 — URL Discovery & Crawl Management
- ☐ Define search seed format (ATS domain, query string, discovery timestamp)
- ☐ Implement URL deduplication (hash or unique index, first_seen / last_seen)
- ☐ Implement crawl runs tracking (run_id, counts, errors)
- ☐ Handle robots / rate limits (basic)

**Deliverable:** URL ingestion pipeline, crawl_runs table populated

### PHASE 3 — Page Fetching (Crawler)
- ☐ Implement fetcher abstraction (requests-based, Playwright-based)
- ☐ Handle JS-rendered pages (Workday, Google Careers)
- ☐ Store raw HTML snapshots (reference path in DB)
- ☐ Implement retry + timeout logic

**Deliverable:** Reliable page fetcher, Raw HTML archive

### PHASE 4 — Normalization & Parsing
- ☐ Build ATS-specific parsers (Greenhouse parser, Lever parser)
- ☐ Extract canonical fields (title, company, location, description, requirements, team, external job ID)
- ☐ Normalize text (whitespace, casing, punctuation)
- ☐ Validate parsed content

**Deliverable:** Structured job payload per page

### PHASE 5 — Entity Resolution (CORE LOGIC)
- ☐ Candidate job selection logic (company, role_family, recency window)
- ☐ Implement hard identifier matching (external job ID, canonical URL)
- ☐ Implement strong signal matching (title + location, high similarity)
- ☐ Implement scoring-based resolution (v1) (weighted rules, thresholds)
- ☐ Log resolution decisions

**Deliverable:** Deterministic entity resolution function, Resolution audit trail

### PHASE 6 — Versioning & History Tracking
- ☐ Insert immutable job_versions
- ☐ Track first_seen / last_seen per job
- ☐ Maintain URL reuse stats
- ☐ Detect content changes (hash diff, section-level diffs)

**Deliverable:** Full job history preserved

### PHASE 7 — Repost Detection & Freshness Scoring
- ☐ Define repost vs new criteria
- ☐ Compare against historical versions
- ☐ Compute confidence score
- ☐ Generate explanation string
- ☐ Store repost_analysis records

**Deliverable:** Repost classification with confidence

### PHASE 8 — Semantic Similarity (ML Layer)
- ☐ Choose embedding model (sentence-transformers)
- ☐ Generate embeddings
- ☐ Store in pgvector
- ☐ Cosine similarity search
- ☐ Tune similarity thresholds

**Deliverable:** Robust detection of lightly edited reposts

### PHASE 9 — Ranking & Prioritization
- ☐ Define "apply now" score (freshness, repost confidence, company behavior)
- ☐ Sort jobs by urgency
- ☐ Filter: new only, low repost confidence

**Deliverable:** Ranked job feed

### PHASE 10 — Output Interfaces
- ☐ CLI interface (new jobs, last N days, confidence threshold)
- ☐ Simple dashboard (optional) (tables, filters)
- ☐ Alerting (optional) (email / Slack / local notification)

**Deliverable:** Usable daily workflow

### PHASE 11 — Evaluation & Metrics (Very Important)
- ☐ Define evaluation set (manually labeled reposts vs new)
- ☐ Measure: false positives, false negatives, precision on "new"
- ☐ Iterate thresholds

**Deliverable:** Evaluation report

### PHASE 12 — Polish for Resume & Interviews
- ☐ Clean README (problem, design, tradeoffs)
- ☐ Architecture diagram
- ☐ Example explanations
- ☐ Metrics & improvements
- ☐ Write resume bullets
