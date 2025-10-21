# Database Cleanup & Fresh Start Guide

## ✅ Status: ALL DATABASES CLEANED

**Date:** October 20, 2025
**Cleaned By:** clean_databases.py script

### Current State

```
📦 articles.db
  ✓ articles table: 0 rows (was 8)
  ✓ article_summaries table: 0 rows (was 0)

📦 subscriptions.db
  ✓ article_summaries table: 0 rows (was 6)
  ✓ quiz_questions table: 0 rows (was 15)
  ✓ categories table: 0 rows (was 6)
  ✓ articles_enhanced table: 0 rows (was 0)
  ✓ subscriptions_enhanced table: 0 rows (was 0)
  ✓ email_logs table: 0 rows (was 0)
```

---

## 🧹 Cleanup Script

### File: `clean_databases.py`

A Python script to manage database cleanup with multiple options.

### Features

1. **Show Status Only** - No changes, just display current state
2. **Clear Data** - Delete all rows, keep schema intact (safe, default)
3. **Drop & Recreate** - Drop tables and recreate with fresh schema

### Usage

#### Option 1: Show Status (Safe)
```bash
python3 clean_databases.py --status

# Output: Shows row counts for all tables
```

#### Option 2: Clear Data (Default)
```bash
python3 clean_databases.py

# Prompts: "Clear all data? (yes/no): "
# Action: Deletes all rows, keeps schema
# Result: All tables exist but are empty
```

#### Option 3: Drop & Recreate (Nuclear)
```bash
python3 clean_databases.py --drop

# Prompts: "This will DROP and RECREATE all tables. Are you sure? (yes/no): "
# Action: Drops all tables, recreates with fresh schema
# Result: All tables are fresh and empty
```

#### Non-Interactive Mode
```bash
# Clear data without prompt
echo "yes" | python3 clean_databases.py

# Drop and recreate without prompt
echo "yes" | python3 clean_databases.py --drop
```

---

## 📋 What Was Deleted

### From articles.db
- **8 articles** (PBS, Swimming World, TechRadar)
- These were test data, will be recollected via RSS crawling

### From subscriptions.db
- **6 categories** (World, Science, Sports, Tech, etc)
- **15 quiz questions** (old test data)
- All subscriptions, email logs, etc (empty anyway)

---

## 🚀 Next Steps: Fresh Start on MAC

### Step 1: Collect Articles Again
```bash
# Extract RSS collector from run_full_pipeline.py into data_collector.py
# Then run:
python3 data_collector.py

# Expected: 8 articles inserted into articles table
```

### Step 2: Process Through Deepseek
```bash
# Create data_processor.py module
python3 data_processor.py

# Expected: 48 summaries (8 articles × 6 summaries each)
# In article_summaries table
```

### Step 3: Generate Output
```bash
# Create page_generator.py module
python3 page_generator.py

# Expected:
# - output/articles_data.json (with all articles + summaries)
# - output/article_*.html (detail pages)
```

### Step 4: Test Locally
```bash
# Open in browser
open main_articles_interface_v2.html

# Test all combinations:
# - HIGH/MID/EASY buttons
# - EN/CN buttons
# - MORE button → detail page
```

### Step 5: Deploy to EC2
```bash
git add -A
git commit -m "create modular data collection, processing, and generation scripts"
git push
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
cd /var/www/news && git pull
python3 data_collector.py && python3 data_processor.py && python3 page_generator.py
```

---

## 📊 Database Schemas (Preserved)

### articles.db

#### Table: articles
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    pub_date TEXT,
    image_url TEXT,
    image_local TEXT,
    content TEXT,
    crawled_at TEXT,
    deepseek_processed BOOLEAN DEFAULT 0,
    processed_at TEXT
);
```

#### Table: article_summaries
```sql
CREATE TABLE article_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    difficulty TEXT,
    language TEXT,
    summary TEXT,
    generated_at TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

### subscriptions.db

All 6 tables preserved with fresh schema:
- `categories`
- `article_summaries` (enhanced with keywords, background, arguments)
- `quiz_questions`
- `articles_enhanced`
- `subscriptions_enhanced`
- `email_logs`

---

## ✅ Verification

### Quick Check
```bash
# Check articles.db
sqlite3 articles.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM article_summaries;"
# Expected output: 0 0

# Check subscriptions.db
sqlite3 subscriptions.db "SELECT name, COUNT(*) as rows FROM (SELECT 'categories' as name FROM categories UNION ALL SELECT 'article_summaries' FROM article_summaries UNION ALL SELECT 'quiz_questions' FROM quiz_questions UNION ALL SELECT 'articles_enhanced' FROM articles_enhanced UNION ALL SELECT 'subscriptions_enhanced' FROM subscriptions_enhanced UNION ALL SELECT 'email_logs' FROM email_logs) GROUP BY name;"
# Expected output: All = 0
```

### Using Script
```bash
python3 clean_databases.py --status
```

---

## 🔧 Troubleshooting

### Issue: "Database is locked"
**Solution:** Close any open connections to the database first
```bash
pkill -f "sqlite3"
pkill -f "python.*articles.db"
```

### Issue: "No such table"
**Solution:** Run with `--drop` flag to recreate tables
```bash
echo "yes" | python3 clean_databases.py --drop
```

### Issue: Script fails silently
**Solution:** Run with error output
```bash
python3 clean_databases.py 2>&1 | tail -20
```

---

## 📝 Script Code Reference

### Key Functions

```python
clean_articles_db(drop_tables=False)
  # Clean articles.db
  # If drop_tables=True: drop and recreate
  # If drop_tables=False: clear data only

clean_subscriptions_db(drop_tables=False)
  # Clean subscriptions.db
  # Handles all 6 tables

show_status()
  # Display current row counts for all tables
```

### Exit Codes
```
0: Success
1: Failure (error during cleaning)
```

---

## 🎯 Clean State Ready For

✅ **Modular Development:**
- Create data_collector.py from scratch
- Create data_processor.py from scratch
- Create page_generator.py from scratch

✅ **Fresh Testing:**
- Test each module independently
- No old data conflicts
- Clean database auditing trail

✅ **Clean Deployment:**
- Push clean code to GitHub
- Pull on EC2
- Run fresh pipeline from scratch

---

## Important Notes

1. **Schema Preserved:** Tables still exist, just empty
2. **Foreign Keys:** Relationships still intact, ready for new data
3. **Reversible:** If you still need old data, it's not deleted from git history
4. **Safe:** Default option clears data, keeps schema

---

## Cleanup Completion Summary

```
╔════════════════════════════════════════════════════════════╗
║         ✅ DATABASE CLEANUP COMPLETE - FRESH START         ║
╚════════════════════════════════════════════════════════════╝

DELETED:
  📋 8 articles
  📊 0 summaries from articles.db
  📊 6 summaries from subscriptions.db
  📚 15 quiz questions
  🏷️  6 categories
  📧 0 emails/logs

PRESERVED:
  🗄️  All 8 tables (structure intact)
  🔑 All foreign key relationships
  ✨ All constraints

READY FOR:
  🆕 Fresh RSS collection
  ⚙️  Modular script development
  🧪 Clean testing
  🚀 Production deployment

NEXT: Create data_collector.py, data_processor.py, page_generator.py
```
