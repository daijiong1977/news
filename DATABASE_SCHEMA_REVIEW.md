# Database Schema Review - Local MAC

## Current Status

### articles.db (Main Database)
**Location:** `/Users/jidai/news/articles.db`

#### Table: `articles` (0 rows after cleanup)
Purpose: Store collected articles from RSS feeds

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
    deepseek_processed BOOLEAN DEFAULT 0,    -- Flag: has Deepseek processed this?
    processed_at TEXT,
    category_id INTEGER                       -- FK to categories (nullable)
);
```

**Current Data:** 8 articles from PBS, Swimming World, TechRadar (all `deepseek_processed = 0`)

**Key Issue:** `deepseek_processed = 0` means NO summaries have been generated yet!

---

#### Table 2: `article_summaries` (0 rows)
Purpose: Store summaries at different difficulty/language levels

```sql
CREATE TABLE article_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    difficulty TEXT,                         -- easy, mid, high
    language TEXT,                           -- en, zh
    summary TEXT,                            -- The actual summary
    generated_at TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

**Current Data:** EMPTY (0 rows)

**Expected Structure After Processing:**
```
article_id | difficulty | language | summary
-----------|------------|----------|--------
1          | easy       | en       | "Simple English..."
1          | easy       | zh       | "简单中文..."
1          | mid        | en       | "Medium English..."
1          | mid        | zh       | "中等中文..."
1          | high       | en       | "Complex English..."
1          | high       | zh       | "复杂中文..."
2          | easy       | en       | "Simple English..."
... (repeat for all 8 articles)
```

**Total Expected Rows:** 8 articles × 6 summaries = 48 rows

---

### subscriptions.db (Secondary Database)
**Location:** `/Users/jidai/news/subscriptions.db`

#### Table 1: `categories`
Purpose: Article categories/topics

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,              -- "World", "Science", "Sports", "Tech"
    website TEXT,
    description TEXT,
    color TEXT,
    emoji TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### Table 2: `article_summaries` (Different from articles.db!)
Purpose: Enhanced summaries with quiz content

```sql
CREATE TABLE article_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    difficulty TEXT,
    language TEXT,
    summary TEXT,
    keywords TEXT,                          -- JSON or comma-separated
    background TEXT,                        -- Context/background info
    pro_arguments TEXT,                     -- Pro arguments
    con_arguments TEXT,                     -- Con arguments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### Table 3: `quiz_questions`
Purpose: Store quiz questions for articles

```sql
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    difficulty TEXT,
    question_number INTEGER,
    question_text TEXT,
    options TEXT,                           -- JSON array
    correct_answer INTEGER,                 -- Index of correct option
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### Table 4: `articles_enhanced`
Purpose: Link between original articles and categories

```sql
CREATE TABLE articles_enhanced (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_article_id INTEGER,            -- FK to articles.db articles.id
    title TEXT NOT NULL,
    date TEXT,
    source TEXT,
    image_file TEXT,
    category_id INTEGER,                    -- FK to categories.id
    original_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

---

#### Table 5: `subscriptions_enhanced`
Purpose: Store subscriber preferences

```sql
CREATE TABLE subscriptions_enhanced (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    age_group TEXT,                         -- "8-10", "11-13", "14+"
    difficulty_level TEXT,                  -- "easy", "mid", "high"
    interests TEXT,                         -- JSON or comma-separated
    frequency TEXT DEFAULT 'daily',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent TIMESTAMP,
    confirmed BOOLEAN DEFAULT 0
);
```

---

#### Table 6: `email_logs`
Purpose: Track sent emails

```sql
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    age_group TEXT,
    difficulty_level TEXT,
    subject TEXT,
    status TEXT,
    email_id TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Architecture Issues

### Problem 1: Two Separate Databases
- `articles.db` - Main articles + summaries (data collection)
- `subscriptions.db` - Enhanced data + subscriptions (user management)

**Question:** Should these be merged or kept separate?

---

