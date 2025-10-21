# Quick Reference: Database & Modular Structure

## Local MAC Current State

```
✅ HAVE:
   - articles.db with 8 articles collected
   - 2 database files (articles.db + subscriptions.db)
   - HTML templates (main_articles_interface_v2.html, article_analysis_v2.html)

❌ MISSING:
   - 48 summaries (0 generated, 0 processed)
   - output/articles_data.json
   - HTML pages
   - Deepseek processing
```

---

## Database Tables (Articles.db - Main Focus)

### Table: `articles` (8 rows)
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT,
    source TEXT,                    -- "PBS NewsHour", "Swimming World", etc
    url TEXT UNIQUE,
    description TEXT,
    pub_date TEXT,
    image_url TEXT,
    image_local TEXT,
    content TEXT,                   -- Full article HTML/text
    crawled_at TEXT,
    deepseek_processed BOOLEAN,     -- 0 = needs processing, 1 = done
    processed_at TEXT
);
```

Sample data:
```
id | title | source | deepseek_processed
1  | Ukrainian drones strike... | PBS NewsHour | 0
2  | Americans are worried... | PBS NewsHour | 0
3  | NC State defeats Georgia... | Swimming World | 0
... (8 total, all = 0)
```

### Table: `article_summaries` (Currently 0 rows - EMPTY)
```sql
CREATE TABLE article_summaries (
    id INTEGER PRIMARY KEY,
    article_id INTEGER,            -- FK to articles.id
    difficulty TEXT,               -- "easy", "mid", "high"
    language TEXT,                 -- "en", "zh"
    summary TEXT,                  -- The actual summary
    generated_at TEXT
);
```

Expected after processing:
```
id | article_id | difficulty | language | summary
1  | 1          | easy       | en       | "Simple summary in English..."
2  | 1          | easy       | zh       | "简单中文摘要..."
3  | 1          | mid        | en       | "Medium complexity..."
4  | 1          | mid        | zh       | "中等难度..."
5  | 1          | high       | en       | "Complex detailed..."
6  | 1          | high       | zh       | "复杂详细..."
7  | 2          | easy       | en       | ...
... (48 total for 8 articles)
```

---

## Three Modular Scripts to Create

### 1️⃣ data_processor.py
**What:** Process unprocessed articles through Deepseek API
**Input:** articles table where `deepseek_processed = 0`
**Output:** Populate `article_summaries` table with 6 summaries per article
**Database Changes:** INSERT into article_summaries, UPDATE articles.deepseek_processed = 1

```bash
# Usage
python3 data_processor.py                 # Process all unprocessed
python3 data_processor.py --article 1     # Process only article 1 (for testing)
python3 data_processor.py --limit 1       # Process first 1 (for testing)
```

**Flow:**
```
FOR each article WHERE deepseek_processed = 0:
  1. Call Deepseek API with article content
  2. Get 6 summaries back: easy_en, easy_zh, mid_en, mid_zh, high_en, high_zh
  3. INSERT 6 rows into article_summaries table
  4. UPDATE articles SET deepseek_processed = 1, processed_at = NOW()
```

---

### 2️⃣ page_generator.py
**What:** Generate HTML pages and JSON output from database
**Input:** articles + article_summaries tables
**Output:** output/articles_data.json + HTML pages
**Database Changes:** NONE (read-only)

```bash
# Usage
python3 page_generator.py               # Generate all output
```

**Output files:**
```
output/
  ├── articles_data.json               # Main JSON with all articles + summaries
  ├── article_1.html                   # Detail page for article 1
  ├── article_2.html
  └── ... (one per article)
```

**JSON structure:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "...",
      "source": "PBS",
      "date": "...",
      "image": "...",
      "keywords": ["..."],
      "summary_easy_en": "Simple...",
      "summary_easy_zh": "简单...",
      "summary_mid_en": "Medium...",
      "summary_mid_zh": "中等...",
      "summary_hard_en": "Complex...",
      "summary_hard_zh": "复杂..."
    }
  ]
}
```

---

### 3️⃣ data_collector.py
**What:** Collect articles from RSS feeds
**Input:** RSS feed URLs
**Output:** Populate articles table
**Database Changes:** INSERT new articles, UPDATE existing ones

