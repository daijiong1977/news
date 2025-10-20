#!/bin/bash
###############################################################################
# Daily News Pipeline Runner
# 
# This script runs the full news pipeline on the EC2 server:
# 1. Crawl RSS feeds (4 sources)
# 2. Fetch article content
# 3. Process with Deepseek API
# 4. Generate HTML pages
#
# Setup:
#   - Install on EC2 at: /var/www/news/run_pipeline.sh
#   - Make executable: chmod +x run_pipeline.sh
#   - Add to cron: crontab -e
#   - Schedule: 0 2 * * * cd /var/www/news && ./run_pipeline.sh
#   - Or use systemd timer (see below)
#
###############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="/var/www/news"
LOG_DIR="/var/www/news/logs"
LOG_FILE="$LOG_DIR/pipeline-$(date +%Y%m%d-%H%M%S).log"
API_KEY="sk-3fa37d1185514b7fbcd4c1ab8b7643db"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===================================================${NC}" | tee -a "$LOG_FILE"
echo -e "${GREEN}Starting News Pipeline - $(date '+%Y-%m-%d %H:%M:%S')${NC}" | tee -a "$LOG_FILE"
echo -e "${GREEN}===================================================${NC}" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"

# Run the pipeline
if DEEPSEEK_API_KEY="$API_KEY" python3 run_full_pipeline.py 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${GREEN}✓ Pipeline completed successfully${NC}" | tee -a "$LOG_FILE"
    
    # Check if output was generated
    if [ -f "output/index.html" ]; then
        ARTICLE_COUNT=$(grep -c "article-item" output/index.html || echo "0")
        echo -e "${GREEN}✓ Generated $ARTICLE_COUNT articles${NC}" | tee -a "$LOG_FILE"
    fi
    
    echo -e "${GREEN}✓ Output available at: /var/www/news/output/index.html${NC}" | tee -a "$LOG_FILE"
    
    # Optional: Clean up old logs (keep last 30 days)
    find "$LOG_DIR" -name "pipeline-*.log" -mtime +30 -delete 2>/dev/null || true
    
    echo -e "${GREEN}Completed at: $(date '+%Y-%m-%d %H:%M:%S')${NC}" | tee -a "$LOG_FILE"
    exit 0
else
    echo -e "${RED}✗ Pipeline failed${NC}" | tee -a "$LOG_FILE"
    echo -e "${RED}Check log: $LOG_FILE${NC}"
    exit 1
fi
