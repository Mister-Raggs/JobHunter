"""
Candidate Selection Logic.

Responsibilities:
- Select a bounded set of candidate jobs for comparison.
- Apply hard filters (company_id, role_family, recency).

Non-Responsibilities:
- No scoring.
- No similarity computation.
- No resolution decisions.

Invariant:
Candidate selection must never exclude a valid match.
It may include false positives but never false negatives.
"""
