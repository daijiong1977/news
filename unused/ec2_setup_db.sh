#!/bin/bash

# EC2 News Pipeline - Complete Setup & Processing Script
# Run this on EC2 server to: rebuild DB, collect articles, process them

set -e

echo "======================================================================"
echo "EC2 NEWS PIPELINE - FULL SETUP & DATA PROCESSING"
echo "======================================================================"
echo ""

# Configuration
WORK_DIR="/var/www/news"
DB_FILE="$WORK_DIR/articles.db"
BACKUP_DB="$WORK_DIR/articles_backup_$(date +%Y%m%d_%H%M%S).db"

cd "$WORK_DIR"

# Step 1: Backup existing database
echo "[1/6] Backing up existing database..."
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DB"
    echo "✓ Backup created: $BACKUP_DB"
else
    echo "✓ No existing database to back up"
fi

# Step 2: Clean/remove old database
echo "[2/6] Cleaning database..."
rm -f "$DB_FILE"
echo "✓ Old database removed"

# Step 3: Rebuild schema
echo "[3/6] Rebuilding database schema..."
python3 << 'DBSCRIPT'
import sys
sys.path.insert(0, '/var/www/news')
exec(open('init_db.py').read())
DBSCRIPT
echo "✓ Database schema created"

# Step 4: Collect articles from RSS feeds
echo "[4/6] Collecting articles from RSS feeds..."
python3 data_collector.py
echo "✓ Articles collected"

# Step 5: Check what was collected
echo "[5/6] Checking collected articles..."
python3 << 'CHECKSCRIPT'
import sqlite3
conn = sqlite3.connect('articles.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM articles')
count = c.fetchone()[0]
c.execute('SELECT id, title, category_id, deepseek_processed FROM articles ORDER BY id')
articles = c.fetchall()
print(f"\n📊 Total articles collected: {count}\n")
for row in articles:
    status = "✓ Processed" if row[3] == 1 else "⏳ Ready"
    print(f"  [{row[0]}] {row[1][:50]}... (Cat: {row[2]}) {status}")
conn.close()
CHECKSCRIPT

# Step 6: Ready for processing
echo ""
echo "[6/6] Setup complete!"
echo ""
echo "======================================================================"
echo "✅ DATABASE READY FOR PROCESSING"
echo "======================================================================"
echo ""
echo "Next steps (on EC2):"
echo ""
echo "1. Export API key:"
echo "   export DEEPSEEK_API_KEY=your_api_key_here"
echo ""
echo "2. Process articles one by one:"
echo "   cd /var/www/news"
echo "   python3 process_one_article.py"
echo "   python3 insert_from_response.py response_article_*.json"
echo ""
echo "3. To process all articles automatically:"
echo "   bash process_all_articles.sh"
echo ""
echo "======================================================================"
