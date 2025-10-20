# Full End-to-End News Pipeline - EC2 Deployment

## Overview

This document describes the complete automated news pipeline running on AWS EC2 (news.6ray.com). The system:

1. **Crawls** articles from 4 RSS sources (PBS, Swimming World, TechRadar, Science Daily)
2. **Fetches** full article content from URLs
3. **Processes** with Deepseek API to generate 3-tier reading levels (elementary, middle, high)
4. **Generates** beautiful HTML pages with summaries
5. **Runs automatically** via systemd timer (2 AM daily)

---

## Architecture

```
Internet (4 RSS Feeds)
    ↓
Python Pipeline (EC2 @ /var/www/news)
    ├── Step 1: Crawl RSS (fetch_rss_feed)
    ├── Step 2: Fetch Content (fetch_article_content)
    ├── Step 3: Deepseek API (process_with_deepseek)
    ├── Step 4: Generate HTML (generate_pages)
    └── Output: /var/www/news/output/*.html
    ↓
Nginx Reverse Proxy (news.6ray.com)
    ↓
Browser: https://news.6ray.com/output/index.html
```

---

## Files

### Main Pipeline Script
- **`run_full_pipeline.py`** - Complete end-to-end pipeline
  - ~750 lines of Python
  - Handles crawling, fetching, Deepseek API calls, HTML generation
  - Stores data in SQLite (`articles.db`)
  - Outputs to `/output/` directory

### Systemd Integration
- **`news-pipeline.service`** - Systemd service unit
  - Runs as `ec2-user`
  - Sets environment variables (API key)
  - Manages permissions for output directory

- **`news-pipeline.timer`** - Systemd timer
  - Triggers at 2:00 AM daily
  - Automatically runs `news-pipeline.service`

### Runner Script
- **`run_pipeline.sh`** - Bash wrapper
  - Creates logs in `/var/www/news/logs/`
  - Handles error reporting
  - Logs to journalctl

---

## Data Flow

### Step 1: Crawl RSS Sources (5-10 sec)
```
4 RSS feeds → Parse XML → Extract title, link, description
↓
Store in articles.db (title, source, url, description, pub_date)
```

**Sources:**
- PBS NewsHour: https://www.pbs.org/newshour/feeds/rss/headlines
- Swimming World: https://www.swimmingworldmagazine.com/news/feed/
- TechRadar: https://www.techradar.com/rss
- Science Daily: https://www.sciencedaily.com/rss/top.xml

### Step 2: Fetch Article Content (10-15 sec)
```
URL → Fetch HTML → Extract paragraphs → Store in DB
↓
First 10 paragraphs stored for each article
```

### Step 3: Process with Deepseek API (1-2 min)
```
Title + Content → Deepseek API (gpt-like model)
↓
Generate 3 summaries:
  - Elementary (ages 8-11): Simple language
  - Middle (ages 12-14): Standard complexity
  - High (ages 15+): Advanced context
↓
Store summaries in article_summaries table
```

**API Details:**
- Endpoint: https://api.deepseek.com/chat/completions
- Model: `deepseek-chat`
- Rate limit: 2-second delay between requests (courteous)
- Cost: ~$0.001-0.002 per article

### Step 4: Generate HTML (5-10 sec)
```
For each processed article:
  - Create article_N.html
  - Display 3 summaries by reading level
  - Link to original article
  - Include article metadata
↓
Create index.html (links to all articles)
```

---

## Database Schema

### articles table
```sql
id INTEGER PRIMARY KEY
title TEXT
source TEXT
url TEXT UNIQUE
description TEXT
pub_date TEXT
image_url TEXT
image_local TEXT
content TEXT
crawled_at TEXT
deepseek_processed BOOLEAN
processed_at TEXT
```

### article_summaries table
```sql
id INTEGER PRIMARY KEY
article_id INTEGER (FK → articles.id)
difficulty TEXT (elementary, middle, high)
language TEXT
summary TEXT
generated_at TEXT
```

---

## Configuration

### API Key
- **Location:** Environment variable `DEEPSEEK_API_KEY`
- **Value:** `sk-3fa37d1185514b7fbcd4c1ab8b7643db`
- **Set in:** `/etc/systemd/system/news-pipeline.service`

### RSS Sources
Edit in `run_full_pipeline.py` lines ~42-59:
```python
SOURCES = {
    "pbs": {...},
    "swimming": {...},
    "techradar": {...},
    "sciencedaily": {...},
}
```

### Article Limits
- Per source (production): 5 articles
- Per source (test mode): 2 articles
- Max to process with Deepseek: 50 per run
- Max HTML pages: 50 per run

### Output Directory
- Location: `/var/www/news/output/`
- Accessible via: `https://news.6ray.com/output/`
- Cleared before each run (optional - currently keeps history)

---

## Running the Pipeline

### Manual Execution

**Test Mode (2 articles per source, 5 processed):**
```bash
cd /var/www/news
export DEEPSEEK_API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"
python3 run_full_pipeline.py --test
```

**Production (5 articles per source, 50 processed):**
```bash
cd /var/www/news
export DEEPSEEK_API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"
python3 run_full_pipeline.py
```

**With Limits:**
```bash
python3 run_full_pipeline.py --limit 3  # 3 articles per source
python3 run_full_pipeline.py --limit 2 --test
```

**Skip Steps:**
```bash
python3 run_full_pipeline.py --skip-crawl        # Skip RSS crawling
python3 run_full_pipeline.py --skip-fetch        # Skip content fetching
python3 run_full_pipeline.py --skip-deepseek     # Skip API processing
python3 run_full_pipeline.py --skip-pages        # Skip HTML generation
```

