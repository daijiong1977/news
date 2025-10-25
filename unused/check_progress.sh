#!/bin/bash

# Monitor backend processing progress
echo "📊 Checking backend processing status..."
echo ""

ssh -o StrictHostKeyChecking=no -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'EOF'
cd /var/www/news

echo "=== PROCESSING LOG (Last 20 lines) ==="
tail -20 process_output.log
echo ""

echo "=== DATABASE STATUS ==="
python3 -c "
import sqlite3
c = sqlite3.connect('articles.db').cursor()
total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
processed = c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1').fetchone()[0]
print(f'Articles: {processed}/{total} processed')
print()
print('Summary records:', c.execute('SELECT COUNT(*) FROM article_summaries').fetchone()[0])
print('Keywords:', c.execute('SELECT COUNT(*) FROM keywords').fetchone()[0])
print('Questions:', c.execute('SELECT COUNT(*) FROM questions').fetchone()[0])
print('Comments:', c.execute('SELECT COUNT(*) FROM comments').fetchone()[0])
"

EOF
