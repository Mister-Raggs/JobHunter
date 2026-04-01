#!/usr/bin/env bash
# Removes the jobhunter cron job.

set -e

if ! crontab -l 2>/dev/null | grep -qF "jobhunter check --auto"; then
    echo "No jobhunter cron job found."
    exit 0
fi

crontab -l 2>/dev/null | grep -vF "jobhunter check --auto" | crontab -
echo "Cron job removed."
