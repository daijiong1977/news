# News Pipeline Backend Documentation

## Overview

The News Pipeline Backend is an automated system that:
1. **Collects** articles from RSS feeds (4 enabled feeds: PBS, Science, Swimming, Technology)
2. **Analyzes** articles using Deepseek API for multi-level summaries and Q&A
3. **Processes** articles through difficulty levels (easy, mid, hard)
4. **Sends** email reports of pipeline execution
5. **Runs automatically** every day at 1:00 AM EST (6:00 AM UTC)

---

## Database Schema

### Core Tables

#### `feeds` - RSS Feed Configuration
Controls which feeds are crawled
```
feed_id       INTEGER PRIMARY KEY
feed_name     TEXT (e.g., 'PBS', 'Science', 'Technology', 'Swimming')
feed_url      TEXT (RSS feed URL)
category_id   INTEGER (foreign key to categories)
enable        BOOLEAN (1=enabled, 0=disabled)
created_at    TEXT (ISO timestamp)
```

**Current Configuration:**
- ✓ PBS (enable=1)
- ✓ Science (enable=1)
- ✓ Swimming (enable=1)
- ✓ Technology (enable=1)
- ✗ Politics (enable=0)
- ✗ US News (enable=0)

#### `categories` - Content Categories
```
category_id   INTEGER PRIMARY KEY
category_name TEXT (e.g., 'PBS', 'Science', etc.)
description   TEXT
prompt_name   TEXT (used for Deepseek prompting)
created_at    TEXT
```

#### `articles` - Raw Articles
```
id                    INTEGER PRIMARY KEY
title                 TEXT
source                TEXT
url                   TEXT UNIQUE
description           TEXT
content               TEXT
pub_date              TEXT
crawled_at            TEXT
deepseek_processed    BOOLEAN (0=pending, 1=processed)
processed_at          TEXT
category_id           INTEGER (foreign key)
zh_title              TEXT (Chinese translation)
image_id              INTEGER (foreign key to article_images)
```

#### `article_summaries` - Processed Content
Multi-level summaries for different audiences
```
id            INTEGER PRIMARY KEY
article_id    INTEGER (foreign key)
difficulty_id INTEGER (1=easy, 2=mid, 3=hard)
language_id   INTEGER (1=en, 2=zh)
summary       TEXT
generated_at  TEXT
```

#### `keywords` - Key Terms
Extracted keywords with difficulty-specific explanations
```
word_id       INTEGER PRIMARY KEY
word          TEXT
article_id    INTEGER
difficulty_id INTEGER
explanation   TEXT
```

#### `questions` - Q&A Content
Multiple choice questions for each article
```
question_id   INTEGER PRIMARY KEY
article_id    INTEGER
difficulty_id INTEGER
question_text TEXT
created_at    TEXT
```

#### `choices` - Answer Options
```
choice_id     INTEGER PRIMARY KEY
question_id   INTEGER
choice_text   TEXT
is_correct    BOOLEAN
explanation   TEXT
```

#### `comments` - Perspectives
Different viewpoints on articles (positive/neutral/negative)
```
comment_id    INTEGER PRIMARY KEY
article_id    INTEGER
difficulty_id INTEGER
attitude      TEXT (positive/neutral/negative)
com_content   TEXT
who_comment   TEXT
comment_date  TEXT
```

#### `background_read` - Context
Background information for understanding articles
```
background_read_id INTEGER PRIMARY KEY
article_id         INTEGER
difficulty_id      INTEGER
background_text    TEXT
created_at         TEXT
```

#### `article_analysis` - Deep Analysis
Structure and tone analysis for mid/hard levels
```
analysis_id   INTEGER PRIMARY KEY
article_id    INTEGER
difficulty_id INTEGER
analysis_en   TEXT
created_at    TEXT
```

