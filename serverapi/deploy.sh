#!/bin/bash
# Deployment script for News User API
# Run this on the server: bash serverapi/deploy.sh

set -e

echo "======================================"
echo "🚀 News API Deployment"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server
if [ ! -d "/var/www/news" ]; then
    echo -e "${RED}❌ Error: /var/www/news not found. Are you on the server?${NC}"
    exit 1
fi

cd /var/www/news

# Step 1: Stop and remove old services
echo -e "\n${YELLOW}Step 1: Removing old services...${NC}"

# Check for old HTML server on port 5001
if systemctl is-active --quiet news-html-server 2>/dev/null; then
    echo "  Stopping news-html-server..."
    sudo systemctl stop news-html-server
    sudo systemctl disable news-html-server
fi

# Remove old service file if exists
if [ -f "/etc/systemd/system/news-html-server.service" ]; then
    echo "  Removing old service file..."
    sudo rm /etc/systemd/system/news-html-server.service
fi

echo -e "${GREEN}✓ Old services removed${NC}"

# Step 2: Run database migration
echo -e "\n${YELLOW}Step 2: Running database migration...${NC}"
python3 dbinit/migrate_user_system.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migration completed${NC}"
else
    echo -e "${RED}❌ Database migration failed${NC}"
    exit 1
fi

# Step 3: Install Python dependencies
echo -e "\n${YELLOW}Step 3: Installing Python dependencies...${NC}"
pip3 install flask flask-cors requests

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Dependency installation failed${NC}"
    exit 1
fi

# Step 4: Install systemd service
echo -e "\n${YELLOW}Step 4: Installing systemd service...${NC}"
sudo cp serverapi/news-api.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Service file installed${NC}"

# Step 5: Start and enable service
echo -e "\n${YELLOW}Step 5: Starting API service...${NC}"
sudo systemctl enable news-api
sudo systemctl restart news-api

# Wait a moment for service to start
sleep 2

if systemctl is-active --quiet news-api; then
    echo -e "${GREEN}✓ API service is running${NC}"
else
    echo -e "${RED}❌ API service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u news-api -f"
    exit 1
fi

# Step 6: Check nginx configuration
echo -e "\n${YELLOW}Step 6: Checking nginx configuration...${NC}"

NGINX_CONF="/etc/nginx/sites-available/news.6ray.com"

if grep -q "location /api/" "$NGINX_CONF" 2>/dev/null; then
    echo -e "${GREEN}✓ Nginx /api/ proxy already configured${NC}"
else
    echo -e "${YELLOW}⚠️  Adding /api/ proxy to nginx configuration...${NC}"
    
    # Backup nginx config
    sudo cp "$NGINX_CONF" "${NGINX_CONF}.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Add proxy configuration (insert before the last closing brace)
    sudo sed -i '/^}/i \    # API Proxy\n    location /api/ {\n        proxy_pass http://127.0.0.1:5001;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto https;\n    }\n' "$NGINX_CONF"
    
    echo -e "${GREEN}✓ Nginx configuration updated${NC}"
    echo -e "${YELLOW}  Reloading nginx...${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
fi

# Step 7: Test API
echo -e "\n${YELLOW}Step 7: Testing API endpoints...${NC}"

# Wait for API to be ready
sleep 2

# Test health endpoint
if curl -s http://localhost:5001/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    exit 1
fi

# Step 8: Run full test suite
echo -e "\n${YELLOW}Step 8: Running full test suite...${NC}"
python3 serverapi/test_api.py http://localhost:5001 didadi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed (check test report)${NC}"
fi

# Final summary
echo -e "\n======================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "======================================"
echo ""
echo "Service Status:"
echo "  sudo systemctl status news-api"
echo ""
echo "View Logs:"
echo "  sudo journalctl -u news-api -f"
echo ""
echo "API Endpoints:"
echo "  https://news.6ray.com/api/health"
echo "  https://news.6ray.com/api/user/register"
echo "  https://news.6ray.com/api/admin/stats"
echo ""
echo "Test API:"
echo "  python3 serverapi/test_api.py https://news.6ray.com didadi"
echo ""
echo "======================================"
