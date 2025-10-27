# Server API Directory

This directory contains all server-side API endpoints for the News Oh,Ye! platform.

## Files

### `user_api.py`
Flask backend for user subscription management and admin panel.

**Port:** 5001 (replacing old HTML server)

**Endpoints:**

#### Public Endpoints:
- `GET /api/device/generate` - Generate unique device_id for tracking (works for anonymous users)
- `POST /api/user/register` - Register new user with emailapi bootstrap
- `POST /api/user/token` - Recover bootstrap token by email
- `POST /api/user/sync-stats` - Sync user statistics (requires X-User-Token header)
- `GET /api/verify?token=xxx` - Verify email address (from email link)
- `GET /api/health` - Health check

#### Admin Endpoints (require X-Admin-Password header):

**User Subscriptions:**
- `GET /api/admin/subscriptions` - List all subscriptions
- `GET /api/admin/subscriptions/export` - Export email list as JSON

**Admin Panel Data:**
- `GET /api/admin/feeds` - Get all RSS feeds with categories
- `GET /api/admin/categories` - Get all categories
- `GET /api/admin/articles?limit=50&offset=0&source=BBC&processed=all&date=2025-10-26` - Get articles with filters
- `GET /api/admin/apikeys` - Get all API keys
- `GET /api/admin/stats` - Get system statistics (articles, sources, processing status)
- `GET /api/admin/article/<article_id>` - Get detailed article info with all related data

**Cron Job Management:**
- `GET /api/cron/status` - Get current cron job configuration and status
- `POST /api/cron/enable` - Enable/update cron job with settings (hour, minute, articles_per_seed)
- `POST /api/cron/disable` - Disable cron job
- `GET /api/cron/logs` - Get list of cron log files
- `GET /api/cron/logs/<filename>` - Get content of specific log file

## Configuration

### Environment Variables

```bash
# Email API URL (default: https://emailapi.6ray.com)
EMAIL_API_URL=https://emailapi.6ray.com

# Admin password (default: didadi)
ADMIN_PASSWORD=didadi

# CORS Configuration (optional - for GitHub Pages migration)
ENABLE_CORS=false
GITHUB_PAGES_URL=https://username.github.io
```

### Database

The API uses `/Users/jidai/news/articles.db` (SQLite3) with these tables:
- `user_subscriptions` - Email subscribers
- `user_stats_sync` - Optional stats backup

## Running Locally

```bash
# Install dependencies
pip install flask flask-cors requests

# Run server
cd /Users/jidai/news
python3 serverapi/user_api.py
```

Server will start on `http://localhost:5001`

## Deploying to Server

### Quick Deploy (Recommended)

```bash
# On server (news.6ray.com)
cd /var/www/news
bash serverapi/deploy.sh
```

The deployment script will:
1. Stop and remove old HTML server service (port 5001)
2. Run database migration
3. Install dependencies
4. Install and start news-api service
5. Configure nginx proxy
6. Run full test suite

### Manual Deploy

### Manual Deploy

### 1. Copy to Server

```bash
scp -r serverapi/ user@news.6ray.com:/var/www/news/
```

### 2. Stop Old HTML Server

```bash
ssh user@news.6ray.com
sudo systemctl stop news-html-server
sudo systemctl disable news-html-server
sudo rm /etc/systemd/system/news-html-server.service
```

### 3. Run Migration

```bash
ssh user@news.6ray.com
cd /var/www/news
python3 dbinit/migrate_user_system.py
```

### 4. Install Dependencies

```bash
pip3 install flask flask-cors requests
```

### 4. Install Dependencies

```bash
pip3 install flask flask-cors requests
```

### 5. Install Systemd Service

Copy `serverapi/news-api.service` to systemd:

```bash
sudo cp serverapi/news-api.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 6. Start Service

### 6. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable news-api
sudo systemctl start news-api
sudo systemctl status news-api
```

### 7. Configure Nginx

Add to nginx config:

```nginx
# Proxy API requests
location /api/ {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
}
```

Reload nginx:
```bash
sudo systemctl reload nginx
```

### 8. Test API

```bash
# Run test suite
python3 serverapi/test_api.py https://news.6ray.com didadi

# Or test manually
curl https://news.6ray.com/api/health
```

