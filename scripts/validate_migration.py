#!/usr/bin/env python3
"""
Validate that database contains same jobs as JSON store.

Usage:
    python scripts/validate_migration.py --json data/store.json --db data/jobs.db
"""

import argparse
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jobhunter.database import Job, get_session


def validate(json_path: Path, db_path: Path):
    """
    Compare JSON store and database contents.

    Returns True if they match, False otherwise.
    """
    # Load JSON data
    print(f"Loading JSON from {json_path}...")
    with open(json_path) as f:
        data = json.load(f)

    json_roles = data.get("roles", {})
    print(f"  JSON: {len(json_roles)} jobs")

    # Load database
    print(f"\nQuerying database at {db_path}...")
    session = get_session(db_path)
    db_jobs = {job.role_id: job for job in session.query(Job).all()}
    print(f"  DB:   {len(db_jobs)} jobs")

    # Compare counts
    if len(json_roles) != len(db_jobs):
        print(f"\n❌ COUNT MISMATCH: JSON has {len(json_roles)}, DB has {len(db_jobs)}")
        return False

    print(f"\n✅ Counts match: {len(json_roles)} jobs in both stores")

    # Check each JSON job exists in DB with matching data
    print("\nValidating job data...")
    mismatches = []
    missing = []

    for role_id, role_data in json_roles.items():
        current = role_data.get("current", {})

        # Check if job exists in DB
        if role_id not in db_jobs:
            missing.append(role_id)
            continue

        db_job = db_jobs[role_id]

        # Compare fields
        fields_to_check = ["company", "title", "location", "url", "source", "source_id"]
        for field in fields_to_check:
            json_value = current.get(field)
            db_value = getattr(db_job, field)

            if json_value != db_value:
                mismatches.append({
                    "role_id": role_id,
                    "field": field,
                    "json": json_value,
                    "db": db_value
                })

    # Report results
    if missing:
        print(f"\n❌ MISSING from DB: {len(missing)} jobs")
        for role_id in missing[:5]:
            print(f"   - {role_id}")
        if len(missing) > 5:
            print(f"   ... and {len(missing) - 5} more")

    if mismatches:
        print(f"\n❌ DATA MISMATCHES: {len(mismatches)} field differences")
        for mismatch in mismatches[:5]:
            print(f"   - {mismatch['role_id']}")
            print(f"     {mismatch['field']}: JSON='{mismatch['json']}' vs DB='{mismatch['db']}'")
        if len(mismatches) > 5:
            print(f"   ... and {len(mismatches) - 5} more")

    if not missing and not mismatches:
        print("✅ All jobs validated successfully!")
        print("   - All role_ids present in database")
        print("   - All fields match between JSON and DB")
        return True

    session.close()
    return False


def main():
    parser = argparse.ArgumentParser(description="Validate migration from JSON to database")
    parser.add_argument("--json", type=Path, default=Path("data/store.json"),
                       help="Path to JSON store file")
    parser.add_argument("--db", type=Path, default=Path("data/jobs.db"),
                       help="Path to SQLite database file")

    args = parser.parse_args()

    if not args.json.exists():
        print(f"❌ JSON file not found: {args.json}")
        sys.exit(1)

    if not args.db.exists():
        print(f"❌ Database file not found: {args.db}")
        sys.exit(1)

    success = validate(args.json, args.db)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
