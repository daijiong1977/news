# Test Setup & Campaign Send Summary

## What You Asked For

Create 4 test subscribers and send level-specific emails:
- easy@daijiong.com (Easy level)
- mid@daijiong.com (Middle level)  
- diff@daijiong.com (Hard level - note: "diff" for difficult)
- cn@daijiong.com (Chinese level)

## What I Created

### 1. **buttondown_subscriber_manager.py** ⭐
   - Create the 4 test subscribers in Buttondown
   - Automatically tag them by level
   - Clean up ALL other existing subscribers (with confirmation)
   - Verify final setup is correct

### 2. **buttondown_send_campaigns.py**
   - Create 4 email drafts in Buttondown
   - One draft per difficulty level
   - Link to the 4 HTML files we generated
   - Print step-by-step sending instructions

### 3. **setup_buttondown_token.sh**
   - Interactive setup for your API token
   - Saves to `.env` file (keep secret!)

### 4. **BUTTONDOWN_QUICKSTART.md**
   - Complete quick start guide
   - All commands in one place
   - Troubleshooting section

## Step-by-Step Process

### Step 1️⃣: Get API Token
Go to: https://buttondown.email/settings/api
- Create a token if you don't have one
- Copy the token

### Step 2️⃣: Run Setup (Interactive)
```bash
bash setup_buttondown_token.sh
```
Paste your token when prompted → Creates `.env` file

### Step 3️⃣: Create Test Subscribers
```bash
python3 buttondown_subscriber_manager.py
```
This will:
- Show all current subscribers
- Create 4 new subscribers with tags
- Ask permission to delete others
- Verify final setup (should show only 4)

### Step 4️⃣: Prepare Campaigns
```bash
python3 buttondown_send_campaigns.py
```
This will:
- Create 4 email drafts
- Show draft IDs
- Print detailed sending instructions

### Step 5️⃣: Send via Dashboard (Manual)
1. Go to: https://buttondown.email/dashboard
2. Click **Emails**
3. Find draft: "📰 Daily News - Easy Level 🟢"
4. Click **Send**
5. Choose **Send to specific subscribers**
6. Select tag: **Level: Easy**
7. Click **Send**

Repeat for other 3 levels (mid/hard/CN)

## What Happens

```
YOUR SYSTEM:
┌─────────────────────────────────────────┐
│  4 HTML files ready                      │
│  ├─ email_enhanced_easy.html             │
│  ├─ email_enhanced_mid.html              │
│  ├─ email_enhanced_hard.html             │
│  └─ email_enhanced_CN.html               │
└─────────────────────────────────────────┘
           ↓
STEP 1: Create subscribers with tags
┌─────────────────────────────────────────┐
│  easy@daijiong.com    → Tag: Level: Easy│
│  mid@daijiong.com     → Tag: Level: Mid │
│  diff@daijiong.com    → Tag: Level: Hard│
│  cn@daijiong.com      → Tag: Level: CN  │
└─────────────────────────────────────────┘
           ↓
STEP 2: Create drafts from HTML
┌─────────────────────────────────────────┐
│  Draft 1: Easy Level content             │
│  Draft 2: Middle Level content           │
│  Draft 3: Hard Level content             │
│  Draft 4: Chinese content                │
└─────────────────────────────────────────┘
           ↓
STEP 3: Send with tag filtering
┌─────────────────────────────────────────┐
│ Send Draft 1 to subscribers tagged:      │
│ "Level: Easy"                            │
│ → easy@daijiong.com ✓                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Send Draft 2 to subscribers tagged:      │
│ "Level: Middle"                          │
│ → mid@daijiong.com ✓                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Send Draft 3 to subscribers tagged:      │
│ "Level: Hard"                            │
│ → diff@daijiong.com ✓                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Send Draft 4 to subscribers tagged:      │
│ "Level: Chinese"                         │
│ → cn@daijiong.com ✓                      │
└─────────────────────────────────────────┘
           ↓
RESULT: Each subscriber receives THEIR level
```

## Key Points

✅ **Easy Level** → Beginner-friendly language
✅ **Middle Level** → Intermediate explanations  
✅ **Hard Level** → Expert-level deep dive
✅ **Chinese** → Full Chinese translation

✅ **No truncation** → Full article summaries
✅ **Responsive layout** → Works on all devices
✅ **Live images** → Served from your server
✅ **Category tags** → Organized by News/Science/Sports

## Cleanup Feature

The subscriber manager will:
1. Show you how many subscribers exist
2. Ask "Delete all except 4 test accounts?"
3. If YES: Delete all others (keeps test 4)
4. If NO: Keep everyone

This lets you test with clean state.

## Buttondown Tags Created

These are automatically created and applied:
- `Level: Easy` → easy@daijiong.com
- `Level: Middle` → mid@daijiong.com
- `Level: Hard` → diff@daijiong.com
- `Level: Chinese` → cn@daijiong.com

## Testing Verification

After sending, check your test email accounts for:

✓ Email received with correct subject
✓ Content matches difficulty level
✓ Images load correctly
✓ Layout is responsive
✓ All text shows (no truncation)

## Next Steps After Testing

1. ✅ Verify all 4 test emails received correctly
2. ✅ Check content matches level (easy/mid/hard/CN)
3. ✅ Verify images load
4. ✅ If all good → Production ready!

Production setup:
- Change image server URL from localhost to domain
- Implement automated sending (optional)
- Start collecting real subscribers
- Scale up campaigns

## Files You'll Use

| File | Purpose | Run When |
|------|---------|----------|
| `setup_buttondown_token.sh` | Set API token | First time only |
| `buttondown_subscriber_manager.py` | Create/delete subscribers | Setup test subscribers |
| `buttondown_send_campaigns.py` | Prepare campaigns | Before each send |
| `.env` | Store API token | Created automatically (keep secret!) |

## Common Questions

**Q: What's the difference between "diff" and "hard"?**
A: "diff" = difficult, abbreviated in email address. Maps to "hard" level internally.

**Q: Will this delete my real subscribers?**
A: Only if you confirm "yes" to the deletion prompt. Default behavior keeps them.

**Q: Can I test again?**
A: Yes! The cleanup step lets you reset to just 4 test accounts each time.

**Q: When do I go live?**
A: After verifying all 4 test emails received correctly. Then change domain from localhost→production.

---

## Ready? Start Here:

```bash
# 1. Interactive token setup
bash setup_buttondown_token.sh

# 2. Create/cleanup subscribers
python3 buttondown_subscriber_manager.py

# 3. Prepare campaigns
python3 buttondown_send_campaigns.py

# 4. Go to Buttondown dashboard and send each campaign
# https://buttondown.email/dashboard

# 5. Check test email accounts
# Should have 4 emails, one per level
```

Good luck! 🚀