### Problem 2: Data Collection Pipeline
Currently embedded in `run_full_pipeline.py`:
1. **Crawl RSS** → Store in `articles` table
2. **Fetch Content** → Add to `articles` table
3. **Process Deepseek** → Insert into `article_summaries` table
4. **Generate HTML** → Create HTML files
5. **Generate JSON** → Create JSON output

**Issue:** Everything is mixed together. Hard to debug!

---

### Problem 3: Current State
- ✅ 8 articles collected
- ❌ 0 summaries generated (deepseek_processed = 0)
- ❌ No JSON output file
- ❌ No HTML pages
- ❌ Everything waiting for Deepseek processing

---

## Proposed Solution: Separate Concerns

### Phase 1: Data Collection Module (`data_collector.py`)
**Purpose:** Only collect and store article data
**Output:** Populate `articles` table with raw data

Operations:
- Fetch RSS feeds
- Extract article content
- Download images
- Store in database
- **No Deepseek processing!**

---

### Phase 2: Data Processing Module (`data_processor.py`)
**Purpose:** Only process collected articles through Deepseek
**Input:** Articles with `deepseek_processed = 0`
**Output:** Populate `article_summaries` table

Operations:
- Find unprocessed articles
- Call Deepseek API for 6 summaries
- Store in database
- Update `deepseek_processed = 1`
- **No HTML generation!**

---

### Phase 3: Page Generation Module (`page_generator.py`)
**Purpose:** Only generate HTML/JSON output
**Input:** Articles + summaries from database
**Output:** HTML pages + JSON files

Operations:
- Read from database
- Build page structure
- Generate JSON
- Write to files
- **No data modification!**

---

## Testing Plan for MAC

### Step 1: Verify Data Collection
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"     # Should be 8
sqlite3 articles.db "SELECT * FROM article_summaries;"   # Should be empty
```

### Step 2: Test Data Processing (Deepseek)
```bash
# Only run Deepseek, don't touch articles table
export DEEPSEEK_API_KEY='sk-...'
python3 data_processor.py
```

### Step 3: Verify Summaries
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM article_summaries;"  # Should be 48 (8×6)
sqlite3 articles.db "SELECT DISTINCT difficulty, language FROM article_summaries ORDER BY 1,2;"
```

### Step 4: Test Page Generation
```bash
python3 page_generator.py
ls output/articles_data.json                 # Should exist with all fields
```

### Step 5: Deploy to EC2 Only After MAC Verification

---

## Questions for You

1. **Database:** Keep two databases or merge into one?
   - Option A: Keep separate (simpler migration path)
   - Option B: Merge into single database (cleaner design)

2. **Data Flow:** Do you want these 3 separate scripts?
   - `data_collector.py` - RSS collection only
   - `data_processor.py` - Deepseek processing only
   - `page_generator.py` - HTML/JSON output only

3. **Summaries:** For `article_summaries` table:
   - Current: `(difficulty, language)` columns
   - Store with difficulty="easy_en" (combined) or separate columns?

4. **Testing:** Should we:
   - First verify 8 articles are correct?
   - Then test Deepseek on 1 article?
   - Then process all 8?
   - Then generate pages?

---

## Current File List

```
Databases:
- articles.db (8 articles, 0 summaries)
- subscriptions.db (empty tables)

Current Pipeline (MONOLITHIC):
- run_full_pipeline.py (937 lines - does EVERYTHING)

HTML/JSON Output:
- main_articles_interface_v2.html (homepage - expects JSON)
- article_analysis_v2.html (detail page - expects JSON)
- output/articles_data.json (probably needs regeneration)
```

---

## Recommendation

✅ **Let's proceed step-by-step on MAC:**

1. Review this schema
2. Verify 8 articles are correct
3. Create `data_processor.py` - run ONE test article
4. Verify summaries table is populated correctly
5. Run on all 8 articles
6. Create `page_generator.py`
7. Test homepage and detail pages locally
8. **ONLY THEN** deploy to EC2

This way we know everything works before touching the server!
