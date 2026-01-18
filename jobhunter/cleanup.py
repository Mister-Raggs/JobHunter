"""
Cleanup module for removing stale job postings.

Stale jobs are those older than a specified number of days (default: 7).
This prevents the job store from accumulating obsolete listings.
"""

from pathlib import Path
from typing import Tuple

from .storage import delete_stale_jobs
from .logger import get_logger

logger = get_logger()


def cleanup_stale_jobs(store_path: Path, days: int = 7) -> Tuple[int, int]:
    """
    Remove job postings older than the specified number of days.

    Args:
        store_path: Path to store file (will derive database path from this)
        days: Number of days to keep jobs (default: 7)

    Returns:
        Tuple of (total_jobs_before, total_jobs_after)
        Difference = jobs_removed
    """
    # Derive database path from store path
    db_path = store_path.parent / "jobs.db"

    try:
        jobs_before, jobs_after = delete_stale_jobs(days=days, db_path=db_path)
        jobs_removed = jobs_before - jobs_after

        logger.info(
            f"Cleanup complete: {jobs_removed} removed, {jobs_after} remaining",
            extra={
                "jobs_before": jobs_before,
                "jobs_removed": jobs_removed,
                "jobs_after": jobs_after,
                "days_threshold": days,
            }
        )

        return (jobs_before, jobs_after)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", extra={"error": str(e), "days": days})
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
