#!/bin/bash

# EC2 News Pipeline - Process All Articles
# Automatically processes all unprocessed articles

set -e

WORK_DIR="/var/www/news"
cd "$WORK_DIR"

# Check if API key is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ Error: DEEPSEEK_API_KEY not set"
    echo "Run: export DEEPSEEK_API_KEY=your_key_here"
    exit 1
fi

echo "======================================================================"
echo "EC2 NEWS PIPELINE - PROCESS ALL ARTICLES"
echo "======================================================================"
echo ""

# Get count of unprocessed articles
UNPROCESSED=$(python3 << 'SCRIPT'
import sqlite3
conn = sqlite3.connect('articles.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=0')
count = c.fetchone()[0]
conn.close()
print(count)
SCRIPT
)

if [ "$UNPROCESSED" -eq 0 ]; then
    echo "✓ All articles already processed!"
    exit 0
fi

echo "📊 Found $UNPROCESSED unprocessed articles"
echo ""

# Process each article
COUNTER=0
while [ "$COUNTER" -lt "$UNPROCESSED" ]; do
    COUNTER=$((COUNTER + 1))
    echo "Processing article $COUNTER of $UNPROCESSED..."
    echo ""
    
    # Generate response
    echo "[Step 1] Generating API response..."
    python3 process_one_article.py
    
    # Get latest response file
    RESPONSE=$(ls -t response_article_*.json 2>/dev/null | head -1)
    
    if [ -z "$RESPONSE" ]; then
        echo "❌ Error: Response file not generated"
        break
    fi
    
    echo "[Step 2] Inserting into database..."
    python3 insert_from_response.py "$RESPONSE"
    
    # Clean up response file
    rm "$RESPONSE"
    
    echo "✓ Article $COUNTER processed successfully"
    echo ""
    
    # Wait a bit before next article to avoid rate limiting
    if [ "$COUNTER" -lt "$UNPROCESSED" ]; then
        echo "⏳ Waiting 5 seconds before next article..."
        sleep 5
    fi
done

echo "======================================================================"
echo "✅ PROCESSING COMPLETE!"
echo "======================================================================"
echo ""

# Show final statistics
python3 << 'SCRIPT'
import sqlite3
conn = sqlite3.connect('articles.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1')
processed = c.fetchone()[0]

tables = {
    'article_summaries': 'Summaries',
    'keywords': 'Keywords',
    'questions': 'Questions',
    'choices': 'Choices',
    'comments': 'Comments/Perspectives',
    'background_read': 'Background Reading',
    'article_analysis': 'Analysis'
}

print("📈 Final Database Statistics:\n")
print(f"  Articles processed: {processed}\n")
print("  Data by table:")
for table, label in tables.items():
    c.execute(f'SELECT COUNT(*) FROM {table}')
    count = c.fetchone()[0]
    print(f"    {label}: {count}")

conn.close()
SCRIPT

echo ""
echo "======================================================================"
