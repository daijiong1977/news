# Daily Pipeline Setup Guide

## Overview

The news pipeline is now configured to run automatically every day at **1:00 AM EST (6:00 AM UTC)** to:

1. ✅ Sync latest code from GitHub
2. ✅ Collect articles from RSS feeds (last 24 hours)
3. ✅ Process them with Deepseek API
4. ✅ Insert into database

## Setup Methods

### Option 1: systemd Timer (Recommended for RedHat/Linux)

**Step 1: Copy service files to systemd**

```bash
sudo cp /var/www/news/news-pipeline.service /etc/systemd/system/
sudo cp /var/www/news/news-pipeline.timer /etc/systemd/system/
```

**Step 2: Enable and start the timer**

```bash
sudo systemctl daemon-reload
sudo systemctl enable news-pipeline.timer
sudo systemctl start news-pipeline.timer
```

**Step 3: Verify it's running**

```bash
sudo systemctl status news-pipeline.timer
sudo systemctl list-timers --all
```

**Step 4: View logs**

```bash
# View journal logs
sudo journalctl -u news-pipeline.service -f

# View pipeline logs
tail -f /var/www/news/logs/daily_pipeline_*.log
```

### Option 2: Cron Job (Alternative)

**Step 1: Run setup script**

```bash
bash /var/www/news/setup_cron.sh
```

**Step 2: Verify cron job**

```bash
crontab -l
# Should show: 0 6 * * * /bin/bash /var/www/news/daily_pipeline.sh
```

**Step 3: View logs**

```bash
tail -f /var/www/news/logs/daily_pipeline_*.log
```

## Schedule Details

- **Frequency**: Every day
- **Time**: 1:00 AM EST (6:00 AM UTC)
- **Duration**: ~2-5 minutes per article (4-20 minutes for 4 articles)
- **Logs**: `/var/www/news/logs/daily_pipeline_YYYY-MM-DD_HH-MM-SS.log`

## Files Included

- `daily_pipeline.sh` - Main pipeline script
- `news-pipeline.service` - systemd service unit
- `news-pipeline.timer` - systemd timer (1 AM EST)
- `setup_cron.sh` - Optional cron setup script

## Pipeline Steps

Each day at 1:00 AM EST:

```
1. Git Pull (sync latest code)
   ↓
2. Data Collector (fetch articles from last 24 hours)
   ↓
3. Process All Articles (Deepseek API analysis)
   ↓
4. Insert to Database (summaries, questions, comments)
   ↓
5. Log Results
```

## Monitoring

### Check if timer is active

```bash
sudo systemctl is-active news-pipeline.timer
sudo systemctl is-enabled news-pipeline.timer
```

### View next scheduled run

```bash
sudo systemctl list-timers news-pipeline.timer
```

### Check recent runs

```bash
sudo journalctl -u news-pipeline.service -n 50
```

### Manual trigger (for testing)

```bash
sudo systemctl start news-pipeline.service
```

## Troubleshooting

### Timer not running

```bash
# Check if systemd is available
systemctl --version

# Check service status
sudo systemctl status news-pipeline.timer
sudo systemctl status news-pipeline.service

# View detailed logs
sudo journalctl -u news-pipeline.timer -xe
```

### API Key not found

Ensure `.env` file exists:

```bash
cat /var/www/news/.env
# Should contain: DEEPSEEK_API_KEY=sk-...
```

### Permission issues

```bash
# Ensure ec2-user owns the directory
sudo chown -R ec2-user:ec2-user /var/www/news
sudo chmod 755 /var/www/news/daily_pipeline.sh
```

## Disable the Pipeline

### Disable systemd timer

```bash
sudo systemctl stop news-pipeline.timer
sudo systemctl disable news-pipeline.timer
```

### Remove cron job

```bash
crontab -e
# Delete the news-pipeline line
```

## Environment Details

- **Server**: EC2 (RedHat/CentOS)
- **User**: ec2-user
- **Working Directory**: /var/www/news
- **Database**: /var/www/news/articles.db
- **API**: Deepseek (sk-aca3446a33184cc4b6381d1ba8d99956)

## Timeline Example

If set up at 2025-10-20:

- **2025-10-21 01:00 AM EST** - First run
- **2025-10-22 01:00 AM EST** - Second run
- **2025-10-23 01:00 AM EST** - Third run
- ... (continues daily)

## Data Growth Expected

Per day (assuming 4 articles collected):

- ~12 article summaries (3 levels × 4 articles)
- ~120 keywords (3 levels × 10 keywords × 4 articles)
- ~40 questions records
- ~200 choices (5 per question)
- ~36 comments (3 perspectives × 3 attitudes × 4 articles)
- ~12 background reading
- ~8 article analysis records

**Weekly**: ~600 new records
**Monthly**: ~2,400 new records
**Yearly**: ~31,200 new records

## Next Steps

1. **Deploy on EC2**:
   ```bash
   scp news-pipeline.* ec2-user@your-server:/var/www/news/
   scp daily_pipeline.sh ec2-user@your-server:/var/www/news/
   ```

2. **Setup on EC2** (systemd method):
   ```bash
   sudo cp /var/www/news/news-pipeline.* /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable news-pipeline.timer
   sudo systemctl start news-pipeline.timer
   ```

3. **Verify**:
   ```bash
   sudo systemctl list-timers --all
   sudo journalctl -u news-pipeline.service -n 10
   ```

## Support

For logs, issues, or monitoring:
- Check: `/var/www/news/logs/`
- Monitor: `sudo journalctl -u news-pipeline.service -f`
- Manual run: `bash /var/www/news/daily_pipeline.sh`
