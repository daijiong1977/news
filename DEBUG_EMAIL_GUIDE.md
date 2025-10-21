# EC2 Email Debug Guide

## Quick Start

Run this command on your EC2 server to diagnose email issues:

```bash
cd /var/www/news
bash debug_email_ec2.sh
```

## What It Checks

✅ **Environment Variables** - Are EMAIL_API_KEY and DEEPSEEK_API_KEY set?  
✅ **.env File** - Does it exist? Can it be read?  
✅ **Database** - Is articles.db accessible with proper tables?  
✅ **Python Modules** - Are required imports available?  
✅ **API Endpoint** - Can we reach emailapi.6ray.com?  
✅ **Cron Jobs** - Are pipeline jobs scheduled?  
✅ **Systemd Services** - Any pipeline services running?  
✅ **Recent Logs** - What happened in the last pipeline run?  
✅ **Email Script** - Can send_email_report.sh execute?  

## Expected Output

### If Everything is Working ✅

```
[1] Checking Environment Variables...
----
✓ EMAIL_API_KEY is set in current session (length: 32)
✓ DEEPSEEK_API_KEY is set in current session (length: 48)

[2] Checking .env File...
----
✓ .env file exists at: /var/www/news/.env

  Content (sensitive values masked):
    DEEPSEEK_API_KEY = key...key
    EMAIL_API_KEY = key...key
    EMAIL_RECIPIENT = jidai@6ray.com

[3] Checking Database...
----
✓ Database exists: articles.db
    articles                  =    20 records
    article_summaries         =    80 records
    keywords                  =   600 records
    questions                 =   600 records
    comments                  =   180 records
    background_read           =    60 records
    article_analysis          =    40 records

[4] Testing Python Email Script...
----
Test 1: Checking Python imports...
  ✓ sqlite3 available
  ✓ json available
  ✓ urllib available

Test 2: Checking API Keys...
  ✓ EMAIL_API_KEY found (length: 32)
  ✓ DEEPSEEK_API_KEY found (length: 48)
  ✓ EMAIL_RECIPIENT: jidai@6ray.com

Test 3: Checking Email API Endpoint...
  Testing endpoint: https://emailapi.6ray.com/send-email
  Recipient: jidai@6ray.com
  ✓ Email API working!
    Status: 200
    Response: {'email_id': '...', 'status': 'sent'}
```

### If EMAIL_API_KEY is Missing ✗

```
[1] Checking Environment Variables...
----
✗ EMAIL_API_KEY is NOT set in current session
✗ DEEPSEEK_API_KEY is NOT set in current session

[2] Checking .env File...
----
✗ .env file NOT found at: /var/www/news/.env
```

**Solution**: Create `.env` file:
```bash
sudo cat > /var/www/news/.env << 'EOF'
DEEPSEEK_API_KEY=your-deepseek-key
EMAIL_API_KEY=your-email-api-key
EMAIL_RECIPIENT=jidai@6ray.com
EOF

sudo chmod 600 /var/www/news/.env
```

## Step-by-Step Debugging

### Step 1: SSH to EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
cd /var/www/news
```

### Step 2: Run Debug Script
```bash
bash debug_email_ec2.sh 2>&1 | tee debug_output.log
```

### Step 3: Check Environment Manually
```bash
# Check if .env exists
ls -la .env

# View .env (carefully - has secrets!)
cat .env

# Source .env and verify
source .env
echo "EMAIL_API_KEY=$EMAIL_API_KEY"
echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY"
```

### Step 4: Test Email Sending Directly
```bash
cd /var/www/news
source .env
python3 send_email_report.sh
```

### Step 5: Check Cron Logs
```bash
# View syslog for cron errors
sudo tail -50 /var/log/syslog | grep CRON

# Check if cron job is set
crontab -l

