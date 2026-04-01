#!/usr/bin/env bash
# Sets up a cron job to run jobhunter check --auto every 30 minutes, 6am-8pm UTC.
# Adjust the hour range if your VPS is in a different timezone.
#
# Usage: bash scripts/setup_cron.sh

set -e

JOBHUNTER_BIN="$(which jobhunter 2>/dev/null || echo "")"
if [ -z "$JOBHUNTER_BIN" ]; then
    echo "Error: 'jobhunter' not found in PATH. Make sure you've run: pip install -e ."
    exit 1
fi

# Cron expression: every 30 min, hours 6-20 (6am-8pm UTC)
CRON_EXPR="*/30 6-20 * * * $JOBHUNTER_BIN check --auto >> /var/log/jobhunter.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -qF "jobhunter check --auto"; then
    echo "Cron job already installed:"
    crontab -l | grep "jobhunter"
    exit 0
fi

# Append to existing crontab
(crontab -l 2>/dev/null; echo "$CRON_EXPR") | crontab -

echo "Cron job installed:"
echo "  $CRON_EXPR"
echo ""
echo "JobHunter will check for new jobs every 30 minutes between 6am-8pm UTC."
echo "Logs: /var/log/jobhunter.log"
echo ""
echo "To remove: bash scripts/remove_cron.sh"
