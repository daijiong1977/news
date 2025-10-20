#!/bin/bash

# Send Email Report of Daily Pipeline Results
# Uses the email API at https://emailapi.6ray.com

# Configuration
EMAIL_API_URL="https://emailapi.6ray.com/send-email"
API_KEY="$EMAIL_API_KEY"  # Should be set from environment
RECIPIENT_EMAIL="${1:-jidai@6ray.com}"  # Default recipient, or pass as argument

# Get current database stats
cd /var/www/news

DB_STATS=$(python3 << 'PYSCRIPT'
import sqlite3
c = sqlite3.connect('articles.db').cursor()
total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
processed = c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1').fetchone()[0]
summaries = c.execute('SELECT COUNT(*) FROM article_summaries').fetchone()[0]
keywords = c.execute('SELECT COUNT(*) FROM keywords').fetchone()[0]
questions = c.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
comments = c.execute('SELECT COUNT(*) FROM comments').fetchone()[0]
background = c.execute('SELECT COUNT(*) FROM background_read').fetchone()[0]
analysis = c.execute('SELECT COUNT(*) FROM article_analysis').fetchone()[0]

print(f"Total Articles: {total}")
print(f"Processed: {processed}")
print(f"Summaries: {summaries}")
print(f"Keywords: {keywords}")
print(f"Questions: {questions}")
print(f"Comments: {comments}")
print(f"Background: {background}")
print(f"Analysis: {analysis}")
total_records = summaries + keywords + questions + comments + background + analysis
print(f"Total Records: {total_records}")
PYSCRIPT
)

# Format email body
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
EMAIL_BODY="News Pipeline Report
=====================

Generated: $TIMESTAMP

Database Status:
$DB_STATS

Server: 18.223.121.227
Database: /var/www/news/articles.db

Pipeline Status: ACTIVE
Next Run: Tomorrow at 1:00 AM EST

---
Automated Report from Daily News Pipeline"

# Send email
if [ -z "$API_KEY" ]; then
    echo "ERROR: EMAIL_API_KEY environment variable not set"
    exit 1
fi

RESPONSE=$(curl -s -X POST "$EMAIL_API_URL" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"to_email\": \"$RECIPIENT_EMAIL\",
    \"subject\": \"Daily News Pipeline Report - $TIMESTAMP\",
    \"message\": \"$EMAIL_BODY\",
    \"from_name\": \"News Pipeline\"
  }")

echo "Email Report sent to: $RECIPIENT_EMAIL"
echo "Response: $RESPONSE"
