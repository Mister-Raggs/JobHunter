#!/usr/bin/env bash
# Deploy latest changes to VPS.
# Usage: bash scripts/deploy.sh user@your-vps-ip
#
# Assumes:
#   - Git repo is cloned to ~/JobHunter on the VPS
#   - .venv exists at ~/JobHunter/.venv
#   - .env is already present on the VPS (copy once with: scp .env user@vps:~/JobHunter/.env)

set -e

VPS="${1:-}"
if [ -z "$VPS" ]; then
    echo "Usage: bash scripts/deploy.sh user@your-vps-ip"
    exit 1
fi

echo "Deploying to $VPS..."

ssh "$VPS" bash << 'EOF'
set -e
cd ~/JobHunter
echo "→ Pulling latest changes..."
git pull origin main
echo "→ Installing dependencies..."
.venv/bin/pip install -e . -q
echo "✓ Deploy complete"
EOF

echo "Done. Cron job will pick up changes on next run."
