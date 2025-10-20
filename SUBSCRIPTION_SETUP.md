# Email Subscription System for Daily Digest

This system allows users to subscribe to daily or weekly email digests of AI-powered article summaries.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (main_articles_interface_v2.html)                  │
│  - Email subscription form                                   │
│  - Shows frequency options (Daily/Weekly)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Subscription Service   │
        │ (subscription_service.py)
        │ Flask API              │
        │ - /subscribe           │
        │ - /unsubscribe         │
        │ - /send-digest         │
        │ - /health              │
        └────────┬───────────────┘
                 │
        ┌────────┴──────────────────┐
        ▼                           ▼
   ┌─────────────────┐      ┌──────────────────┐
   │  SQLite DB      │      │  Email API       │
   │ (subscriptions) │      │ (emailapi.6ray.com)
   │                 │      │ via X-API-Key    │
   └─────────────────┘      └──────────────────┘
        ▲
        │
   ┌────┴──────────────────┐
   │ Email Scheduler        │
   │ (email_scheduler.py)   │
   │ - Runs daily at 8 AM   │
   │ - Runs weekly Mondays  │
   └───────────────────────┘
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/jidai/news

pip install flask requests schedule
```

### 2. Configure Environment Variables

```bash
# Set your Email API credentials
export EMAIL_API_BASE_URL="https://emailapi.6ray.com"
export EMAIL_API_KEY="<your-key-id.secret>"  # From bootstrap endpoint
```

### 3. Start the Subscription Service

```bash
# Terminal 1: Start the subscription backend
python3 subscription_service.py
```

The service will:
- ✅ Initialize SQLite database with `subscriptions` and `email_logs` tables
- ✅ Listen on `http://localhost:5001`
- ✅ Handle subscription requests from the frontend

### 4. Start the Email Scheduler (Optional)

```bash
# Terminal 2: Start the email scheduler
python3 email_scheduler.py
```

The scheduler will:
- ✅ Send daily digest at **8:00 AM** every day
- ✅ Send weekly digest at **8:00 AM** every Monday
- ✅ Log results to console

### 5. Test Manually

```bash
# Test subscription
curl -X POST http://localhost:5001/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "frequency": "daily"
  }'

# Test sending digest
curl -X POST http://localhost:5001/send-digest \
  -H "Content-Type: application/json" \
  -d '{"frequency": "daily"}'
```

## Frontend Integration

The subscription form is now built into `main_articles_interface_v2.html`:

- 📧 Email input field
- 📅 Frequency selector (Daily/Weekly)
- ✓ Subscribe button
- ✓ Status messages (success/error)

When users submit:
1. Form sends request to `/subscribe`
2. Backend stores email + frequency in database
3. User sees confirmation message
4. Scheduler sends emails at configured times

## Database Schema

### subscriptions table
```sql
- id: Primary key
- email: User's email (unique)
- frequency: 'daily' or 'weekly'
- status: 'active' or 'inactive'
- category: Article category (world/science/tech/sports)
- created_at: Timestamp
- last_sent: Last digest timestamp
- confirmation_token: For future email verification
- confirmed: Boolean for double opt-in
```

### email_logs table
```sql
- id: Primary key
- email: Recipient
- subject: Email subject
- status: 'sent', 'failed', 'bounced'
- email_id: ID from Email API
- sent_at: Timestamp
```

## Email API Integration

This service uses the Email API at `https://emailapi.6ray.com`:

1. **Bootstrap a device key:**
```bash
curl -X POST https://emailapi.6ray.com/client/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"device_id":"daily-digest-server","display_name":"Daily Digest"}'
```

2. **Store the API key:**
```bash
export EMAIL_API_KEY="<key-from-response>"
```

3. **Emails sent with:**
   - `X-API-Key` header authentication
   - HTML digest template
   - Category filtering
   - Error logging

## Testing Scenarios

### Scenario 1: Test Daily Subscription
1. Visit `http://localhost:8000/main_articles_interface_v2.html`
2. Fill email + select "Daily"
3. Click Subscribe
4. Check success message
5. Query database: `SELECT * FROM subscriptions`

### Scenario 2: Test Email Sending
```bash
# Trigger manual send
curl -X POST http://localhost:5001/send-digest \
  -H "Content-Type: application/json" \
  -d '{"frequency": "daily"}'

# Check logs
SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;
```

### Scenario 3: Test Unsubscribe
```bash
curl -X POST "http://localhost:5001/unsubscribe?email=test@example.com"
```

## Production Deployment

For production:

1. **Use production Email API:**
   - Update `EMAIL_API_BASE_URL` to `https://emailapi.6ray.com`

2. **Run as service:**
```bash
# Use systemd or supervisor to run services
# Example systemd unit file:
[Unit]
Description=Daily Digest Subscription Service
After=network.target

[Service]
Type=simple
User=news
WorkingDirectory=/Users/jidai/news
Environment="EMAIL_API_KEY=..."
ExecStart=/usr/bin/python3 subscription_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Add database backup:**
```bash
# Daily backup
0 0 * * * cp /Users/jidai/news/subscriptions.db /backup/subscriptions_$(date +\%Y\%m\%d).db
```

4. **Monitor logs:**
```bash
# View subscription service logs
tail -f /var/log/daily-digest/subscription.log

# View email logs
SELECT * FROM email_logs WHERE status = 'failed' ORDER BY sent_at DESC;
```

## Troubleshooting

### Issue: "Email API key not configured"
- Set `EMAIL_API_KEY` environment variable
- Verify key format: `<key-id>.<secret>`

### Issue: "Connection refused"
- Ensure subscription service is running: `python3 subscription_service.py`
- Check port 5001 is not in use: `lsof -i :5001`

### Issue: "Email not sent"
- Check `email_logs` table for errors
- Verify recipient domain is not blocked
- Check Email API status: `curl https://emailapi.6ray.com/health`

### Issue: "Scheduler not running"
- Ensure scheduler process is running
- Check for cron alternative: use `nohup` or systemd

## Future Enhancements

- ✅ Category filtering (user chooses topics)
- ✅ Double opt-in verification
- ✅ Unsubscribe links in emails
- ✅ Bounce handling
- ✅ Digest preview before send
- ✅ Custom sender name/branding
- ✅ A/B testing subject lines
- ✅ Analytics dashboard

## Support

For issues or questions about the Email API, see `/Users/jidai/iphone/eamilapi/frontend.md`