## Testing

### Run Full Test Suite

```bash
# Local testing
python3 serverapi/test_api.py http://localhost:5001 didadi

# Production testing
python3 serverapi/test_api.py https://news.6ray.com didadi
```

The test script will:
- Test all public endpoints (health, register, token recovery, stats sync)
- Test all admin endpoints (feeds, categories, articles, API keys, stats, cron management)
- Generate a detailed JSON report
- Return exit code 0 if all tests pass

### Manual Testing

### Test Device ID Generation

```bash
# Generate device_id (works for anonymous users)
curl -X GET http://localhost:5001/api/device/generate
```

**Response:**
```json
{
  "success": true,
  "device_id": "news-a1b2c3d4e5f6g7h8i9j0"
}
```

**Usage:**
- Called automatically on first page load
- Stored in localStorage as `news_device_id`
- Used for anonymous user tracking
- Required for user registration (sent to emailapi)
- Enables offline token regeneration

### Test Registration

```bash
curl -X POST http://localhost:5001/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "reading_style": "enjoy"
  }'
```

### Test Token Recovery

```bash
curl -X POST http://localhost:5001/api/user/token \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Test Stats Sync

```bash
curl -X POST http://localhost:5001/api/user/sync-stats \
  -H "Content-Type: application/json" \
  -H "X-User-Token: your-bootstrap-token" \
  -d '{
    "stats": {
      "word_article123_test": {"completed": true, "timestamp": 1234567890}
    }
  }'
```

### Test Admin Endpoints

```bash
# Get all feeds
curl -X GET http://localhost:5001/api/admin/feeds \
  -H "X-Admin-Password: didadi"

# Get all categories
curl -X GET http://localhost:5001/api/admin/categories \
  -H "X-Admin-Password: didadi"

# Get articles with filters
curl -X GET "http://localhost:5001/api/admin/articles?limit=10&processed=true" \
  -H "X-Admin-Password: didadi"

# Get system statistics
curl -X GET http://localhost:5001/api/admin/stats \
  -H "X-Admin-Password: didadi"

# Get article detail
curl -X GET http://localhost:5001/api/admin/article/20251024001 \
  -H "X-Admin-Password: didadi"

# Get subscriptions list
curl -X GET http://localhost:5001/api/admin/subscriptions \
  -H "X-Admin-Password: didadi"

# Get cron job status
curl -X GET http://localhost:5001/api/cron/status \
  -H "X-Admin-Password: didadi"

# Enable cron job (daily at 13:00 with 3 articles per feed)
curl -X POST http://localhost:5001/api/cron/enable \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: didadi" \
  -d '{"hour": 13, "minute": 0, "articles_per_seed": 3}'

# Disable cron job
curl -X POST http://localhost:5001/api/cron/disable \
  -H "X-Admin-Password: didadi"

# Get cron logs
curl -X GET http://localhost:5001/api/cron/logs \
  -H "X-Admin-Password: didadi"
```

## GitHub Pages Migration (Optional)

When ready to host statistics on GitHub Pages:

1. Set environment variables:
```bash
export ENABLE_CORS=true
export GITHUB_PAGES_URL=https://yourusername.github.io
```

2. Restart service:
```bash
sudo systemctl restart news-user-api
```

3. Update frontend to call `https://news.6ray.com/api/*` from GitHub Pages

## Logs

```bash
# View service logs
sudo journalctl -u news-api -f

# View recent errors
sudo journalctl -u news-api -p err --since today
```
sudo journalctl -u news-user-api -n 50 --no-pager
```

## Server Load Analysis

| Endpoint | Expected Frequency | Server Impact |
|----------|-------------------|---------------|
| `/api/user/register` | Once per user | ⚠️ Low (rare) |
| `/api/user/token` | Rare (token loss) | ⚠️ Minimal |
| `/api/user/sync-stats` | User-initiated | ⚠️ Low (batched) |
| `/api/verify` | Once per user | ⚠️ Minimal |
| `/api/admin/*` | Admin only | ⚠️ Minimal |

**Total Load:** ~5-10 requests per user lifetime ✅
