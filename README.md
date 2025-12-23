# Job Hunter (MVP Reset)

Clean slate to rebuild Job Hunter with minimal, iterative steps.

## Quick Start

Run the minimal CLI:

```bash
python -m jobhunter.app --version
python -m jobhunter.app
```

## Ingest a Posting (MVP)

Provide a single JSON posting and persist to a simple store:

```bash
python -m jobhunter.app ingest --input data/sample_posting.json --store data/store.json
```

On first run you'll see `Status: new`. Re-run with changes (e.g., edit `location`), and you'll see `Status: updated` with a list of diffs.

## Next Steps (Short)
- Add ingestion of a single source.
- Normalize a few core fields (title, location).
- Decide role vs posting deterministically for MVP.
- Persist simple state (JSON/SQLite) and show diffs.
