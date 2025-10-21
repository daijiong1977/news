# Schema Migration: Add category_id Column

**Date:** October 20, 2025  
**Status:** ✅ COMPLETED

---

## What Changed

### Migration Executed
```
Added: category_id INTEGER column to articles table
```

### Before
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

### After
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
    processed_at TEXT,
    category_id INTEGER                      -- ✨ NEW
);
```

---

## Column Details

### category_id
- **Type:** INTEGER
- **Nullable:** YES (can be NULL)
- **Default:** NULL (no default)
- **Purpose:** Link article to a category
- **Relationship:** `articles.category_id` → `categories.id` (in subscriptions.db or future merged DB)

---

## Why This Change?

### Current State
- Articles from 4 sources: PBS, Swimming World, TechRadar, Science Daily
- No way to organize by category in the database

### New Capability
- Each article can be assigned to a category
- Categories table (in subscriptions.db) has: id, name, emoji, color, etc.
- Enables category-based filtering on homepage
- Example: "🌍 World", "🏊 Sports", "💻 Tech", "🔬 Science"

---

## How to Use

### Setting Category
```sql
-- Assign PBS articles to "World" category (id=1)
UPDATE articles SET category_id = 1 WHERE source = 'PBS NewsHour';

-- Assign Swimming articles to "Sports" category (id=2)
UPDATE articles SET category_id = 2 WHERE source = 'Swimming World Magazine';

-- Assign TechRadar to "Tech" category (id=3)
UPDATE articles SET category_id = 3 WHERE source = 'TechRadar';
```

### Querying by Category
```sql
-- Get all articles in a category
SELECT * FROM articles WHERE category_id = 1;

-- Get articles without a category
SELECT * FROM articles WHERE category_id IS NULL;

-- Count by category
SELECT category_id, COUNT(*) FROM articles GROUP BY category_id;
```

### NULL Handling
```sql
-- Articles with NULL category_id will be uncategorized
-- They'll still appear on homepage, just not filtered by category
```

---

## Migration Script

### File: migrate_db.py

Usage:
```bash
# Show current schema only (no changes)
python3 migrate_db.py --no-migrate

# Run migration (interactive - asks for confirmation)
python3 migrate_db.py

# Non-interactive
echo "yes" | python3 migrate_db.py
```

Features:
- Shows current schema before migration
- Checks if column already exists (idempotent)
- Prompts for confirmation before making changes
- Verifies column was added successfully
- Displays new schema after completion

---

## Updated Configuration Scripts

### clean_databases.py
- Updated to include `category_id` when recreating fresh schema
- Safe to run: `python3 clean_databases.py --drop`

### DATABASE_SCHEMA_REVIEW.md
- Updated to show new column
- Documentation synced with actual schema

---

## Data Flow with Categories

### Before (No Categories)
```
RSS Feed → Article → Display
```

### After (With Categories)
```
RSS Feed → Article → Category Assignment → Filtered Display
                    ↓
                  DB Query by category_id
```

### Example Article Record
```json
{
  "id": 1,
  "title": "Ukraine uses drones to hit Russian gas plant",
  "source": "PBS NewsHour",
  "url": "https://...",
  "content": "...",
  "category_id": 1,
  "deepseek_processed": 0
}
```

---

## Next Steps

### Step 1: Populate Categories (if needed)
```sql
-- Insert category records in subscriptions.db
INSERT INTO categories (name, emoji, color) VALUES 
  ('World', '🌍', '#667eea'),
  ('Sports', '🏊', '#4caf50'),
  ('Tech', '💻', '#ff9800'),
  ('Science', '🔬', '#2196f3');
```

### Step 2: Assign Categories to Articles
```sql
-- When collecting articles, determine category from source
UPDATE articles SET category_id = 1 WHERE source LIKE 'PBS%';
UPDATE articles SET category_id = 2 WHERE source LIKE '%Swimming%';
UPDATE articles SET category_id = 3 WHERE source LIKE '%TechRadar%';
UPDATE articles SET category_id = 4 WHERE source LIKE '%Science%';
```

### Step 3: Use in Queries
```python
# In data_collector.py or data_processor.py:
# Map sources to category IDs automatically

SOURCE_TO_CATEGORY = {
    'PBS NewsHour': 1,
    'Swimming World Magazine': 2,
    'TechRadar': 3,
    'Science Daily': 4
}

# When inserting: article['category_id'] = SOURCE_TO_CATEGORY.get(article['source'])
```

---

## Verification

### Check Column Exists
```bash
sqlite3 articles.db "PRAGMA table_info(articles)" | grep category_id
# Output: 12|category_id|INTEGER|0||0
```

### Check Current Values
```bash
sqlite3 articles.db "SELECT COUNT(*) as total, COUNT(category_id) as categorized, COUNT(*) - COUNT(category_id) as uncategorized FROM articles;"
# Output: 0|0|0 (all empty after cleanup)
```

---

## Backward Compatibility

✅ **Fully compatible:**
- NULL values default for existing queries
- No breaking changes to existing code
- Optional field (not required)
- Can be left NULL indefinitely

---

## Related Documentation

- `DATABASE_SCHEMA_REVIEW.md` - Updated schema reference
- `clean_databases.py` - Updated cleanup script
- `migrate_db.py` - Migration script

---

## Summary

**Migration:** ✅ COMPLETE
- Column added to articles table
- Schema preserved
- Fully backward compatible
- Ready for data population
- Next: Assign categories to sources during data collection
