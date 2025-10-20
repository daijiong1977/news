# DEPLOYMENT SUMMARY - October 20, 2025

## ✅ Pre-Deployment Complete

### Local Workspace Cleaned
- ✓ Removed all test response files (7 files)
- ✓ Reset articles.db to schema-only state
- ✓ Database verified: 19 tables + lookup tables ready
- ✓ All preview data removed

### Critical Files Ready for Deployment

| File | Size | Purpose |
|------|------|---------|
| `init_db.py` | 18K | Initialize 19-table schema |
| `data_collector.py` | 7.9K | Collect articles from RSS feeds |
| `process_one_article.py` | 28K | Generate Deepseek API analysis |
| `insert_from_response.py` | 16K | Insert validated data into DB |
| `prompts_compact.md` | 2.7K | Category-specific prompts |
| `config.json` | 1.0K | RSS feed configuration |
| `DEPLOYMENT.md` | Comprehensive | EC2 setup guide |
| `ec2_setup.sh` | 3.8K | Automated EC2 setup script |

### Database Schema (LOCKED - 19 Tables)

**Core Tables:**
- articles, article_images, article_summaries, keywords, questions, choices, comments, background_read, article_analysis

**Lookup Tables (Pre-populated):**
- categories (8): US News, Swimming, PBS, Technology, Science, Politics, Business, Health
- difficulty_levels (3): easy, mid, hard
- languages (2): en, zh

**User Tables:**
- users, user_difficulty_levels, user_languages, user_categories, user_preferences, user_awards

### Processing Workflow

```
Step 1: data_collector.py
└─ Fetch articles from RSS feeds → Insert into articles table

Step 2: process_one_article.py (for each unprocessed article)
├─ Load article content
├─ Select category-specific prompt
├─ Call Deepseek API with JSON mode
└─ Save response to response_article_X_TIMESTAMP.json

Step 3: insert_from_response.py
├─ Load response file
├─ Extract zh_title (with fallback to zh_hard first sentence)
├─ Insert all content into 9 data tables
├─ Update articles.zh_title
└─ Mark article as deepseek_processed=1
```

### API Configuration (CRITICAL)

- **Timeout:** `(30, 300)` tuple format (connect=30s, read=300s)
- **Response Format:** JSON mode with explicit schema
- **Max Tokens:** 6000
- **Temperature:** 0.7
- **Content:** Each article generates ~199 records (3 levels × [summaries, keywords, questions, choices, background, analysis, perspectives])

### GitHub Push Complete

```
Commit: "Deployment preparation: Production-ready pipeline"
- All 7 critical files staged
- Clean commit with full description
- Pushed to main branch
```

## 🚀 EC2 Deployment Instructions

### Quick Start (Single Command)

SSH into your EC2 server and run:

```bash
curl -fsSL https://raw.githubusercontent.com/daijiong1977/news/main/ec2_setup.sh | bash
```

**OR manually:**

```bash
git clone https://github.com/daijiong1977/news.git
cd news
bash ec2_setup.sh
```

### What ec2_setup.sh Does

1. Updates system packages
2. Installs Python 3 + pip + git
3. Clones/updates repository
4. Prompts for Deepseek API key → Creates .env
5. Runs init_db.py to create fresh database
6. Creates logs directory
7. Generates process_articles_loop.sh for automated processing

### After Setup - 3 Usage Options

**Option 1: Manual Processing (Test)**
```bash
cd ~/news
python3 data_collector.py                    # Collect articles
python3 process_one_article.py               # Generate analysis
python3 insert_from_response.py response_article_*.json  # Insert
```

**Option 2: Automated Loop (Background)**
```bash
cd ~/news
nohup bash process_articles_loop.sh > logs/main.log 2>&1 &
```

**Option 3: Systemd Service (Production)**
```bash
sudo cp news-pipeline.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable news-pipeline.service
sudo systemctl start news-pipeline.service
```

## 📊 Monitoring & Verification

### Check Processing Status
```bash
sqlite3 ~/news/articles.db "SELECT COUNT(*) as total, SUM(deepseek_processed) as processed FROM articles;"
```

### View Data Counts
```bash
sqlite3 ~/news/articles.db << EOF
SELECT 'article_summaries', COUNT(*) FROM article_summaries
UNION ALL SELECT 'keywords', COUNT(*) FROM keywords
UNION ALL SELECT 'questions', COUNT(*) FROM questions
UNION ALL SELECT 'choices', COUNT(*) FROM choices
UNION ALL SELECT 'comments', COUNT(*) FROM comments
UNION ALL SELECT 'background_read', COUNT(*) FROM background_read
UNION ALL SELECT 'article_analysis', COUNT(*) FROM article_analysis;
EOF
```

### Check Logs
```bash
tail -50 logs/processor.log   # Processing errors
tail -50 logs/collector.log   # Collection status
tail -50 logs/main.log        # Overall loop status
```

## 🔐 Security Notes

- API key stored in `.env` (git-ignored, 600 permissions)
- Database file created fresh on each server
- No credentials in code or repository
- Use SSH keys for EC2 access (not password)

## 📋 Expected Output After First Complete Run

```
Database State After Processing 1 Article:
┌─────────────────┬────────┐
│ Table           │ Count  │
├─────────────────┼────────┤
│ articles        │   1    │
│ article_images  │   1    │
│ article_summary │   4    │ (3 EN + 1 ZH)
│ keywords        │   30   │ (10 × 3 levels)
│ questions       │   30   │ (8+10+12)
│ choices         │  120   │ (4 per question)
│ comments        │   9    │ (3 per level with attitudes)
│ backgrounds     │   3    │ (1 per level)
│ article_analysis│   2    │ (mid + hard)
└─────────────────┴────────┘
TOTAL: 199 records per article
```

## 🎯 Next Major Milestone

After EC2 is running and processing articles:

**Create page_generator.py** - Generate HTML/JSON output from database for web display

---

**Status:** ✅ Ready for EC2 Deployment  
**Local DB:** Fresh schema-only state  
**GitHub:** All files pushed  
**API:** Configured and tested  
**Documentation:** Complete with deployment scripts  

**Your next action:** SSH to EC2 and run the setup script!
