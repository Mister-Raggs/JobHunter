# Job Discovery Platform

A production-style system for crawling, deduplicating, and tracking job postings over time, with a focus on **entity resolution**, **repost detection**, and **explainable decision-making**.

This project explores real-world challenges in data engineering, applied ML, and systems design for large-scale job aggregation platforms.

## 🚀 Core Goals

- Identify whether a job posting is **new**, **edited**, or a **repost**
- Deduplicate postings across ATS platforms (Greenhouse, Lever, Workday, etc.)
- Track job lifecycle changes over time
- Provide explainable, auditable entity resolution decisions
- Support safe backfills and logic upgrades without data loss

## 🧠 High-Level Architecture

The system is organized into **three immutable-to-derived layers**:
```
Raw Job Pages (immutable)
         ↓
Normalized Job Pages (deterministic)
         ↓
Jobs + Job Versions (derived, re-computable)
```

**Key Design Principle:**
> Raw data is immutable. All higher-level entities are reproducible.

This design allows safe re-running of entity resolution logic as it evolves.

## 🧩 Major Components

### 1. Ingestion
- Crawl job postings from ATS platforms
- Store raw HTML and metadata immutably

### 2. Normalization
- Extract canonical fields (title, location, seniority, text)
- Generate embeddings for semantic comparison
- Fully deterministic and reproducible

### 3. Entity Resolution
- Determine whether an incoming posting maps to an existing job
- Use a rule-based, explainable scoring model (v1)
- Conservative by default to avoid accidental merges

### 4. Versioning
- Model a job as a long-lived entity
- Each posting appearance is stored as an immutable version
- Explicitly detect reposts vs edits

### 5. Backfill & Reprocessing
- Full rebuilds
- Scoped reprocessing (by company, date, or ATS)
- Incremental forward-only processing

## 📁 Repository Structure
```
pipelines/
  ingest/              # Crawling & raw ingestion
  normalize/           # Deterministic normalization
  entity_resolution/   # Candidate selection & scoring
  versioning/          # Repost vs edit logic
  backfill/            # Full & partial reprocessing
  ranking/             # Freshness & relevance scoring

storage/
  repositories/        # Database access only
  migrations/          # Schema evolution

models/
  embeddings/          # Text embedding & caching
  ml/                  # Future ML-based resolution

evaluation/
  labeling/            # Hand-labeled job pairs
  metrics.py           # Precision/recall analysis

docs/
  architecture.md
  entity_resolution.md
  schema.md
```

## 🔍 Entity Resolution (v1)

Entity resolution uses a **deterministic scoring model** combining:

- Hard identifiers (ATS job IDs, canonical URLs)
- Structural similarity (title, location, seniority)
- Semantic similarity (text embeddings)
- Conflict penalties (team, location, seniority mismatches)

Each decision produces:
- A score
- A confidence level
- A human-readable explanation

This design allows safe iteration and future ML upgrades.

## 🔁 Backfills & Reproducibility

Supports:
- Full historical rebuilds
- Scoped reprocessing (by company, date, ATS)
- Incremental production updates

All derived data can be regenerated from raw inputs.

## 📊 Evaluation & Future Work

- Offline evaluation using labeled job pairs
- Transition from rule-based scoring → ML classifier
- Improved crawl scheduling & freshness heuristics
- Ranking jobs by novelty rather than repost frequency

## 🧪 Status

This project is under active development and structured to resemble production data platforms used in industry.