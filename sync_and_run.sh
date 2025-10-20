#!/bin/bash

# Full backend sync and processing script
# Pulls latest from GitHub, then runs article processing in background

echo "🔄 Starting backend sync and processing..."

# SSH to EC2 and execute
ssh -o StrictHostKeyChecking=no -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'EOF'
cd /var/www/news

echo "📥 Pulling latest from GitHub..."
git pull origin main

echo "⚙️ Loading API key..."
source .env
export DEEPSEEK_API_KEY

echo "🚀 Starting article processing in background..."
nohup bash process_all_articles.sh > process_output.log 2>&1 &
PID=$!

echo "✅ Processing started (PID: $PID)"
echo ""
echo "Monitor progress with:"
echo "  ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 'cd /var/www/news && tail -f process_output.log'"
echo ""
echo "Check database status with:"
echo "  ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 'cd /var/www/news && python3 -c \"import sqlite3; c=sqlite3.connect(\\\"articles.db\\\").cursor(); print(\\\"Processed:\\\", c.execute(\\\"SELECT COUNT(*) FROM articles WHERE deepseek_processed=1\\\").fetchone()[0])\"'"

EOF

echo "✓ Backend job submitted"
