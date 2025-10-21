# Implementation Plan: Modular Approach

## Phase 0: Current Status (MAC)

### Database State
```
✅ articles.db
  - articles table: 8 rows (PBS, Swimming, TechRadar sources)
  - article_summaries table: 0 rows (EMPTY - needs processing)

❓ subscriptions.db
  - 6 tables (categories, articles_enhanced, quiz_questions, etc)
  - Status unknown (focus on articles.db first)
```

### Files That Need Creation/Modification
```
TO CREATE:
  🆕 data_collector.py      - Extract RSS and store in articles table
  🆕 data_processor.py      - Process through Deepseek, store in article_summaries
  🆕 page_generator.py      - Generate HTML + JSON from database

TO MODIFY:
  📝 run_full_pipeline.py   - Keep as is, but update to use modular scripts

TO TEST:
  🔍 main_articles_interface_v2.html - Homepage (needs JSON input)
  🔍 article_analysis_v2.html - Detail page (needs JSON input)
```

---

## Phase 1: Create data_processor.py

### Purpose
Process articles through Deepseek API and store 6 summaries per article.

### Design
```python
# data_processor.py

import sqlite3
import requests
import json
import os
from datetime import datetime

def process_articles(limit=None, article_id=None):
    """
    Process unprocessed articles through Deepseek.
    
    Args:
        limit: Max number of articles to process (for testing)
        article_id: Process specific article ID (for testing)
    
    Database Flow:
        INPUT:  SELECT * FROM articles WHERE deepseek_processed = 0
        OUTPUT: INSERT INTO article_summaries (article_id, difficulty, language, summary)
                UPDATE articles SET deepseek_processed = 1, processed_at = NOW()
    """

def generate_summaries(content, title):
    """
    Call Deepseek API to get 6 summaries.
    
    Returns:
    {
        "easy_en": "...",
        "easy_zh": "...",
        "mid_en": "...",
        "mid_zh": "...",
        "high_en": "...",
        "high_zh": "..."
    }
    """

def store_summaries(article_id, summaries):
    """
    Insert 6 summaries into database with proper structure.
    
    Inserts:
      - article_id=X, difficulty="easy", language="en", summary="..."
      - article_id=X, difficulty="easy", language="zh", summary="..."
      - article_id=X, difficulty="mid", language="en", summary="..."
      - article_id=X, difficulty="mid", language="zh", summary="..."
      - article_id=X, difficulty="high", language="en", summary="..."
      - article_id=X, difficulty="high", language="zh", summary="..."
    """

if __name__ == "__main__":
    # Test on 1 article first
    process_articles(limit=1)
```

### Testing Steps
```bash
# Step 1: Test on 1 article
sqlite3 articles.db "UPDATE articles SET deepseek_processed = 0;"
python3 data_processor.py --limit 1

# Step 2: Verify
sqlite3 articles.db "SELECT article_id, difficulty, language FROM article_summaries;"
# Expected: 6 rows for article 1

# Step 3: Verify structure
sqlite3 articles.db "SELECT DISTINCT difficulty, language FROM article_summaries ORDER BY 1, 2;"
# Expected:
# easy|en
# easy|zh
# high|en
# high|zh
# mid|en
# mid|zh

# Step 4: Run on all articles
python3 data_processor.py

# Step 5: Final verification
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"
# Expected: 48 (8 articles × 6 summaries)
```

---

## Phase 2: Create page_generator.py

### Purpose
Read articles + summaries from database, generate HTML pages and JSON output.

### Design
```python
# page_generator.py

import sqlite3
import json
from datetime import datetime

def generate_articles_json():
    """
    Read all articles with ALL 6 summaries, create JSON.
    
    Database:
        SELECT a.*, s.* FROM articles a
        LEFT JOIN article_summaries s ON a.id = s.article_id
    
    Output JSON structure:
    {
        "articles": [
            {
                "id": 1,
                "title": "...",
                "source": "PBS",
                "date": "...",
                "image": "...",
                "keywords": [...],
                "summary_easy_en": "...",
                "summary_easy_zh": "...",
                "summary_mid_en": "...",
                "summary_mid_zh": "...",
                "summary_hard_en": "...",
                "summary_hard_zh": "..."
            },
            ...
        ]
    }
    """

def generate_html_pages():
    """
    Generate HTML pages for each article.
    
    Creates:
        output/article_1.html
        output/article_2.html
        ...
    """

if __name__ == "__main__":
    generate_articles_json()
    generate_html_pages()
    print("✓ Generated JSON and HTML pages")
```

### Output Structure
```
output/
  ├── articles_data.json       (Main JSON with all articles + summaries)
  ├── article_1.html           (Detail page for article 1)
  ├── article_2.html           (Detail page for article 2)
  └── ...
```

---

## Phase 3: Update run_full_pipeline.py

### Current Structure (937 lines)
```python
# Does EVERYTHING in one script
1. Crawl RSS
2. Fetch content
3. Process Deepseek
4. Generate HTML
5. Generate JSON
```

### New Approach (Call modular scripts)
```python
# run_full_pipeline.py - NEW (Should be much simpler)

if __name__ == "__main__":
    print("Running full pipeline...")
    
    # Step 1: Collect articles
    from data_collector import collect_articles
    collect_articles()
    print("✓ Articles collected/updated")
    
    # Step 2: Process unprocessed articles
    from data_processor import process_articles
    process_articles()
    print("✓ Summaries generated")
    
    # Step 3: Generate pages
    from page_generator import generate_articles_json, generate_html_pages
    generate_articles_json()
    generate_html_pages()
    print("✓ Pages generated")
    
    print("✅ PIPELINE COMPLETE")
```

---

