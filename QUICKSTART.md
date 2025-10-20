# Daily News Digest - Setup & Usage Guide

## 📋 What You Get

A complete system to:
1. **Configure** 3-5 RSS feeds with an interactive setup tool
2. **Fetch** top 3 articles per source from the last 24 hours
3. **Extract** full article content from original links
4. **Format** results as HTML (for reading) and JSON (for integration)
5. **Email** daily digests via Gmail to multiple recipients
6. **Automate** daily runs via cron scheduling

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Configure Your Sources & Email

```bash
cd /Users/jidai/news
python3 setup_config.py
```

Menu options:
- **Option 1**: Add RSS sources (do this 3-5 times)
- **Option 2**: Configure Gmail SMTP (for sending emails)
- **Option 3**: Add recipient emails
- **Option 4**: Adjust digest settings (articles count, time window, etc.)
- **Option 6**: Save and exit

### Step 2: Generate Your First Digest

```bash
python3 generate_daily_digest.py
```

Output:
- `daily_digest.html` - Open in browser to preview
- `daily_digest.json` - Machine-readable format

### Step 3: Send via Email (Optional)

```bash
python3 generate_daily_digest.py --send-email
```

---

## 🔧 Detailed Configuration

### Add RSS Sources via setup_config.py

Example sources to add:

| Source | URL |
|--------|-----|
| PBS NewsHour | `https://www.pbs.org/newshour/feeds/rss/headlines` |
| Swimming World | `https://www.swimmingworldmagazine.com/news/feed/` |
| BBC News | `http://feeds.bbc.co.uk/news/rss.xml` |
| Reuters | `https://www.reuters.com/rssFeed/worldNews` |

### Configure Gmail for Email Sending

1. Go to Google Account: https://myaccount.google.com/security
   - Enable 2-Factor Authentication (if not already enabled)

2. Generate App Password: https://myaccount.google.com/apppasswords
   - Select Mail
   - Select Windows Computer (or your device)
   - Copy the 16-character password

3. In `setup_config.py` (Option 2):
   - Enter your Gmail address
   - Enter the 16-character app password
   - Test connection (Option 4) to verify it works

---

## 📊 Output Formats

### HTML Output (`daily_digest.html`)

```html
📰 Daily News Digest
Generated 2025-10-19 18:24

═══════════════════════════════════════
PBS NEWSHOUR
═══════════════════════════════════════

  📄 Ceasefire violations in Gaza strain fragile truce
     [2025-10-19T17:50:40-04:00]
     On Sunday, there were major strains on the fragile ceasefire 
     between Israel and Hamas...

═══════════════════════════════════════
SWIMMING WORLD MAGAZINE
═══════════════════════════════════════

  📄 Cal Baptist Men Repeat, Rice Women Win MPSF
     [2025-10-19T21:31:59+00:00]
     The Cal Baptist men's team won its second straight MPSF 
     Open Water Championship...
```

### JSON Output (`daily_digest.json`)

```json
[
  {
    "source": "PBS NewsHour",
    "title": "Ceasefire violations in Gaza...",
    "link": "https://www.pbs.org/newshour/show/...",
    "pub_date": "2025-10-19T17:50:40-04:00",
    "snippet": "Brief summary from RSS feed...",
    "content": "Full extracted article content..."
  },
  ...
]
```

---

## ⏰ Automate with Cron (Optional)

### Option A: Using the helper script

```bash
python3 schedule_digest.py
# Select option 2 for daily generation + email at 9 AM
```

### Option B: Manual crontab setup

```bash
crontab -e
```

Add one of these lines:

**Just generate (no email):**
```
0 9 * * * cd /Users/jidai/news && python3 generate_daily_digest.py >> digest.log 2>&1
```

**Generate + send email:**
```
0 9 * * * cd /Users/jidai/news && python3 generate_daily_digest.py --send-email >> digest.log 2>&1
```

This runs at **9:00 AM every day** and logs output to `digest.log`.

---

## 💡 Usage Examples

### Generate digest, save to custom file
```bash
python3 generate_daily_digest.py --html-output mydigest.html --json-output mydigest.json
```

### Get articles from last 72 hours instead of 24
Edit `config.json`:
```json
"digest_settings": {
  "hours_lookback": 72,
  ...
}
```

### Get 5 articles per source instead of 3
Edit `config.json`:
```json
"digest_settings": {
  "articles_per_source": 5,
  ...
}
```

### Add a new RSS source after setup
1. Run `setup_config.py` again
2. Go to option 1 (Manage RSS Feed Sources)
3. Select "Add RSS source"
4. Enter name and URL
5. Save

---

## 🐛 Troubleshooting

### "No articles found"
- Check RSS feed URLs are reachable
- Verify articles were published in last 24 hours
- Run with more verbose output to debug

### "Email not sending"
```bash
python3 setup_config.py
# Go to option 2 (SMTP)
# Select option 4 (Test connection)
```

Common issues:
- Gmail app password is wrong (must be 16 chars from Google)
- 2FA not enabled on Gmail account
- Email recipients list is empty

### "Article content is empty"
- Some websites block automated content extraction
- System extracts what's available in RSS + attempts to scrape
- Content quality depends on RSS feed and site structure

### "Script runs slowly"
- The system pauses 0.3 seconds between requests (to be respectful)
- Each article requires fetching the original page
- Swimming World Magazine is fastest, PBS takes longer due to page structure

---

## 📁 File Reference

```
/Users/jidai/news/
├── config.json                    # ← Your configuration (edit via setup_config.py)
├── setup_config.py                # Interactive config tool
├── generate_daily_digest.py       # Main digest generator
├── schedule_digest.py             # Cron scheduling helper
├── daily_digest.html              # Generated HTML (open in browser)
├── daily_digest.json              # Generated JSON
├── digest.log                      # Cron execution log (if automated)
└── README_DIGEST.md               # Full documentation
```

---

## 🔒 Security Notes

- **App Passwords**: Gmail app passwords are stored in plain text in `config.json`. Keep this file private.
- **Only stored locally**: Your credentials never leave your machine.
- **No account sharing**: Generate unique app passwords for each device.

---

## 📞 Next Steps

1. ✅ Run `setup_config.py` to configure sources
2. ✅ Run `generate_daily_digest.py` to test
3. ✅ Open `daily_digest.html` in your browser to preview
4. ✅ Optionally: Configure email and run `--send-email` flag
5. ✅ Optionally: Set up cron job for daily automation

---

## 💻 Command Reference

```bash
# Interactive setup
python3 setup_config.py

# Generate digest only
python3 generate_daily_digest.py

# Generate + send email
python3 generate_daily_digest.py --send-email

# Custom output files
python3 generate_daily_digest.py --html-output file.html --json-output file.json

# Set up cron scheduling
python3 schedule_digest.py

# View digest log (if running via cron)
tail -f digest.log
```

Happy news reading! 📰
