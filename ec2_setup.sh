#!/bin/bash

# EC2 News Pipeline - Automated Setup Script
# Run this on your EC2 server to set up the complete pipeline

set -e  # Exit on error

echo "======================================================================="
echo "EC2 NEWS PIPELINE - AUTOMATED SETUP"
echo "======================================================================="
echo ""

# Step 1: Update system
echo "[1/7] Updating system packages..."
sudo yum update -y > /dev/null 2>&1
echo "✓ System packages updated"

# Step 2: Install Python and dependencies
echo "[2/7] Installing Python 3 and dependencies..."
sudo yum install python3 python3-pip git -y > /dev/null 2>&1
pip3 install requests feedparser python-dotenv > /dev/null 2>&1
echo "✓ Python 3 and dependencies installed"

# Step 3: Clone repository
echo "[3/7] Cloning repository..."
cd ~
if [ -d "news" ]; then
    cd news
    git pull origin main
else
    git clone https://github.com/daijiong1977/news.git
    cd news
fi
echo "✓ Repository cloned/updated"

# Step 4: Create environment file
echo "[4/7] Setting up environment..."
if [ ! -f ".env" ]; then
    read -p "Enter your Deepseek API key: " API_KEY
    echo "DEEPSEEK_API_KEY=$API_KEY" > .env
    chmod 600 .env
    echo "✓ Environment file created"
else
    echo "✓ Environment file already exists"
fi

# Step 5: Initialize database
echo "[5/7] Initializing database..."
python3 init_db.py > /dev/null
echo "✓ Database initialized with fresh schema"

# Step 6: Create logs directory
echo "[6/7] Creating log directory..."
mkdir -p logs
echo "✓ Logs directory created"

# Step 7: Create processing loop script
echo "[7/7] Creating automated processing script..."
cat > process_articles_loop.sh << 'SCRIPT'
#!/bin/bash
cd ~/news
source .env

while true; do
    # Get count of unprocessed articles
    COUNT=$(sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=0;" 2>/dev/null || echo "0")
    
    if [ "$COUNT" -gt 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing article ($(($COUNT)) remaining)..."
        
        # Generate analysis
        python3 process_one_article.py >> logs/processor.log 2>&1
        
        # Get latest response file
        RESPONSE=$(ls -t response_article_*.json 2>/dev/null | head -1)
        
        if [ -n "$RESPONSE" ]; then
            # Insert into database
            python3 insert_from_response.py "$RESPONSE" >> logs/processor.log 2>&1
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Article processed and inserted"
            rm "$RESPONSE"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] No unprocessed articles. Collecting new articles..."
        python3 data_collector.py >> logs/collector.log 2>&1
    fi
    
    # Wait 5 minutes before checking again
    sleep 300
done
SCRIPT

chmod +x process_articles_loop.sh
echo "✓ Processing script created"

echo ""
echo "======================================================================="
echo "✓ EC2 SETUP COMPLETE!"
echo "======================================================================="
echo ""
echo "Database Location: ~/news/articles.db"
echo "Configuration: ~/news/config.json"
echo "API Key: ~/.env (KEEP SECURE)"
echo ""
echo "Next Steps:"
echo ""
echo "1. Collect articles:"
echo "   cd ~/news && python3 data_collector.py"
echo ""
echo "2. Test processing (single article):"
echo "   cd ~/news && python3 process_one_article.py"
echo ""
echo "3. Insert processed article:"
echo "   cd ~/news && python3 insert_from_response.py response_article_*.json"
echo ""
echo "4. Run automated loop (background):"
echo "   cd ~/news && nohup bash process_articles_loop.sh > logs/main.log 2>&1 &"
echo ""
echo "5. Check status:"
echo "   sqlite3 ~/news/articles.db \"SELECT COUNT(*) as total, SUM(deepseek_processed) as processed FROM articles;\""
echo ""
echo "======================================================================="
