"""
Cleanup module for removing stale job postings.

Stale jobs are those older than a specified number of days (default: 7).
This prevents the job store from accumulating obsolete listings.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from .logger import get_logger

logger = get_logger()


def cleanup_stale_jobs(store_path: Path, days: int = 7) -> Tuple[int, int]:
    """
    Remove job postings older than the specified number of days.

    Initializes created_at timestamps for existing jobs on first run.
    On subsequent runs, removes jobs where created_at is older than the threshold.

    Args:
        store_path: Path to store.json file
        days: Number of days to keep jobs (default: 7)

    Returns:
        Tuple of (total_jobs_before, total_jobs_after)
        Difference = jobs_removed
    """
    if not store_path.exists():
        logger.debug("Store file does not exist, nothing to clean", extra={"path": str(store_path)})
        return (0, 0)

    try:
        with open(store_path, "r") as f:
            content = f.read().strip()
            if not content:
                logger.debug("Store file is empty, nothing to clean")
                return (0, 0)
            store = json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to read store file for cleanup", extra={"error": str(e), "path": str(store_path)})
        return (0, 0)

    if "roles" not in store:
        logger.debug("Store has no roles, nothing to clean")
        return (0, 0)

    roles = store["roles"]
    total_before = len(roles)

    # Get the cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    logger.debug(
        "Starting stale job cleanup",
        extra={"days": days, "cutoff_date": cutoff_date.isoformat(), "total_jobs": total_before}
    )

    roles_to_remove = []
    jobs_initialized = 0
    jobs_removed = 0

    for role_id, role_data in roles.items():
        if "current" not in role_data:
            continue

        current = role_data["current"]

        # Initialize created_at if missing (first run)
        if "created_at" not in current:
            current["created_at"] = datetime.now().isoformat()
            jobs_initialized += 1
        else:
            # Check if job is stale
            try:
                created_at = datetime.fromisoformat(current["created_at"])
                if created_at < cutoff_date:
                    roles_to_remove.append(role_id)
                    jobs_removed += 1
                    logger.debug(
                        "Marking job for removal (stale)",
                        extra={
                            "role_id": role_id,
                            "company": current.get("company"),
                            "created_at": current["created_at"],
                            "age_days": (datetime.now() - created_at).days,
                        },
                    )
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Invalid created_at timestamp format",
                    extra={"role_id": role_id, "created_at": current.get("created_at"), "error": str(e)},
                )

    # Remove stale jobs
    for role_id in roles_to_remove:
        del roles[role_id]

    # Save updated store
    total_after = len(roles)
    try:
        with open(store_path, "w") as f:
            json.dump(store, f, indent=2)
        logger.info(
            "Cleanup completed",
            extra={
                "jobs_initialized": jobs_initialized,
                "jobs_removed": jobs_removed,
                "jobs_before": total_before,
                "jobs_after": total_after,
            },
        )
    except IOError as e:
        logger.error("Failed to save store after cleanup", extra={"error": str(e), "path": str(store_path)})

    return (total_before, total_after)
