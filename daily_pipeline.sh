#!/bin/bash

# Daily News Pipeline - Collect and Process Articles
# Runs every day at 1:00 AM EST
# Collects articles from last 24 hours and processes them with Deepseek

set -e

WORK_DIR="/var/www/news"
cd "$WORK_DIR"

# Source environment variables
source .env
export DEEPSEEK_API_KEY

# Logging
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="${WORK_DIR}/logs/daily_pipeline_${TIMESTAMP}.log"
mkdir -p "${WORK_DIR}/logs"

{
    echo "======================================================================="
    echo "DAILY NEWS PIPELINE - STARTED AT $(date)"
    echo "======================================================================="
    
    # Step 1: Sync latest code from GitHub
    echo ""
    echo "[1/3] Syncing latest code from GitHub..."
    git pull origin main || echo "Warning: git pull encountered issues, continuing..."
    
    # Step 2: Collect articles from last 24 hours
    echo ""
    echo "[2/3] Collecting articles from RSS feeds (last 24 hours)..."
    python3 data_collector.py
    
    # Step 3: Process all unprocessed articles
    echo ""
    echo "[3/3] Processing articles with Deepseek API..."
    bash process_all_articles.sh
    
    echo ""
    echo "======================================================================="
    echo "DAILY NEWS PIPELINE - COMPLETED AT $(date)"
    echo "======================================================================="
    
    # Show summary
    echo ""
    echo "Database Summary:"
    python3 << 'PYSCRIPT'
import sqlite3
c = sqlite3.connect('articles.db').cursor()
total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
processed = c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1').fetchone()[0]
summaries = c.execute('SELECT COUNT(*) FROM article_summaries').fetchone()[0]
print(f"  Total articles: {total}")
print(f"  Processed: {processed}")
print(f"  Summaries: {summaries}")
PYSCRIPT

} 2>&1 | tee "$LOG_FILE"

echo "Log saved to: $LOG_FILE"