#### `difficulty_levels` - Learning Levels
```
difficulty_id INTEGER PRIMARY KEY
difficulty    TEXT (easy, mid, hard)
meaning       TEXT
grade         TEXT (grade levels 3-5, 6-8, 9-12)
```

#### `languages` - Supported Languages
```
language_id INTEGER PRIMARY KEY
language    TEXT (en, zh)
```

---

## Crawling Parameters

### Data Collection (`data_collector.py`)

**Configuration:**
- **num_per_source**: Number of articles per feed (default: 5)
  - Modify in `data_collector.py` line: `collect_articles(num_per_source=5)`
  
- **Active Feeds**: Controlled by `feeds.enable` column
  - Only feeds with `enable = 1` are crawled
  - Query: `SELECT * FROM feeds WHERE enable = 1`

- **Collection Targets:**
  - PBS: 5 articles
  - Science: 5 articles
  - Swimming: 5 articles
  - Technology: 5 articles
  - **Total: 20 articles per run**

### Deepseek Processing (`data_processor.py`)

**API Configuration:**
- **Model**: deepseek-chat
- **API Key**: stored in `.env` file (sk-aca3446...)
- **Timeout**: (30, 300) - 30s connection, 300s read timeout
- **Max Tokens**: 6000
- **Temperature**: 0.7
- **Response Format**: JSON mode with explicit schema

**Processing Steps per Article:**
1. Extract basic information (title, source, category)
2. Generate 3 difficulty levels of content:
   - **Easy**: Simple language, basic facts (grades 3-5)
   - **Mid**: Intermediate concepts, context (grades 6-8)
   - **Hard**: Advanced analysis, implications (grades 9-12)
3. Create: summaries, keywords, Q&A, perspectives, background
4. Mark `deepseek_processed = 1` when complete

---

## Background Process Management

### Starting the Pipeline

**Option 1: Manual One-Time Run**
```bash
# From /var/www/news on EC2
nohup bash daily_pipeline.sh > pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**Option 2: Automated Daily (Systemd Timer)**
```bash
# Status
sudo systemctl status news-pipeline.timer

# Start
sudo systemctl start news-pipeline.timer

# Stop
sudo systemctl stop news-pipeline.timer

# Enable on reboot
sudo systemctl enable news-pipeline.timer

# Disable
sudo systemctl disable news-pipeline.timer
```

**Option 3: View Schedule**
```bash
# Next scheduled run
sudo systemctl list-timers news-pipeline.timer

# Current configuration
cat /etc/systemd/system/news-pipeline.timer
```

### Monitoring Background Processes

**Check if Pipeline is Running:**
```bash
# List all nohup processes
ps aux | grep daily_pipeline

# Find process ID
pgrep -f daily_pipeline

# Real-time monitoring
top -p $(pgrep -f daily_pipeline)
```

**View Pipeline Logs:**
```bash
# List all pipeline logs
ls -lh /var/www/news/pipeline_*.log

# View latest log (live)
tail -f /var/www/news/pipeline_$(ls -t /var/www/news/pipeline_*.log | head -1 | xargs basename)

# View specific log
cat /var/www/news/pipeline_20251020_230000.log

# Search logs for errors
grep "✗" /var/www/news/pipeline_*.log

# Search for status
grep "✓ Collection complete" /var/www/news/pipeline_*.log
```

**Check Database Status:**
```bash
# Count unprocessed articles
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0')
print('Unprocessed articles:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1')
print('Processed articles:', cursor.fetchone()[0])
conn.close()
"

# Check feeds status
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('SELECT feed_name, enable FROM feeds ORDER BY feed_name')
for name, enable in cursor.fetchall():
    status = '✓' if enable else '✗'
    print(f'{status} {name}')
conn.close()
"
```

### Stopping the Pipeline

**Stop Current Run:**
```bash
# Find process
pgrep -f daily_pipeline

# Kill by PID
kill -15 <PID>

