#!/bin/bash

# Setup daily cron job for news pipeline
# Schedules the pipeline to run every day at 1:00 AM EST

echo "Setting up daily news pipeline cron job..."
echo ""

# Create cron entry (1:00 AM EST = 6:00 AM UTC)
CRON_ENTRY="0 6 * * * /bin/bash /var/www/news/daily_pipeline.sh"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "daily_pipeline" ; echo "$CRON_ENTRY") | crontab -

echo "✓ Cron job configured"
echo ""
echo "Schedule: Every day at 1:00 AM EST (6:00 AM UTC)"
echo "Script: /var/www/news/daily_pipeline.sh"
echo "Logs: /var/www/news/logs/daily_pipeline_*.log"
echo ""
echo "Verify with: crontab -l"
echo "To remove: crontab -e (and delete the line)"
