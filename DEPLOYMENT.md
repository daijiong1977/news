# News Pipeline - Deployment Guide to EC2

## Overview

This document provides step-by-step instructions for deploying the news article processing pipeline to your Amazon EC2 server.

The system works in three stages:
1. **Data Collection** (`data_collector.py`) - Fetch articles from RSS feeds
2. **API Processing** (`process_one_article.py`) - Generate analysis via Deepseek API
3. **Database Insertion** (`insert_from_response.py`) - Insert validated responses into database

## Pre-Deployment Checklist (Local)

- [x] Database schema initialized (`articles.db` with 19 tables)
- [x] All source code files ready for deployment
- [x] Test response files cleaned up
- [x] GitHub repository prepared
- [x] Config with API credentials ready

## EC2 Deployment Steps

### Step 1: SSH into EC2 Server

```bash
ssh -i /path/to/your-key.pem ec2-user@your-ec2-ip
```

### Step 2: Install Dependencies

```bash
# Update system packages
sudo yum update -y

# Install Python 3.9+
sudo yum install python3 python3-pip -y

# Install required Python packages
pip3 install requests sqlite3 feedparser python-dotenv
```

### Step 3: Clone Repository

```bash
cd ~/
git clone https://github.com/daijiong1977/news.git
cd news
```

### Step 4: Configure Environment

Create `.env` file with your Deepseek API key:

```bash
cat > .env << 'EOF'
DEEPSEEK_API_KEY=your_api_key_here
EOF

chmod 600 .env
```

Or set as environment variable:

```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

### Step 5: Initialize Database

```bash
python3 init_db.py
```

This will create the fresh `articles.db` with 19 tables and populate lookup tables.

### Step 6: Collect Articles

```bash
python3 data_collector.py
```

This will fetch articles from configured RSS feeds and insert them into the database.

### Step 7: Test Processing (Single Article)

```bash
python3 process_one_article.py
```

This will:
- Get the first unprocessed article
- Call Deepseek API with appropriate category prompt
- Save response to `response_article_X_TIMESTAMP.json`
- Display verification report

### Step 8: Insert Processed Article

```bash
python3 insert_from_response.py response_article_1_*.json
```

This will:
- Load the saved response
- Extract Chinese title (with fallback)
- Insert all content into database
- Mark article as processed

## Automated Processing Workflow

For continuous processing without manual intervention:

### Option A: Bash Loop (Simple)

```bash
#!/bin/bash
cd ~/news
export DEEPSEEK_API_KEY=your_api_key

while true; do
    # Get count of unprocessed articles
    COUNT=$(sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=0;")
    
    if [ "$COUNT" -gt 0 ]; then
        echo "Processing article..."
        python3 process_one_article.py
        
        # Get latest response file
        RESPONSE=$(ls -t response_article_*.json 2>/dev/null | head -1)
        
        if [ -n "$RESPONSE" ]; then
            python3 insert_from_response.py "$RESPONSE"
            echo "Article inserted successfully"
        fi
    else
        echo "No unprocessed articles. Waiting..."
    fi
    
    # Wait 5 minutes before checking again
    sleep 300
done
```

Save as `process_articles.sh` and run in background:

```bash
nohup bash process_articles.sh > process_log.txt 2>&1 &
```

### Option B: Cron Job (Scheduled)

Edit crontab:

```bash
crontab -e
```

Add line to run collection every 6 hours and process articles every hour:

```cron
# Collect articles every 6 hours
0 */6 * * * cd ~/news && python3 data_collector.py >> logs/collector.log 2>&1

# Process one article every hour (if available)
0 * * * * cd ~/news && export DEEPSEEK_API_KEY=your_api_key && python3 process_one_article.py && RESPONSE=$(ls -t response_article_*.json 2>/dev/null | head -1) && [ -n "$RESPONSE" ] && python3 insert_from_response.py "$RESPONSE" >> logs/processor.log 2>&1
```

### Option C: Systemd Service (Production)

Create `/etc/systemd/system/news-pipeline.service`:

```ini
[Unit]
Description=News Article Processing Pipeline
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/news
Environment="DEEPSEEK_API_KEY=your_api_key"
ExecStart=/usr/bin/python3 /home/ec2-user/news/process_articles_loop.sh
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable news-pipeline.service
sudo systemctl start news-pipeline.service
```

Check status:

```bash
sudo systemctl status news-pipeline.service
journalctl -u news-pipeline.service -f
```

## Monitoring

### Check Database Status

```bash
# Total articles
sqlite3 articles.db "SELECT COUNT(*) as total, SUM(deepseek_processed) as processed FROM articles;"

# Data counts by table
sqlite3 articles.db << EOF
SELECT 'summaries', COUNT(*) FROM article_summaries
UNION ALL SELECT 'keywords', COUNT(*) FROM keywords
UNION ALL SELECT 'questions', COUNT(*) FROM questions
UNION ALL SELECT 'choices', COUNT(*) FROM choices
UNION ALL SELECT 'comments', COUNT(*) FROM comments
UNION ALL SELECT 'backgrounds', COUNT(*) FROM background_read
UNION ALL SELECT 'analysis', COUNT(*) FROM article_analysis;
EOF
```

### Check Processing Logs

```bash
# Check for errors
tail -100 process_log.txt | grep -i error

# Check recent processing
tail -50 process_log.txt
```

## File Structure

Essential files on EC2 server:

```
~/news/
├── articles.db                      # SQLite database (created by init_db.py)
├── init_db.py                       # Initialize database schema
├── data_collector.py                # Collect articles from RSS feeds
├── process_one_article.py           # Generate Deepseek analysis
├── insert_from_response.py          # Insert responses into database
├── prompts_compact.md               # API prompts for each category
├── config.json                      # Configuration (RSS feeds, etc.)
├── .env                             # API credentials (created manually)
├── process_articles.sh              # Processing loop script (optional)
└── logs/                            # Log directory (create manually)
    ├── collector.log
    └── processor.log
```

## Troubleshooting

### Issue: API Timeout

If you see socket timeout errors:
- Check network connectivity: `ping api.deepseek.com`
- Verify timeout is set to `(30, 300)` in process_one_article.py
- Check API key is valid

### Issue: Article Not Found

Ensure articles are collected first:
```bash
python3 data_collector.py
```

### Issue: Insertion Fails

Check response file is valid JSON:
```bash
python3 -m json.tool response_article_*.json | head -20
```

### Issue: Database Locked

If database is locked, restart any background processes:
```bash
pkill -f "python3 process_one_article.py"
pkill -f "python3 insert_from_response.py"
```

## Next Steps

After deployment and initial processing:

1. **Generate Pages** - Create `page_generator.py` to output HTML/JSON from database
2. **Web Interface** - Deploy web server to display articles
3. **Monitoring** - Set up alerts for processing failures
4. **Scaling** - Add multiple processing workers if needed

## Support

For issues or questions:
1. Check the logs
2. Review this deployment guide
3. Verify database state with SQL queries
4. Check Deepseek API status and remaining credits

---

**Last Updated:** October 20, 2025  
**Deployment Ready:** Yes ✓
