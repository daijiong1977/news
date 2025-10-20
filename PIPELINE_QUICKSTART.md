# News Pipeline - Quick Start Guide

## What It Does

The automated news pipeline:
1. **Crawls** 4 RSS feeds daily (PBS, Swimming World, TechRadar, Science Daily)
2. **Fetches** full article content from URLs
3. **Processes** with Deepseek AI to create 3 reading levels
4. **Generates** beautiful HTML pages
5. **Publishes** to https://news.6ray.com/output/

**Runs automatically at 2 AM UTC every day** ✓

---

## Quick Commands

### Manual Trigger
```bash
# From your Mac
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
sudo systemctl start news-pipeline.service
```

### View Output
```bash
# In your browser
https://news.6ray.com/output/index.html
```

### Check Status
```bash
# See if timer is active
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'sudo systemctl list-timers news-pipeline.timer'
```

### View Logs
```bash
# Real-time logs
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'sudo journalctl -u news-pipeline.service -f'

# Last 100 lines
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'sudo journalctl -u news-pipeline.service -n 100'
```

### Manual Test
```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'EOF'
cd /var/www/news
rm -f articles.db  # Start fresh
export DEEPSEEK_API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"
python3 run_full_pipeline.py --test  # Quick test (2 articles per source)
EOF
```

---

## How to Customize

### Change Running Time
Edit on EC2 server:
```bash
sudo nano /etc/systemd/system/news-pipeline.timer
```

Change this line (runs at 2 AM UTC):
```ini
OnCalendar=*-*-* 02:00:00
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart news-pipeline.timer
```

### Add More RSS Sources
On local Mac, edit `run_full_pipeline.py` (lines 42-59):
```python
SOURCES = {
    "new_source": {
        "url": "https://example.com/rss",
        "name": "Example News",
        "max_articles": 5,
    },
    # ... existing sources ...
}
```

Then deploy:
```bash
scp -i ~/Downloads/web1.pem /Users/jidai/news/run_full_pipeline.py \
  ec2-user@18.223.121.227:/var/www/news/run_full_pipeline.py
```

### Increase Articles Per Run
Edit `run_full_pipeline.py`:
```python
# Line ~80: Change from 5 to your desired number
"max_articles": 10,  # Was 5
```

---

## Troubleshooting

### Service won't start
```bash
# Check error details
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'sudo journalctl -u news-pipeline.service -xe | tail -50'
```

### No files being generated
```bash
# Check if articles.db exists
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'ls -lh /var/www/news/articles.db'

# Check permissions
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'ls -lh /var/www/news/output/'
```

### API key issue
The key is embedded in the systemd service file. Verify:
```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'sudo grep DEEPSEEK /etc/systemd/system/news-pipeline.service'
```

---

## File Locations

**On EC2 Server:**
- Code: `/var/www/news/run_full_pipeline.py`
- Output: `/var/www/news/output/index.html`
- Database: `/var/www/news/articles.db`
- Logs: `/var/www/news/logs/pipeline-*.log`
- Config: `/etc/systemd/system/news-pipeline.{service,timer}`

**On Your Mac (GitHub):**
- Repo: ~/Downloads/news or ~/news
- Deployed files: `run_full_pipeline.py`, `run_pipeline.sh`

---

## What Happens At 2 AM

1. **Systemd timer** triggers `news-pipeline.service`
2. **Service** runs `/var/www/news/run_pipeline.sh` as `ec2-user`
3. **Bash script** calls `python3 run_full_pipeline.py`
4. **Python** does:
   - ✓ Crawl 4 RSS feeds (5 articles each = 20 total)
   - ✓ Fetch full content from URLs
   - ✓ Send to Deepseek API (1-2 min, with delays)
   - ✓ Get 3 summaries per article
   - ✓ Generate HTML pages + index
5. **Output** published to `/var/www/news/output/`
6. **Nginx** serves via `https://news.6ray.com/output/`
7. **Logs** written to `/var/www/news/logs/`

**Total time: ~2-3 minutes**

---

## Monitoring

### Weekly Check
```bash
# Verify it ran
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 \
  'ls -lhtr /var/www/news/logs/ | tail -7'

# See output
curl https://news.6ray.com/output/index.html | head -20
```

### Monthly Maintenance
```bash
# Archive old data (if needed)
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'EOF'
cd /var/www/news
tar -czf archive-$(date +%Y%m%d).tar.gz articles.db output/
# Optional: Delete old files
EOF
```

---

## Features

✓ Automated daily runs (2 AM UTC)  
✓ 4 RSS feeds (can add more)  
✓ 3-tier reading levels (elementary, middle, high)  
✓ Beautiful HTML output  
✓ Stores history in SQLite  
✓ Systemd logging  
✓ Error handling & reporting  
✓ Configurable delays (respectful to servers)

---

## Next Steps

1. ✓ **Deployed** - Running on EC2
2. ✓ **Timer Active** - Runs daily at 2 AM
3. ✓ **API Configured** - Deepseek key embedded
4. **Monitor** - Check output weekly
5. **Extend** - Add more sources or customize

---

**API Key:** `sk-3fa37d1185514b7fbcd4c1ab8b7643db` ✓ Configured  
**Server:** `18.223.121.227` (EC2)  
**Domain:** `news.6ray.com`  
**Schedule:** Daily at 2:00 AM UTC  
**Last Run:** Available in logs  
**Status:** ✓ ACTIVE AND READY
