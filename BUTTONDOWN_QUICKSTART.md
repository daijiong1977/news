# Quick Start: Setup & Send Multi-Level Emails

## Prerequisites

You need your Buttondown API token. Get it from:
https://buttondown.email/settings/api

## Step 1: Set API Token

### Option A: Interactive Setup
```bash
bash setup_buttondown_token.sh
```

Then enter your API token when prompted.

### Option B: Manual Setup
```bash
echo "BUTTONDOWN_API_TOKEN=your_actual_token_here" > .env
```

## Step 2: Create Test Subscribers

```bash
python3 buttondown_subscriber_manager.py
```

This will:
1. ✅ List all current subscribers
2. ✅ Create 4 test subscribers:
   - easy@daijiong.com (Level: Easy)
   - mid@daijiong.com (Level: Middle)
   - diff@daijiong.com (Level: Hard)
   - cn@daijiong.com (Level: Chinese)
3. 🧹 Clean up all other subscribers (asks for confirmation)
4. 🔍 Verify the final setup

## Step 3: Prepare Campaigns

```bash
python3 buttondown_send_campaigns.py
```

This will:
1. 📧 Create 4 email drafts (one per level)
2. 📋 Print detailed sending instructions
3. Show draft IDs for reference

## Step 4: Send Campaigns (Manual via Buttondown Dashboard)

1. Go to https://buttondown.email/dashboard
2. Go to **Emails** section
3. Find each draft by subject line
4. Click **Send**
5. Choose **Send to specific subscribers**
6. Filter by tag (Level: Easy, Level: Middle, etc.)
7. Click **Send!**

## Expected Results

Each test subscriber receives their appropriate level:

| Email | Receives | Content Type |
|-------|----------|--------------|
| easy@daijiong.com | email_enhanced_easy.html | 🟢 Beginner-friendly |
| mid@daijiong.com | email_enhanced_mid.html | 🔵 Intermediate |
| diff@daijiong.com | email_enhanced_hard.html | 🟠 Expert-level |
| cn@daijiong.com | email_enhanced_CN.html | 🔴 中文版本 |

## Troubleshooting

### "BUTTONDOWN_API_TOKEN not set"
```bash
export BUTTONDOWN_API_TOKEN='your_token_here'
python3 buttondown_subscriber_manager.py
```

### "API Error: Invalid token"
- Check token is correct: https://buttondown.email/settings/api
- Make sure it's set: `echo $BUTTONDOWN_API_TOKEN`

### Subscribers not receiving emails
- Verify they have the correct tag
- Dashboard → Subscribers → Check tags for each email
- Verify campaign tag filter matches

### Images not showing in email
- Check image URLs in HTML files
- Must update from `localhost:8000` to production domain
- Edit `generate_enhanced_email.py` to change domain

## Files Created

- `buttondown_subscriber_manager.py` - Create/delete subscribers
- `buttondown_send_campaigns.py` - Prepare campaigns
- `setup_buttondown_token.sh` - Setup helper
- `.env` - Your API token (keep secret!)

## What Happens Next

After successful send:
1. Check test email accounts for receipt
2. Verify content matches difficulty level
3. Verify images load correctly
4. If all good → Ready for production setup!

## Production Setup

Once testing is complete:
1. Update image server domain from `localhost:8000` → your domain
2. Implement automated sending (optional)
3. Start collecting real subscribers
4. Schedule regular email sends

---

**Ready to start? Run:**
```bash
bash setup_buttondown_token.sh
```