(Already partially exists in run_full_pipeline.py - extract it)

---

## Testing Steps on MAC (In Order)

### Step 1: Verify Articles Collected
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
# Expected: 8

sqlite3 articles.db "SELECT id, title, deepseek_processed FROM articles LIMIT 3;"
# Expected:
# 1|Ukrainian drones...|0
# 2|Americans are...|0
# 3|NC State defeats...|0
```

### Step 2: Verify Summaries Empty
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"
# Expected: 0
```

### Step 3: Process 1 Article (Testing)
```bash
python3 data_processor.py --article 1
```

### Step 4: Verify 6 Rows Inserted
```bash
sqlite3 articles.db "SELECT article_id, difficulty, language FROM article_summaries WHERE article_id = 1 ORDER BY 1, 2, 3;"
# Expected:
# 1|easy|en
# 1|easy|zh
# 1|high|en
# 1|high|zh
# 1|mid|en
# 1|mid|zh
```

### Step 5: Process All Articles
```bash
python3 data_processor.py
```

### Step 6: Verify All Summaries
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"
# Expected: 48 (8 × 6)

sqlite3 articles.db "SELECT article_id, COUNT(*) FROM article_summaries GROUP BY article_id;"
# Expected: Each article should have 6 summaries
```

### Step 7: Generate Output
```bash
python3 page_generator.py
```

### Step 8: Verify JSON
```bash
ls -lh output/articles_data.json

python3 -c "import json; data = json.load(open('output/articles_data.json')); print(f'Articles: {len(data[\"articles\"])}'); print(f'Fields in first article: {list(data[\"articles\"][0].keys())}')"
# Expected:
# Articles: 8
# Fields: ['id', 'title', 'source', 'date', 'image', 'keywords', 'summary_easy_en', ...]
```

### Step 9: Test Homepage
```bash
# Open browser
open main_articles_interface_v2.html

# Verify:
# - 8 articles display
# - HIGH dropdown shows complex summaries
# - MID dropdown shows medium summaries
# - EASY dropdown shows simple summaries
# - EN button shows English
# - CN button shows Chinese
# - MORE button works
```

---

## Key Concepts

### Difficulty Levels
- **easy**: Simple language (ages 8-10)
- **mid**: Standard language (ages 11-13)
- **high**: Complex language (ages 14+)

### Language Pairs
- **en**: English
- **zh**: Simplified Chinese (中文)

### Summary Naming Convention
```
Pattern: summary_[difficulty]_[language]

Examples:
- summary_easy_en   (Simple English)
- summary_easy_zh   (Simple Chinese)
- summary_mid_en    (Medium English)
- summary_mid_zh    (Medium Chinese)
- summary_hard_en   (Complex English)
- summary_hard_zh   (Complex Chinese)
```

### Database Flag
```
articles.deepseek_processed:
  0 = Not yet processed (needs Deepseek)
  1 = Already processed (has summaries)
```

---

## Common Commands

### Reset for Testing
```bash
# Clear summaries (but keep articles)
sqlite3 articles.db "DELETE FROM article_summaries;"
sqlite3 articles.db "UPDATE articles SET deepseek_processed = 0;"

# Verify
sqlite3 articles.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM article_summaries;"
# Expected: 8, 0
```

### Check Processing Status
```bash
sqlite3 articles.db "SELECT COUNT(*) FILTER (WHERE deepseek_processed = 0) as need_processing, COUNT(*) FILTER (WHERE deepseek_processed = 1) as completed FROM articles;"
# Example: 0, 8 (all done)
```

### Check Summary Completeness
```bash
sqlite3 articles.db "SELECT article_id, COUNT(*) as count FROM article_summaries GROUP BY article_id;"
# Expected: Each article = 6
```

### Export to JSON for Inspection
```bash
sqlite3 articles.db -json "SELECT * FROM article_summaries LIMIT 10" | python3 -m json.tool
```

---

## Next Action

👉 **Create data_processor.py first** - This is the core module that needs Deepseek API
   - Test on 1 article
   - Verify 6 rows in database
   - Then run on all 8 articles

Then create page_generator.py and test locally before EC2 deployment.
