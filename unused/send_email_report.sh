#!/bin/bash

# Send Email Report of Daily Pipeline Results
# Uses the email API at https://emailapi.6ray.com

# Determine working directory (support both EC2 /var/www/news and local development)
WORK_DIR="${1:-.}"
if [ -d "/var/www/news" ]; then
    WORK_DIR="/var/www/news"
elif [ -d "/Users/jidai/news" ]; then
    WORK_DIR="/Users/jidai/news"
else
    WORK_DIR="."
fi

cd "$WORK_DIR" || exit 1

# Load environment variables if available
if [ -f "$WORK_DIR/.env" ]; then
    set -a
    source "$WORK_DIR/.env"
    set +a
    export DEEPSEEK_API_KEY
    export EMAIL_API_KEY
    export EMAIL_RECIPIENT
fi

# Ensure EMAIL_RECIPIENT has a default
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-jidai@6ray.com}"
export EMAIL_RECIPIENT

RECIPIENT_EMAIL="${2:-${EMAIL_RECIPIENT}}"

python3 << 'PYSCRIPT'
import sqlite3
import os
import json
import urllib.request
from datetime import datetime

# Get API key (from bootstrap environment or .env)
API_KEY = os.environ.get('EMAIL_API_KEY')
RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'jidai@6ray.com')

# Debug: Check if we have the API key
if not API_KEY:
    print("⚠ Warning: EMAIL_API_KEY not set - email will not be sent")
    print("  Make sure EMAIL_API_KEY is set in bootstrap or environment")
    exit(0)  # Exit gracefully, don't fail the pipeline

print(f"✓ EMAIL_API_KEY found (length: {len(API_KEY)} chars)")
print(f"✓ Recipient: {RECIPIENT}")

# Get database stats
c = sqlite3.connect('articles.db').cursor()
total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
processed = c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1').fetchone()[0]
summaries = c.execute('SELECT COUNT(*) FROM article_summaries').fetchone()[0]
keywords = c.execute('SELECT COUNT(*) FROM keywords').fetchone()[0]
questions = c.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
comments = c.execute('SELECT COUNT(*) FROM comments').fetchone()[0]
background = c.execute('SELECT COUNT(*) FROM background_read').fetchone()[0]
analysis = c.execute('SELECT COUNT(*) FROM article_analysis').fetchone()[0]

# Format message
message = f"""News Pipeline Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Database Status:
  Total Articles: {total}
  Processed: {processed}
  Summaries: {summaries}
  Keywords: {keywords}
  Questions: {questions}
  Comments: {comments}
  Background: {background}
  Analysis: {analysis}
  Total Records: {summaries + keywords + questions + comments + background + analysis}

Server: 18.223.121.227
Database: /var/www/news/articles.db

Pipeline Status: ACTIVE
Next Run: Tomorrow at 1:00 AM EST

---
Automated Report from Daily News Pipeline"""

# Send email
payload = {
    "to_email": RECIPIENT,
    "subject": f"Daily News Pipeline Report - {datetime.now().strftime('%Y-%m-%d')}",
    "message": message,
    "from_name": "News Pipeline"
}

try:
    url = 'https://emailapi.6ray.com/send-email'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-Key', API_KEY)
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        if response.status == 200:
            print(f"✓ Email sent successfully to {RECIPIENT}")
            print(f"  Email ID: {result.get('email_id', 'N/A')}")
        else:
            print(f"✗ Error: {result}")
except Exception as e:
    print(f"✗ Failed: {str(e)}")

PYSCRIPT