# Check cron environment
env | grep -E "EMAIL|DEEPSEEK"
```

### Step 6: Test Cron Directly
```bash
# Run the pipeline script manually
cd /var/www/news
bash daily_pipeline.sh

# Check if email was sent
tail -50 logs/daily_pipeline_*.log | grep -A 5 "SEND"
```

## Common Issues and Fixes

### Issue 1: ".env: No such file or directory"

**Cause**: .env file doesn't exist

**Fix**:
```bash
sudo cat > /var/www/news/.env << 'EOF'
DEEPSEEK_API_KEY=your-key
EMAIL_API_KEY=your-key
EMAIL_RECIPIENT=jidai@6ray.com
EOF
```

### Issue 2: "EMAIL_API_KEY not set"

**Cause**: Environment variable not loaded by cron

**Fix**:
```bash
# Edit crontab
sudo crontab -e

# Change this:
0 1 * * * /var/www/news/daily_pipeline.sh

# To this:
0 1 * * * cd /var/www/news && source .env && bash daily_pipeline.sh
```

### Issue 3: "Permission denied"

**Cause**: .env file has wrong permissions

**Fix**:
```bash
sudo chmod 600 /var/www/news/.env
sudo chown www-data:www-data /var/www/news/.env  # or your cron user
```

### Issue 4: "Connection refused" on email API

**Cause**: Network issue or API endpoint down

**Fix**:
```bash
# Test connectivity
curl -I https://emailapi.6ray.com/send-email

# Check DNS
nslookup emailapi.6ray.com

# Test with telnet
telnet emailapi.6ray.com 443
```

### Issue 5: "Authentication failed"

**Cause**: Invalid API key

**Fix**:
```bash
# Verify API key is correct
grep EMAIL_API_KEY /var/www/news/.env

# Test with curl
curl -X POST https://emailapi.6ray.com/send-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -d '{"to_email":"test@example.com","subject":"Test","message":"Test"}'
```

## Permanent Fix: Source .env in Crontab

Edit crontab:
```bash
sudo crontab -e
```

Add these lines at the top:
```bash
# Source environment variables
SHELL=/bin/bash
BASH_ENV=/var/www/news/.env

# Daily pipeline at 1 AM
0 1 * * * cd /var/www/news && bash daily_pipeline.sh
```

Or add environment directly:
```bash
DEEPSEEK_API_KEY=your-key
EMAIL_API_KEY=your-key
0 1 * * * cd /var/www/news && bash daily_pipeline.sh
```

## Files to Check

```
/var/www/news/
├── .env                          # Environment variables
├── daily_pipeline.sh             # Main pipeline script
├── send_email_report.sh          # Email sending script
├── articles.db                   # SQLite database
├── logs/
│   ├── daily_pipeline_*.log      # Pipeline execution logs
│   └── ...
└── debug_email_ec2.sh            # This debug script
```

## Quick Commands

```bash
# Test environment
source /var/www/news/.env && echo "API Key: $EMAIL_API_KEY"

# Test database access
sqlite3 /var/www/news/articles.db "SELECT COUNT(*) FROM articles;"

# Test email endpoint
curl -X POST https://emailapi.6ray.com/send-email \
  -H "X-API-Key: $EMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"to_email":"test@example.com","subject":"Test","message":"Test"}'

# Run pipeline manually
cd /var/www/news && bash daily_pipeline.sh 2>&1 | tee test_run.log

# Check last email attempt
grep -r "Email sent\|Failed" /var/www/news/logs/
```

## Need Help?

If debug script shows issues:

1. **Save output**: `bash debug_email_ec2.sh > debug.txt 2>&1`
2. **Share the output** with your DevOps team
3. **Check log files**: `tail -100 /var/www/news/logs/daily_pipeline_*.log`
4. **Check syslog**: `sudo tail -100 /var/log/syslog | grep -A 5 -B 5 "news\|pipeline\|email"`

---

**Run the debug script and let me know what output you get!** 🚀
