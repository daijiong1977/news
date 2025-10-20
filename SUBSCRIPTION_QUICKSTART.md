# 🚀 Quick Start: Email Subscription System

## What's New

Your Daily Digest page now has a **full email subscription system** integrated with the Email API!

## ⚡ Quick Setup (5 minutes)

### Step 1: Get Email API Key
```bash
# Bootstrap a device key
curl -X POST https://emailapi.6ray.com/client/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"device_id":"daily-digest-server","display_name":"Daily Digest"}' \
  | python -m json.tool
```

Copy the `api_key` from response (format: `key_id.secret`)

### Step 2: Install Dependencies
```bash
cd /Users/jidai/news
pip install flask requests schedule
```

### Step 3: Set Environment Variables
```bash
export EMAIL_API_BASE_URL="https://emailapi.6ray.com"
export EMAIL_API_KEY="<paste-your-key-here>"
```

### Step 4: Start Services

**Terminal 1 - Subscription Backend:**
```bash
cd /Users/jidai/news
python3 subscription_service.py
```

**Terminal 2 - Email Scheduler (optional):**
```bash
cd /Users/jidai/news
python3 email_scheduler.py
```

### Step 5: Test It!

Visit: **http://localhost:8000/main_articles_interface_v2.html**

You should see the **"📧 Subscribe to Daily Digest"** form!

## ✨ Features

✅ **Email Subscription Form**
- Email input field
- Daily/Weekly frequency choice
- Real-time feedback

✅ **Automatic Digest Sending**
- Daily digest at 8:00 AM
- Weekly digest every Monday
- HTML formatted emails

✅ **Database Storage**
- SQLite database (`subscriptions.db`)
- Tracks subscribers and send history
- Easy to query and backup

✅ **Email API Integration**
- Uses your Email API credentials
- Secure authentication with API key
- Detailed logging and error tracking

## 📊 What Happens When User Subscribes

```
User fills form
     ↓
Click "Subscribe"
     ↓
Form data → Backend API (/subscribe)
     ↓
Backend stores in database
     ↓
User sees success message
     ↓
Scheduler runs at configured time
     ↓
Backend queries database for subscribers
     ↓
Generates HTML digest with articles
     ↓
Sends via Email API
     ↓
Logs result to email_logs table
```

## 🧪 Test Commands

### Test Subscription
```bash
curl -X POST http://localhost:5001/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "frequency": "daily"
  }'
```

### Check Subscriptions
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT email, frequency, status FROM subscriptions;"
```

### Manual Send
```bash
curl -X POST http://localhost:5001/send-digest \
  -H "Content-Type: application/json" \
  -d '{"frequency": "daily"}'
```

### Check Email Logs
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;"
```

## 📁 New Files Created

- `subscription_service.py` - Flask backend API
- `email_scheduler.py` - Automatic digest scheduler
- `subscriptions.db` - SQLite database (created on first run)
- `SUBSCRIPTION_SETUP.md` - Full documentation

## 🔧 Configuration

### Change Send Times
Edit `email_scheduler.py`:
```python
# Line 52-53:
schedule.every().day.at("06:00").do(send_daily_digest)  # Change 08:00 to 06:00
schedule.every().monday.at("09:00").do(send_weekly_digest)  # Change time
```

### Change Email Template
Edit `subscription_service.py`, function `generate_digest_html()` (around line 115)

### Add More Categories
Edit `subscription_service.py`, function `categoryMap` (around line 55):
```python
categoryMap = {
    'world': ['PBS', 'pbs'],
    'science': ['Science Daily', 'science'],
    'tech': ['TechRadar', 'tech'],
    'sports': ['Swimming', 'swim'],
    'your-category': ['keyword1', 'keyword2']  # Add here
}
```

## ✅ Verification Checklist

- [ ] Email API key obtained and set
- [ ] Dependencies installed (`pip install flask requests schedule`)
- [ ] Subscription service running on port 5001
- [ ] Subscription form visible on main page
- [ ] Can successfully subscribe (check database)
- [ ] Email logs show successful sends
- [ ] Scheduler running and sending at right times

## 🆘 Troubleshooting

**"Connection refused" error?**
- Ensure subscription service is running
- Check port: `lsof -i :5001`

**"Email API key error"?**
- Verify environment variable: `echo $EMAIL_API_KEY`
- Bootstrap new key if needed

**Form not working?**
- Check browser console for errors
- Ensure localhost:5001 is accessible
- Check `subscription_service.py` logs

**Emails not sending?**
- Check `email_logs` table for errors
- Verify Email API status
- Check subscriber count: `SELECT COUNT(*) FROM subscriptions WHERE status='active';`

## 📞 Need Help?

See detailed docs: `/Users/jidai/news/SUBSCRIPTION_SETUP.md`

Email API docs: `/Users/jidai/iphone/eamilapi/frontend.md`
