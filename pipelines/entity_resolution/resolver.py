"""
Entity Resolution Orchestrator.

Responsibilities:
- Coordinate candidate selection.
- Invoke scoring logic.
- Apply decision thresholds.
- Return an explainable resolution result.

Non-Responsibilities:
- No database access.
- No feature computation.
- No mutation of persistent state.

Invariant:
This module must be deterministic given the same inputs.
"""