### Via Systemd Timer

**Manual Start:**
```bash
sudo systemctl start news-pipeline.service
```

**Check Status:**
```bash
sudo systemctl status news-pipeline.service
```

**View Logs:**
```bash
sudo journalctl -u news-pipeline.service -f      # Follow in real-time
sudo journalctl -u news-pipeline.service -n 100  # Last 100 lines
sudo journalctl -u news-pipeline.service --since "2 hours ago"
```

**Check Timer Schedule:**
```bash
sudo systemctl list-timers news-pipeline.timer
```

**View Output Logs:**
```bash
ls -lh /var/www/news/logs/
tail -f /var/www/news/logs/pipeline-*.log
```

---

## Monitoring & Troubleshooting

### View Generated Pages
```bash
open https://news.6ray.com/output/index.html
```

### Check Database
```bash
# From EC2 server
cd /var/www/news
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM articles')
print('Total articles:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM article_summaries')
print('Summaries:', c.fetchone()[0])
"
```

### Common Issues

**1. Permission Denied on articles.db**
```
Error: sqlite3.OperationalError: attempt to write a readonly database
```
Solution:
```bash
sudo chown ec2-user:ec2-user /var/www/news/articles.db
sudo chmod 644 /var/www/news/articles.db
```

**2. Deepseek API Key Not Found**
```
Error: DEEPSEEK_API_KEY not set
```
Solution: Verify in systemd service or environment:
```bash
echo $DEEPSEEK_API_KEY  # Check if set
sudo systemctl cat news-pipeline.service | grep API
```

**3. Service Fails to Start**
```bash
# Check detailed error
sudo journalctl -u news-pipeline.service -xe

# Test manually to see actual error
cd /var/www/news
export DEEPSEEK_API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"
python3 run_full_pipeline.py --test
```

**4. Deepseek API Rate Limit**
```
Error: API rate limit exceeded
```
Solution: Pipeline already includes 2-second delays between requests. If needed, increase delay in `run_full_pipeline.py` line ~356:
```python
time.sleep(2)  # Increase to 3 or 5
```

---

## Performance

### Typical Run Times
- **Step 1 (Crawl):** 5-10 seconds (20 articles from 4 sources)
- **Step 2 (Fetch Content):** 10-15 seconds (parallel requests)
- **Step 3 (Deepseek API):** 1-2 minutes (rate limited, serial)
- **Step 4 (Generate HTML):** 5-10 seconds

**Total: ~2-3 minutes for 20 articles**

### Resource Usage
- **CPU:** ~30-40% during API calls
- **Memory:** ~150-200 MB
- **Network:** ~5-10 MB per run
- **Disk:** ~200 KB per article (HTML + DB entries)

---

## Maintenance

### Clean Up Old Data
```bash
# Archive articles older than 30 days
cd /var/www/news
tar -czf archive-$(date +%Y%m%d).tar.gz articles.db output/
rm -f articles.db && python3 -c "import sqlite3; sqlite3.connect('articles.db')" # Recreate

# Clean old logs (automatic - keeps 30 days)
find /var/www/news/logs -name "*.log" -mtime +30 -delete
```

### Update RSS Sources
Edit `run_full_pipeline.py` and restart:
```bash
sudo systemctl restart news-pipeline.timer
```

### Update Deepseek API Key
Edit in:
1. `/etc/systemd/system/news-pipeline.service` (Environment var)
2. `run_full_pipeline.py` (fallback default)
3. `run_pipeline.sh` (bash script)

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart news-pipeline.timer
```

---

## Accessing Results

### Via Web
```
https://news.6ray.com/output/index.html
```

### Via SSH
```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
ls -la /var/www/news/output/
```

### Via SCP (Download)
```bash
scp -i ~/Downloads/web1.pem -r ec2-user@18.223.121.227:/var/www/news/output ~/Downloads/
```

---

## Advanced Usage

### Custom Test Run
```bash
# Run with specific parameters
cd /var/www/news
export DEEPSEEK_API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"

# Only crawl and fetch (no Deepseek)
python3 run_full_pipeline.py --skip-deepseek --skip-pages

# Only process existing articles with Deepseek
python3 run_full_pipeline.py --skip-crawl --skip-fetch

# Limit to 1 article from each source
python3 run_full_pipeline.py --limit 1
```

### Cron Job Alternative to Systemd
If you prefer cron instead of systemd timer:
```bash
sudo crontab -e
# Add line:
0 2 * * * cd /var/www/news && bash run_pipeline.sh
```

### Environment Expansion
To run at different times, edit `news-pipeline.timer`:
```ini
[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00   # Change hour/minute
OnCalendar=*-*-* 14:00:00   # Add multiple times (run twice daily)
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart news-pipeline.timer
```

---

## Success Indicators

✅ **Pipeline Working If:**
- `https://news.6ray.com/output/index.html` loads
- 20+ articles in index
- Each article has 3 summaries (elementary, middle, high)
- Pages are properly styled with links to original articles
- Logs show "✓ PIPELINE COMPLETE"
- Systemd timer shows "active (waiting)"
- Articles have varied content from 4 different sources

---

## Next Steps

1. **Monitor First Run:** Verify 2 AM run completes successfully
2. **Check Results:** View pages to ensure quality
3. **Adjust Limits:** Scale to more articles if needed
4. **Add More Sources:** Extend `SOURCES` dict for additional feeds
5. **Customize Output:** Modify HTML templates in `generate_pages()`

---

**Last Updated:** October 20, 2025  
**Server:** 18.223.121.227 (EC2)  
**API Key:** ✓ Configured  
**Systemd Timer:** ✓ Active (runs daily at 2 AM UTC)
