#!/usr/bin/env bash
# Simple deploy script for news site
# - Assumes repository has been cloned into the target directory
# - Runs as the deploy user (ec2-user) and restarts a systemd service named `news`

set -euo pipefail

REPO_DIR="/var/www/news"
LOG_DIR="/var/log/news-deploy"
SERVICE_NAME="news"

mkdir -p "$LOG_DIR"
cd "$REPO_DIR"

echo "[$(date --iso-8601=seconds)] Starting deploy in $REPO_DIR" | tee -a "$LOG_DIR/deploy.log"

# Ensure we are on main and up-to-date
git fetch --all --prune
git checkout main
git reset --hard origin/main

# Optional: build or install dependencies here
# Example for Python:
# if [ -f requirements.txt ]; then
#   python3 -m venv venv
#   . venv/bin/activate
#   pip install -r requirements.txt
# fi

echo "[$(date --iso-8601=seconds)] Restarting service: $SERVICE_NAME" | tee -a "$LOG_DIR/deploy.log"
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager | sed -n '1,120p' | tee -a "$LOG_DIR/deploy.log"

echo "[$(date --iso-8601=seconds)] Deploy finished" | tee -a "$LOG_DIR/deploy.log"

exit 0
