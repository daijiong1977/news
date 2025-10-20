#!/bin/bash
cd /var/www/news
source .env
export DEEPSEEK_API_KEY
nohup bash process_all_articles.sh > process_output.log 2>&1 &
PID=$!
echo "Background processing started (PID: $PID)"
echo "Check progress: tail -f process_output.log"