## Phase 4: Testing on MAC

### Test 1: Process 1 Article
```bash
# Reset database
sqlite3 articles.db "UPDATE articles SET deepseek_processed = 0;"

# Process article 1 only
python3 -c "from data_processor import process_articles; process_articles(article_id=1)"

# Verify
sqlite3 articles.db "SELECT article_id, difficulty, language, length(summary) FROM article_summaries WHERE article_id = 1 ORDER BY 1,2,3;"

# Expected output:
# 1|easy|en|150
# 1|easy|zh|200
# 1|high|en|400
# 1|high|zh|450
# 1|mid|en|250
# 1|mid|zh|280
```

### Test 2: Generate JSON
```bash
python3 page_generator.py

# Verify
ls -lh output/articles_data.json
cat output/articles_data.json | python3 -m json.tool | head -50
```

### Test 3: Check JSON Structure
```bash
python3 << 'EOF'
import json
with open('output/articles_data.json') as f:
    data = json.load(f)
    for article in data['articles'][:1]:
        print(f"Article {article['id']}: {article['title'][:40]}")
        print(f"  Fields: {list(article.keys())}")
        for key in sorted(article.keys()):
            if 'summary' in key:
                val = article[key]
                print(f"  {key}: {'✓' if val else '✗'} ({len(val) if val else 0} chars)")
EOF
```

Expected output:
```
Article 1: Ukrainian drones strike Russian g
  Fields: ['id', 'title', 'source', 'date', 'image', 'keywords', 'summary_easy_en', 'summary_easy_zh', 'summary_mid_en', 'summary_mid_zh', 'summary_hard_en', 'summary_hard_zh']
  summary_easy_en: ✓ (145 chars)
  summary_easy_zh: ✓ (198 chars)
  summary_hard_en: ✓ (398 chars)
  summary_hard_zh: ✓ (445 chars)
  summary_mid_en: ✓ (251 chars)
  summary_mid_zh: ✓ (287 chars)
```

### Test 4: Test on All 8 Articles
```bash
# Reset
sqlite3 articles.db "UPDATE articles SET deepseek_processed = 0;"

# Process all
python3 data_processor.py

# Verify count
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"
# Expected: 48 (8 × 6)

# Generate output
python3 page_generator.py

# Verify JSON has 8 articles
python3 -c "import json; data = json.load(open('output/articles_data.json')); print(f'Articles: {len(data[\"articles\"])}')"
```

### Test 5: Verify Homepage Rendering
```bash
# Open in browser
open main_articles_interface_v2.html

# Test:
# 1. High dropdown → shows complex English
# 2. Mid dropdown → shows medium English
# 3. Easy dropdown → shows simple English
# 4. EN button → shows English summaries
# 5. CN button → shows Chinese summaries
# 6. Click MORE → opens detail page with article_analysis_v2.html
```

---

## Deployment Checklist

### Before Deploying to EC2

- [ ] Test data_processor.py on 1 article locally
- [ ] Verify 6 rows inserted correctly
- [ ] Test data_processor.py on all 8 articles
- [ ] Verify article_summaries table has 48 rows
- [ ] Run page_generator.py
- [ ] Verify output/articles_data.json exists and has correct structure
- [ ] Open main_articles_interface_v2.html in browser
- [ ] Test: HIGH/MID/EASY + EN/CN combinations
- [ ] Click MORE button → verify detail page loads
- [ ] Check browser console for errors
- [ ] All tests pass ✅

### Deployment to EC2
```bash
# 1. Commit to GitHub
git add -A
git commit -m "refactor: separate data collection, processing, and generation"
git push

# 2. SSH to EC2
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

# 3. Pull latest
cd /var/www/news
git pull

# 4. Reset and process
sqlite3 articles.db "UPDATE articles SET deepseek_processed = 0;"
python3 data_processor.py

# 5. Generate output
python3 page_generator.py

# 6. Verify
ls -lh output/articles_data.json
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"

# 7. Check website
curl https://news.6ray.com/
```

---

## Questions Needing Your Input

1. **Summaries storage:** Should difficulty column be:
   - Option A (current): difficulty="easy", difficulty="mid", difficulty="high"
   - Option B: Keep separate _en/_zh suffix: difficulty="easy_en", difficulty="easy_zh"

2. **Database merge:** Should we:
   - Keep articles.db and subscriptions.db separate? (easier for now)
   - Merge everything into one database? (cleaner for later)

3. **Testing scope:** Should we:
   - Focus ONLY on articles.db first?
   - Ignore subscriptions.db for now?
   - Deal with quiz/keywords later?

4. **Homepage functionality:** What should work first:
   - Display all 8 articles with summaries? ✅
   - Difficulty filtering (HIGH/MID/EASY)? ✅
   - Language switching (EN/CN)? ✅
   - Category filtering? (maybe later)
   - Quiz functionality? (later)

---

## Success Criteria

### Phase 1 Complete When:
- ✅ data_processor.py processes 1 article → 6 rows in DB
- ✅ 6 rows have correct difficulty/language combinations
- ✅ SQL query verified: 48 rows total for 8 articles

### Phase 2 Complete When:
- ✅ output/articles_data.json generated successfully
- ✅ JSON has all required fields
- ✅ All 8 articles have all 6 summaries

### Phase 3 Complete When:
- ✅ Homepage loads without errors
- ✅ All 9 combinations work (3 difficulties × 3 settings)
- ✅ Detail pages render correctly
- ✅ No console errors

### Deployment Complete When:
- ✅ All tests pass on MAC
- ✅ Code pushed to GitHub
- ✅ EC2 pulls and processes successfully
- ✅ Website live and functional
- ✅ Daily schedule runs without errors
