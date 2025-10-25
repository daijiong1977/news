#!/bin/bash

# News Pipeline Runner with nohup background execution
# This script starts the complete pipeline (mine + images + deepseek)
# with 3 articles per source and runs in the background

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_DIR/log"
LOG_FILE="$LOG_DIR/pipeline_nohup_$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "======================================"
echo "🚀 News Pipeline Runner"
echo "======================================"
echo "📁 Project: $PROJECT_DIR"
echo "🕐 Timestamp: $TIMESTAMP"
echo "📝 Log file: $LOG_FILE"
echo "======================================"
echo ""

# Start pipeline in background with nohup
echo "⏳ Starting pipeline (3 articles per source)..."
echo "   Running: python3 pipeline.py --full --articles-per-seed 3"
echo ""

nohup python3 "$PROJECT_DIR/pipeline.py" --full --articles-per-seed 3 -v > "$LOG_FILE" 2>&1 &
PIPELINE_PID=$!

echo "✅ Pipeline started successfully!"
echo "📊 Process ID: $PIPELINE_PID"
echo "📂 Log file: $LOG_FILE"
echo ""
echo "🔍 To monitor progress, run:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 To stop the pipeline, run:"
echo "   kill $PIPELINE_PID"
echo ""
echo "======================================"