# Force kill if needed
kill -9 <PID>
```

**Stop Scheduled Pipeline:**
```bash
# Disable the timer
sudo systemctl stop news-pipeline.timer
```

### Restarting the Pipeline

**Restart Immediately:**
```bash
# Stop current run
pkill -f daily_pipeline

# Start new run
nohup bash daily_pipeline.sh > pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**Restart Systemd Timer:**
```bash
sudo systemctl restart news-pipeline.timer
```

---

## Pipeline Workflow

### Step 1: Data Collection
```
daily_pipeline.sh
  ↓
data_collector.py
  ├─ Query feeds WHERE enable = 1
  ├─ For each enabled feed:
  │  ├─ Fetch RSS feed (5 articles per source)
  │  ├─ Parse XML/Atom
  │  ├─ Check for duplicates
  │  └─ Insert into articles table
  └─ Report: X new articles, Y duplicates
```

### Step 2: Data Processing
```
data_processor.py
  ├─ Query unprocessed articles (deepseek_processed = 0)
  ├─ For each article:
  │  ├─ Send to Deepseek API with category-specific prompt
  │  ├─ Parse response (JSON mode)
  │  ├─ Insert multi-level content:
  │  │  ├─ article_summaries (3 difficulty levels)
  │  │  ├─ keywords (with explanations)
  │  │  ├─ questions (with choices)
  │  │  ├─ comments (perspectives)
  │  │  ├─ background_read (context)
  │  │  └─ article_analysis (structure/tone)
  │  └─ Mark deepseek_processed = 1
  └─ Report: X articles processed
```

### Step 3: Database Verification
```
check_progress.sh
  ├─ Count total articles
  ├─ Count processed articles
  ├─ Count unprocessed articles
  └─ Show statistics
```

### Step 4: Email Report
```
send_email_report.sh
  ├─ Query database statistics
  ├─ Format report:
  │  ├─ Total articles
  │  ├─ Processed articles
  │  ├─ Unprocessed articles
  │  ├─ Enabled feeds
  │  └─ Processing timestamp
  └─ Send via emailapi.6ray.com → jidai@6ray.com
```

---

## Feed Configuration Management

### View All Feeds
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT f.feed_id, f.feed_name, f.enable, c.category_name
    FROM feeds f
    JOIN categories c ON f.category_id = c.category_id
    ORDER BY f.feed_name
