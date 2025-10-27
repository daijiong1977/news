# Server Deployment Checklist

## Overview
This document outlines the deployment steps for the News User API server, replacing the old HTML server on port 5001.

## Pre-Deployment Summary

### What's Being Deployed
- **New Service**: `news-api` (Flask REST API)
- **Port**: 5001 (replacing old HTML server)
- **Features**:
  - User subscription management (register, token recovery, stats sync)
  - Admin panel data endpoints (feeds, categories, articles, API keys, stats)
  - Cron job management (status, enable/disable, logs)

### What's Being Removed
- **Old Service**: `news-html-server` (Python HTTP server)
- **Old Service File**: `/etc/systemd/system/news-html-server.service`

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# On server (news.6ray.com)
cd /var/www/news

# Pull latest code
git pull origin main

# Run deployment script
bash serverapi/deploy.sh
```

The script will:
1. ✅ Stop and remove old HTML server service
2. ✅ Run database migration (user_subscriptions, user_stats_sync tables)
3. ✅ Install Python dependencies (Flask, Flask-CORS, requests)
4. ✅ Install and start news-api systemd service
5. ✅ Configure nginx proxy for /api/ routes
6. ✅ Run full API test suite
7. ✅ Generate test report

### Method 2: Manual Deployment

See `serverapi/README.md` for step-by-step manual deployment instructions.

## Testing

### Automated Testing

```bash
# Run full test suite
python3 serverapi/test_api.py https://news.6ray.com didadi
```

Test coverage:
- ✅ Public endpoints (health, register, token recovery, stats sync)
- ✅ Admin endpoints (feeds, categories, articles, API keys, stats)
- ✅ Cron management (status, logs)
- ✅ Generates JSON report with pass/fail results

### Manual Testing

```bash
# Test health check
curl https://news.6ray.com/api/health

# Test admin endpoint
curl -X GET https://news.6ray.com/api/admin/stats \
  -H "X-Admin-Password: didadi"
```

## Post-Deployment Verification

### 1. Check Service Status

```bash
sudo systemctl status news-api
```

Expected: `Active: active (running)`

### 2. Check Logs

```bash
sudo journalctl -u news-api -f
```

Expected: No error messages

### 3. Test Admin Panel

1. Open https://news.6ray.com/website/admin.html
2. Login with password: `didadi`
3. Navigate through tabs:
   - Feeds (should load RSS feeds)
   - Categories (should load categories)
   - Articles (should load articles)
   - API Keys (should load keys)
   - Statistics (should show stats)
   - Cron Jobs (should show current cron status)

### 4. Test User Registration

```bash
curl -X POST https://news.6ray.com/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "reading_style": "enjoy"
  }'
```

Expected: JSON response with `user_id` and `bootstrap_token`

## Rollback Plan

If deployment fails:

```bash
# Stop new service
sudo systemctl stop news-api

# Restore old HTML server (if backup exists)
# (You may need to restore from backup or redeploy old version)

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

## Database Changes

### New Tables (from migration)

1. **user_subscriptions**
   - Stores email subscribers with bootstrap tokens
   - Fields: user_id, email, name, reading_style, bootstrap_token, verified, etc.

2. **user_stats_sync**
   - Optional cloud backup of user activity statistics
   - Fields: user_id, stats_json, last_sync

### Migration Verification

```bash
# Check if tables exist
sqlite3 /var/www/news/articles.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'user_%';"
```

Expected output:
```
user_subscriptions
user_stats_sync
user_difficulty_levels
user_categories
user_preferences
user_awards
```

## Service Management Commands

```bash
# Start service
sudo systemctl start news-api

# Stop service
sudo systemctl stop news-api

# Restart service
sudo systemctl restart news-api

# Enable auto-start
sudo systemctl enable news-api

# Disable auto-start
sudo systemctl disable news-api

# View status
sudo systemctl status news-api

# View logs (real-time)
sudo journalctl -u news-api -f

# View logs (last 100 lines)
sudo journalctl -u news-api -n 100
```

## Nginx Configuration

The deployment script adds this to nginx config:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
}
```

### Verify Nginx Config

```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

## Troubleshooting

### API Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u news-api -n 50

# Common issues:
# - Port 5001 already in use
# - Missing Python dependencies
# - Database file not found
# - Permission issues
```

### Admin Panel Can't Connect

```bash
# Check nginx proxy configuration
sudo nginx -t

# Check if API is responding locally
curl http://localhost:5001/api/health

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Database Migration Failed

```bash
# Run migration manually
python3 /var/www/news/dbinit/migrate_user_system.py

# Check database integrity
sqlite3 /var/www/news/articles.db "PRAGMA integrity_check;"
```

## Success Criteria

Deployment is successful when:

- ✅ `systemctl status news-api` shows `Active: active (running)`
- ✅ `curl http://localhost:5001/api/health` returns `{"status": "healthy"}`
- ✅ Admin panel at https://news.6ray.com/website/admin.html loads and functions
- ✅ All tabs in admin panel display data correctly
- ✅ Test suite passes: `python3 serverapi/test_api.py https://news.6ray.com didadi`
- ✅ No errors in `sudo journalctl -u news-api -n 100`

## Contact

If you encounter issues during deployment, check:
1. Service logs: `sudo journalctl -u news-api -f`
2. Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Test report: `test_report_*.json` in project directory

---

**Last Updated**: 2025-10-26
