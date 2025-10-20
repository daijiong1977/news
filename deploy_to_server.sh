#!/bin/bash
# Deployment script: Always sync from GitHub to remote server
# Usage: ./deploy_to_server.sh

set -e

REMOTE_HOST="18.223.121.227"
REMOTE_USER="ec2-user"
REMOTE_KEY="$HOME/Downloads/web1.pem"
REMOTE_PATH="/var/www/news"

echo "================================================"
echo "NEWS DEPLOYMENT: GitHub → Remote Server"
echo "================================================"
echo ""

# Step 1: Verify local git is clean or committed
echo "Step 1: Checking local git status..."
if ! git diff --quiet; then
    echo "⚠ Error: You have uncommitted changes!"
    echo "Please commit or stash changes before deploying."
    git status
    exit 1
fi
echo "✓ Local git is clean"
echo ""

# Step 2: Push to GitHub
echo "Step 2: Pushing to GitHub..."
git push origin main
echo "✓ Pushed to GitHub"
echo ""

# Step 3: Pull on remote server from GitHub
echo "Step 3: Pulling latest from GitHub on remote server..."
ssh -i "$REMOTE_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
cd /var/www/news

echo "=== Checking git status on server ==="
git status

echo ""
echo "=== Pulling from GitHub ==="
git pull origin main

echo ""
echo "=== Files synced successfully ==="
ls -lh *.py | head -10
EOF

echo ""
echo "✓ Remote server updated from GitHub"
echo ""
echo "================================================"
echo "✓ DEPLOYMENT COMPLETE"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. SSH to server: ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227"
echo "  2. Run pipeline: cd /var/www/news && python3 run_full_pipeline.py"
echo ""
