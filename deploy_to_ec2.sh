#!/bin/bash

# Deploy script - Copy latest files from Mac to EC2 server
# Usage: bash deploy_to_ec2.sh

EC2_KEY="$HOME/Downloads/web1.pem"
EC2_USER="ec2-user"
EC2_IP="18.223.121.227"
EC2_PATH="/var/www/news"
LOCAL_PATH="/Users/jidai/news"

echo "========================================="
echo "DEPLOYING TO EC2 SERVER"
echo "========================================="
echo ""

# Files to deploy
FILES=(
    "init_db.py"
    "data_collector.py"
    "process_one_article.py"
    "insert_from_response.py"
    "prompts_compact.md"
    "config.json"
    "example_response_structure.json"
    "ec2_setup_db.sh"
    "process_all_articles.sh"
)

echo "Copying files to EC2..."
for file in "${FILES[@]}"; do
    if [ -f "$LOCAL_PATH/$file" ]; then
        scp -o StrictHostKeyChecking=no -i "$EC2_KEY" "$LOCAL_PATH/$file" "$EC2_USER@$EC2_IP:$EC2_PATH/" 2>/dev/null
        echo "✓ $file"
    else
        echo "⚠ $file not found locally"
    fi
done

echo ""
echo "========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "Next steps on EC2:"
echo ""
echo "  ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227"
echo "  cd /var/www/news"
echo "  export DEEPSEEK_API_KEY=sk-aca3446a33184cc4b6381d1ba8d99956"
echo "  bash process_all_articles.sh"
echo ""
