#!/bin/bash

# Daily News Pipeline - Collect and Process Articles
# Runs every day at 1:00 AM EST
# Collects articles from last 24 hours and processes them with Deepseek

set -e

WORK_DIR="/var/www/news"
cd "$WORK_DIR"

# Source environment variables from .env if it exists
if [ -f "$WORK_DIR/.env" ]; then
    set -a
    source "$WORK_DIR/.env"
    set +a
fi

# Export API keys and settings (set by bootstrap or .env)
export DEEPSEEK_API_KEY
export EMAIL_API_KEY
export EMAIL_RECIPIENT

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
    
    # Step 4: Check database results
    echo ""
    echo "[CHECK] Database Status:"
    python3 << 'PYSCRIPT'
import sqlite3
c = sqlite3.connect('articles.db').cursor()
total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
processed = c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1').fetchone()[0]
summaries = c.execute('SELECT COUNT(*) FROM article_summaries').fetchone()[0]
keywords = c.execute('SELECT COUNT(*) FROM keywords').fetchone()[0]
questions = c.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
choices = c.execute('SELECT COUNT(*) FROM choices').fetchone()[0]
comments = c.execute('SELECT COUNT(*) FROM comments').fetchone()[0]
background = c.execute('SELECT COUNT(*) FROM background_read').fetchone()[0]
analysis = c.execute('SELECT COUNT(*) FROM article_analysis').fetchone()[0]

print(f"  Total articles: {total}")
print(f"  Processed articles: {processed}")
print(f"  Article summaries: {summaries}")
print(f"  Keywords: {keywords}")
print(f"  Questions: {questions}")
print(f"  Choices: {choices}")
print(f"  Comments: {comments}")
print(f"  Background reading: {background}")
print(f"  Article analysis: {analysis}")
print(f"  Total records: {summaries + keywords + questions + choices + comments + background + analysis}")
PYSCRIPT

    # Step 5: Send email report (if EMAIL_API_KEY is configured)
    if [ -n "$EMAIL_API_KEY" ]; then
        echo ""
        echo "[SEND] Email report..."
        bash send_email_report.sh
    fi

} 2>&1 | tee "$LOG_FILE"

echo "Log saved to: $LOG_FILE"
