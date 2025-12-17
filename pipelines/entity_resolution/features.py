"""
Feature Extraction for Entity Resolution.

Responsibilities:
- Compute individual similarity and conflict features.
- Normalize and compare fields (title, location, seniority, text).

Non-Responsibilities:
- No weighting logic.
- No threshold logic.
- No persistence.

Invariant:
Missing data must never be treated as a mismatch.
"""
