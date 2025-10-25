#!/bin/bash

# Debug Email Pipeline on EC2 Server
# Run this script to troubleshoot EMAIL_API_KEY and email sending issues

echo "======================================================================="
echo "EMAIL PIPELINE DEBUG - EC2 SERVER"
echo "======================================================================="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo ""

# Check 1: Environment variables
echo "[1] Checking Environment Variables..."
echo "----"
if [ -z "$EMAIL_API_KEY" ]; then
    echo "✗ EMAIL_API_KEY is NOT set in current session"
else
    echo "✓ EMAIL_API_KEY is set in current session (length: ${#EMAIL_API_KEY})"
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "✗ DEEPSEEK_API_KEY is NOT set in current session"
else
    echo "✓ DEEPSEEK_API_KEY is set in current session (length: ${#DEEPSEEK_API_KEY})"
fi

echo ""
echo "[2] Checking .env File..."
echo "----"
WORK_DIR="/var/www/news"

if [ -f "$WORK_DIR/.env" ]; then
    echo "✓ .env file exists at: $WORK_DIR/.env"
    echo ""
    echo "  Content (sensitive values masked):"
    grep -E "^(DEEPSEEK_API_KEY|EMAIL_API_KEY|EMAIL_RECIPIENT)" "$WORK_DIR/.env" | while IFS='=' read -r key value; do
        if [ -z "$value" ]; then
            echo "    $key = (empty)"
        else
            masked="${value:0:3}...${value: -3}"
            echo "    $key = $masked"
        fi
    done
else
    echo "✗ .env file NOT found at: $WORK_DIR/.env"
    echo "  Create it with: cat > $WORK_DIR/.env << 'EOF'"
    echo "  DEEPSEEK_API_KEY=your-key"
    echo "  EMAIL_API_KEY=your-key"
    echo "  EMAIL_RECIPIENT=your-email@example.com"
    echo "  EOF"
fi

echo ""
echo "[3] Checking Database..."
echo "----"
cd "$WORK_DIR" 2>/dev/null || { echo "✗ Cannot cd to $WORK_DIR"; exit 1; }

if [ -f "articles.db" ]; then
    echo "✓ Database exists: articles.db"
    
    # Check table counts
    python3 << 'PYEOF'
import sqlite3

try:
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    
    tables = ['articles', 'article_summaries', 'keywords', 'questions', 'comments', 'background_read', 'article_analysis']
    
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"    {table:25} = {count:5} records")
    
    conn.close()
except Exception as e:
    print(f"  ✗ Error reading database: {e}")
PYEOF
else
    echo "✗ Database NOT found: articles.db"
fi

echo ""
echo "[4] Testing Python Email Script..."
echo "----"

# Create a test Python script
python3 << 'PYEOF'
import os
import sys

print("Python version:", sys.version)
print("")

# Test 1: Check imports
print("Test 1: Checking Python imports...")
try:
    import sqlite3
    print("  ✓ sqlite3 available")
except:
    print("  ✗ sqlite3 NOT available")

try:
    import json
    print("  ✓ json available")
except:
    print("  ✗ json NOT available")

try:
    import urllib.request
    print("  ✓ urllib available")
except:
    print("  ✗ urllib NOT available")

print("")
print("Test 2: Checking API Keys...")

email_api_key = os.environ.get('EMAIL_API_KEY')
deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')
recipient = os.environ.get('EMAIL_RECIPIENT', 'jidai@6ray.com')

if email_api_key:
    print(f"  ✓ EMAIL_API_KEY found (length: {len(email_api_key)})")
else:
    print("  ✗ EMAIL_API_KEY NOT found")
    print("    Try: export EMAIL_API_KEY='your-key'")

if deepseek_api_key:
    print(f"  ✓ DEEPSEEK_API_KEY found (length: {len(deepseek_api_key)})")
else:
    print("  ✗ DEEPSEEK_API_KEY NOT found")

print(f"  ✓ EMAIL_RECIPIENT: {recipient}")

print("")
print("Test 3: Checking Email API Endpoint...")
try:
    import urllib.request
    import json
    
    test_payload = {
        "to_email": recipient,
        "subject": "TEST: News Pipeline Debug",
        "message": "This is a test email from the debug script",
        "from_name": "News Pipeline Debug"
    }
    
    if not email_api_key:
        print("  ✗ Cannot test: EMAIL_API_KEY not set")
    else:
        print(f"  Testing endpoint: https://emailapi.6ray.com/send-email")
        print(f"  Recipient: {recipient}")
        
        data = json.dumps(test_payload).encode('utf-8')
        req = urllib.request.Request('https://emailapi.6ray.com/send-email', data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-API-Key', email_api_key)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if response.status == 200:
                    print(f"  ✓ Email API working!")
                    print(f"    Status: {response.status}")
                    print(f"    Response: {result}")
                else:
                    print(f"  ✗ Email API returned status: {response.status}")
                    print(f"    Response: {result}")
        except urllib.error.URLError as e:
            print(f"  ✗ Network error: {e.reason}")
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP Error: {e.code}")
            try:
                print(f"    Response: {e.read().decode('utf-8')}")
            except:
                pass
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}")
            
except Exception as e:
    print(f"  ✗ Error during test: {e}")

PYEOF

echo ""
echo "[5] Checking Cron Jobs..."
echo "----"
crontab -l 2>/dev/null | grep -E "news|pipeline" || echo "  No news/pipeline cron jobs found"

echo ""
echo "[6] Checking Systemd Services..."
echo "----"
systemctl list-units --all --plain | grep -E "news|pipeline" || echo "  No news/pipeline systemd services found"

echo ""
echo "[7] Checking Recent Logs..."
echo "----"

if [ -f "$WORK_DIR/logs/daily_pipeline_latest.log" ]; then
    echo "✓ Latest pipeline log found"
    echo ""
    tail -20 "$WORK_DIR/logs/daily_pipeline_latest.log"
else
    echo "✗ No pipeline logs found"
    if [ -d "$WORK_DIR/logs" ]; then
        echo "  Available logs:"
        ls -lh "$WORK_DIR/logs/" | tail -5
    fi
fi

echo ""
echo "[8] Testing send_email_report.sh Script..."
echo "----"

if [ -f "$WORK_DIR/send_email_report.sh" ]; then
    echo "✓ send_email_report.sh exists"
    echo "  Running test..."
    cd "$WORK_DIR"
    bash send_email_report.sh 2>&1 | head -20
else
    echo "✗ send_email_report.sh NOT found"
fi

echo ""
echo "======================================================================="
echo "DEBUG COMPLETE"
echo "======================================================================="
echo ""
echo "Summary:"
echo "--------"
echo "If EMAIL_API_KEY is not set above:"
echo "  1. Check .env file exists at $WORK_DIR/.env"
echo "  2. Verify EMAIL_API_KEY is in .env"
echo "  3. Run: source $WORK_DIR/.env"
echo "  4. Run: env | grep EMAIL_API_KEY"
echo ""
echo "If cron job is not working:"
echo "  1. Check /var/log/syslog for cron errors"
echo "  2. Verify .env is readable by cron user"
echo "  3. Add environment vars to crontab -e"
echo ""
echo "To manually test email sending:"
echo "  cd $WORK_DIR"
echo "  source .env"
echo "  bash send_email_report.sh"
echo ""
