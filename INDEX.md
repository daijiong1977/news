# 📰 Daily News Digest System - Complete Setup

## 🎯 What You Have

A production-ready system to aggregate multiple RSS feeds, extract full article content, and deliver daily news digests via HTML browser display or email.

---

## ⚡ Quick Start (60 seconds)

```bash
# 1. Generate digest
python3 generate_daily_digest.py

# 2. View in browser
open daily_digest.html
```

Done! You now have a digest with top articles from PBS NewsHour and Swimming World Magazine.

---

## 📋 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **QUICKSTART.md** | 5-minute getting started guide | 5 min |
| **README_DIGEST.md** | Complete feature documentation | 10 min |
| **SYSTEM_SUMMARY.md** | Feature summary with examples | 8 min |
| **SYSTEM_ARCHITECTURE.txt** | System design overview | 5 min |

---

## 🔧 Main Commands

### Generate Digest
```bash
# Just generate
python3 generate_daily_digest.py

# Generate + send email
python3 generate_daily_digest.py --send-email

# Custom files
python3 generate_daily_digest.py --html-output custom.html --json-output custom.json
```

### Configuration
```bash
# Interactive setup
python3 setup_config.py

# Set up cron automation
python3 schedule_digest.py
```

---

## 📁 File Structure

```
/Users/jidai/news/
├── Configuration
│   ├── config.json                    # Your settings
│   ├── setup_config.py                # Interactive setup tool
│   └── schedule_digest.py             # Cron helper
│
├── Core Engine
│   └── generate_daily_digest.py       # Main generator
│
├── Documentation
│   ├── QUICKSTART.md                  # Quick start
│   ├── README_DIGEST.md               # Full docs
│   ├── SYSTEM_SUMMARY.md              # Overview
│   ├── SYSTEM_ARCHITECTURE.txt        # Architecture
│   └── INDEX.md                       # This file
│
├── Outputs (Generated)
│   ├── daily_digest.html              # HTML digest
│   ├── daily_digest.json              # JSON digest
│   └── digest.log                     # Automation log
│
└── Assets (From RSS feeds)
    ├── pbs_assets/                    # PBS images
    ├── swimmingworld_assets/          # Swimming World images
    └── (other sources' images)
```

---

## 🎯 Features

✅ **Multi-Source RSS Aggregation**
- Configure 3-5+ RSS feeds
- Easily add/remove/enable/disable sources
- Per-source top 3 articles (configurable)

✅ **Full Article Extraction**
- Fetches original article links
- Extracts complete content (not just RSS summaries)
- Intelligent fallback parsing

✅ **ISO 8601 Timestamps**
- All dates properly formatted
- Timezone information preserved
- Example: `2025-10-19T17:50:40-04:00`

✅ **Multiple Output Formats**
- **HTML**: Beautiful, responsive design for reading
- **JSON**: Structured data for programmatic access

✅ **Email Integration**
- Google Gmail support
- Secure app password authentication
- Multiple recipients
- Connection testing included

✅ **Daily Automation**
- Optional cron scheduling
- Automatic daily generation + email
- Execution logging

---

## 📊 Current Setup

**Enabled RSS Sources:**
- PBS NewsHour (https://www.pbs.org/newshour/feeds/rss/headlines)
- Swimming World Magazine (https://www.swimmingworldmagazine.com/news/feed/)

**Digest Settings:**
- Top 3 articles per source
- 24-hour time window
- Outputs to `daily_digest.html` and `daily_digest.json`

**Email:**
- Not configured yet (optional)

---

## 🚀 Next Steps

### 1. Try It Now
```bash
python3 generate_daily_digest.py
open daily_digest.html
```

### 2. Add More Sources (Optional)
```bash
python3 setup_config.py
# Select "1. Manage RSS Feed Sources" → "1. Add RSS source"
```

### 3. Enable Email (Optional)
```bash
python3 setup_config.py
# Select "2. Configure Google SMTP Email"
# Then "3. Manage Email Recipients"
```

### 4. Set Up Automation (Optional)
```bash
python3 schedule_digest.py
# Choose daily generation time (9 AM default)
```

---

## 💡 Example Workflows

### Personal Morning Briefing
```bash
python3 generate_daily_digest.py && open daily_digest.html
```
Read your news in the browser with beautiful formatting.

### Team Email Distribution
```bash
# Setup emails once
python3 setup_config.py  # Configure recipients

# Then daily
python3 generate_daily_digest.py --send-email
```
All team members receive HTML digest in their inbox.

### Programmatic Access
```bash
python3 generate_daily_digest.py
# Parse daily_digest.json for use in other applications
```
Use structured data for custom processing.

---

## 🐛 Troubleshooting

**No articles found?**
- Check RSS feed URLs are correct in config.json
- Verify articles were published within 24 hours
- Try increasing `hours_lookback` in config.json

**Email not working?**
1. Run `python3 setup_config.py`
2. Go to option 2 (SMTP)
3. Test connection (option 4)
4. Check Gmail has 2FA enabled and app password is correct

**Content extraction issues?**
- Some websites block automated scraping
- System uses RSS summary as fallback
- Quality depends on RSS feed and site structure

---

## 📚 Reading Guide

**First Time Users:** Start with QUICKSTART.md

**Complete Reference:** See README_DIGEST.md

**System Design:** Check SYSTEM_ARCHITECTURE.txt

**Feature Examples:** Review SYSTEM_SUMMARY.md

---

## 🔐 Security Notes

- **App Passwords**: Stored locally in `config.json`
- **Plain Text**: Credentials are not encrypted (keep file private)
- **No Cloud**: Everything runs on your machine
- **Respectful Requests**: 0.3s delay between requests to be courteous

---

## 📞 Support & Customization

All features are fully documented in the code with comments.

To customize:
1. Edit `config.json` directly for simple changes
2. Run `setup_config.py` for interactive configuration
3. Modify `generate_daily_digest.py` for advanced customization

---

## ✨ What Makes This System Great

- **Complete Solution**: Everything you need in one place
- **Easy to Use**: Interactive menus, no complex configuration
- **Flexible**: Add any RSS feed, customize everything
- **Production Ready**: Tested and working
- **Extensible**: Well-documented code for customization
- **Automated**: Optional daily scheduling with email

---

## 🎁 Quick Reference

```
START HERE:
  python3 generate_daily_digest.py

CONFIGURE:
  python3 setup_config.py

AUTOMATE:
  python3 schedule_digest.py

DOCS:
  cat QUICKSTART.md              (quick reference)
  cat README_DIGEST.md           (full docs)
  cat SYSTEM_SUMMARY.md          (features)
  cat SYSTEM_ARCHITECTURE.txt    (architecture)
```

---

**Everything is ready to use. Start generating digests now!** 🚀
