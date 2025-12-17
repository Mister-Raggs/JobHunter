"""
Scoring Logic for Entity Resolution (v1).

Responsibilities:
- Compute a deterministic match score between an incoming job and a candidate job.
- Emit a score breakdown and explanation.

Non-Responsibilities:
- No database access.
- No candidate selection.
- No threshold decisions.

Invariant:
Given identical inputs, this module must always return
the same score and explanation.
"""