''')
for feed_id, name, enable, category in cursor.fetchall():
    status = '✓ ENABLED' if enable else '✗ DISABLED'
    print(f'{status:12} - ID {feed_id}: {name} ({category})')
conn.close()
"
```

### Enable a Feed
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('UPDATE feeds SET enable = 1 WHERE feed_name = ?', ('Swimming',))
conn.commit()
print('✓ Swimming feed enabled')
conn.close()
"
```

### Disable a Feed
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('UPDATE feeds SET enable = 0 WHERE feed_name = ?', ('Politics',))
conn.commit()
print('✓ Politics feed disabled')
conn.close()
"
```

### Add a New Feed
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()

# First, ensure category exists
category_name = 'Business'
cursor.execute('SELECT category_id FROM categories WHERE category_name = ?', (category_name,))
result = cursor.fetchone()

if result:
    category_id = result[0]
    cursor.execute('''
        INSERT INTO feeds (feed_name, feed_url, category_id, enable)
        VALUES (?, ?, ?, 1)
    ''', ('Reuters Business', 'https://feeds.reuters.com/business', category_id))
    conn.commit()
    print('✓ New feed added: Reuters Business')
else:
    print('✗ Category not found')

conn.close()
"
```

---

## Troubleshooting

### Pipeline Not Running
```bash
# Check if systemd timer is active
sudo systemctl status news-pipeline.timer

# Check if service is running
sudo systemctl status news-pipeline.service

# View systemd logs
sudo journalctl -u news-pipeline.service -n 50

# Check nohup process
ps aux | grep daily_pipeline
```

### No New Articles Collected
```bash
# Verify feeds are enabled
python3 -c "import sqlite3; conn = sqlite3.connect('articles.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM feeds WHERE enable = 1'); print('Enabled feeds:', cursor.fetchone()[0])"

# Test individual feed
python3 data_collector.py

# Check feed URLs
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('SELECT feed_name, feed_url FROM feeds WHERE enable = 1')
for name, url in cursor.fetchall():
    print(f'{name}: {url}')
conn.close()
"
```

### Articles Not Processing
```bash
# Check unprocessed count
python3 -c "import sqlite3; conn = sqlite3.connect('articles.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0'); print('Unprocessed:', cursor.fetchone()[0])"

# Run processor manually
python3 data_processor.py

# Check API key
grep DEEPSEEK_API_KEY .env
```

### Email Not Sending
```bash
# Check email API key
grep EMAIL_API_KEY .env

# Test email manually
python3 send_email_report.sh

# Check email logs
tail -f /var/www/news/pipeline_*.log | grep -i email
```

---

## Configuration Files

### `.env` - API Keys
```bash
DEEPSEEK_API_KEY=sk-aca3446a33184cc4b6381d1ba8d99956
EMAIL_API_KEY=d94d7e22263d0982.4e91184e309c345bd80e27ad1709f24533955a11150cde9d
EMAIL_RECIPIENT=jidai@6ray.com
```

### `daily_pipeline.sh` - Pipeline Script
```bash
#!/bin/bash
cd /var/www/news
git pull origin main
python3 data_collector.py
python3 data_processor.py
bash check_progress.sh
bash send_email_report.sh
```

### `/etc/systemd/system/news-pipeline.timer` - Scheduler
Runs at: 1:00 AM EST (6:00 AM UTC) daily

### `/etc/systemd/system/news-pipeline.service` - Service Unit
Executes: `/var/www/news/daily_pipeline.sh`

---

## Performance Metrics

**Typical Run Time:** 30-45 minutes
- Data collection: 2-5 minutes
- Deepseek processing: 20-35 minutes (depends on API)
- Database verification: <1 minute
- Email sending: <1 minute

**Resource Usage:**
- Memory: ~200-400 MB during processing
- Network: ~5-10 MB download
- API Calls: 20 per run (one per article)

**Article Volume:**
- Articles collected per run: 20 (5 per enabled feed × 4 feeds)
- Articles processed per run: 20
- Database size growth: ~200 KB per run

---

## Maintenance

### Regular Tasks
- **Daily**: Verify pipeline ran (check log files)
- **Weekly**: Review email reports for anomalies
- **Monthly**: Check database size, archive old logs
- **Quarterly**: Review feed URLs for changes/404s

### Cleanup
```bash
# Archive old pipeline logs (older than 7 days)
find /var/www/news -name "pipeline_*.log" -mtime +7 -exec gzip {} \;

# Remove very old archives (older than 30 days)
find /var/www/news -name "pipeline_*.log.gz" -mtime +30 -delete

# Check database size
du -h /var/www/news/articles.db
```

### Database Maintenance
```bash
# Optimize database
sqlite3 /var/www/news/articles.db "VACUUM;"

# Check database integrity
sqlite3 /var/www/news/articles.db "PRAGMA integrity_check;"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start pipeline (now) | `nohup bash daily_pipeline.sh > pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &` |
| Check if running | `ps aux \| grep daily_pipeline` |
| View latest log | `tail -f pipeline_*.log` |
| Stop pipeline | `pkill -f daily_pipeline` |
| Check feeds | `python3 -c "import sqlite3; ..."` |
| Enable feed | `sqlite3 articles.db "UPDATE feeds SET enable=1 WHERE feed_name='X';"` |
| View timer status | `sudo systemctl status news-pipeline.timer` |
| See next run time | `sudo systemctl list-timers news-pipeline.timer` |

