"""
Job Version Classification.

Responsibilities:
- Determine whether a new posting is a repost or an edit.
- Compare content hashes against the latest job version.

Non-Responsibilities:
- No entity resolution.
- No diff generation.

Invariant:
Reposts must still generate a new immutable job_version row.
"""
