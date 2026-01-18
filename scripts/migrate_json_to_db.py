#!/usr/bin/env python3
"""
Migrate jobs from JSON store to SQLite database.

Usage:
    python scripts/migrate_json_to_db.py --json data/store.json --db data/jobs.db
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jobhunter.database import Job, init_database, get_session


def parse_timestamp(ts_str):
    """Parse ISO timestamp string, handle missing timestamps."""
    if not ts_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, AttributeError):
        return datetime.now()


def migrate(json_path: Path, db_path: Path, dry_run: bool = False):
    """
    Migrate jobs from JSON to database.

    Args:
        json_path: Path to JSON store file
        db_path: Path to SQLite database file
        dry_run: If True, don't write to database
    """
    # Load JSON data
    print(f"Loading jobs from {json_path}...")
    with open(json_path) as f:
        data = json.load(f)

    roles = data.get("roles", {})
    print(f"Found {len(roles)} jobs in JSON store")

    if dry_run:
        print("\n[DRY RUN] Would migrate the following jobs:")
        for i, (role_id, role_data) in enumerate(list(roles.items())[:5], 1):
            current = role_data.get("current", {})
            print(f"  {i}. {role_id}: {current.get('company')} - {current.get('title')}")
        if len(roles) > 5:
            print(f"  ... and {len(roles) - 5} more")
        return

    # Initialize database
    print(f"\nInitializing database at {db_path}...")
    init_database(db_path)
    session = get_session(db_path)

    # Migrate jobs
    migrated = 0
    skipped = 0
    errors = 0

    for role_id, role_data in roles.items():
        current = role_data.get("current", {})

        # Validate required fields
        required = ["company", "title", "location", "url", "source", "source_id"]
        if not all(current.get(field) for field in required):
            print(f"⚠️  Skipping {role_id}: missing required fields")
            skipped += 1
            continue

        try:
            # Check if job already exists
            existing = session.query(Job).filter_by(role_id=role_id).first()
            if existing:
                print(f"⚠️  Job {role_id} already exists, skipping")
                skipped += 1
                continue

            # Create job record
            created_at = parse_timestamp(current.get("created_at"))
            job = Job(
                role_id=role_id,
                company=current["company"],
                title=current["title"],
                location=current["location"],
                url=current["url"],
                source=current["source"],
                source_id=current["source_id"],
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(job)
            migrated += 1

            if migrated % 20 == 0:
                print(f"  Migrated {migrated} jobs...")

        except Exception as e:
            print(f"❌ Error migrating {role_id}: {e}")
            errors += 1

    # Commit changes
    try:
        session.commit()
        print(f"\n✅ Migration complete!")
        print(f"   Migrated: {migrated}")
        print(f"   Skipped:  {skipped}")
        print(f"   Errors:   {errors}")
    except Exception as e:
        session.rollback()
        print(f"❌ Failed to commit: {e}")
        return False
    finally:
        session.close()

    return True


def main():
    parser = argparse.ArgumentParser(description="Migrate jobs from JSON to database")
    parser.add_argument("--json", type=Path, default=Path("data/store.json"),
                       help="Path to JSON store file")
    parser.add_argument("--db", type=Path, default=Path("data/jobs.db"),
                       help="Path to SQLite database file")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be migrated without writing")

    args = parser.parse_args()

    if not args.json.exists():
        print(f"❌ JSON file not found: {args.json}")
        sys.exit(1)

    migrate(args.json, args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
