"""
Full Backfill Pipeline.

Responsibilities:
- Recompute all derived entities from normalized job pages.
- Ensure deterministic, ordered replay by fetched_at.

Non-Responsibilities:
- No crawling.
- No normalization logic.

Invariant:
A full rebuild must be idempotent and reproducible.
"""
