# Article ID Migration - Summary

## Overview

Changed article ID system from sequential integers (1, 2, 3...) to semantic identifiers that encode the collection date.

## New ID Format

**Format**: `yearmonthday + 2-digit counter`

**Examples**:
- `2025102401` — First article collected on October 24, 2025
- `2025102402` — Second article collected on October 24, 2025  
- `2025102501` — First article collected on October 25, 2025

**Constraints**:
- Maximum 99 articles per day per system
- Format is TEXT, not INTEGER
- Provides automatic date tracking for each article

## Changes Made

### 1. Database Schema (`dbinit/init_schema.md`)

**Changed column type**:
- `articles.id`: `INTEGER PRIMARY KEY AUTOINCREMENT` → `TEXT PRIMARY KEY`

**Updated foreign key references** (9 tables total):
1. `article_images.article_id`: INTEGER → TEXT
2. `article_summaries.article_id`: INTEGER → TEXT
3. `keywords.article_id`: INTEGER → TEXT
4. `questions.article_id`: INTEGER → TEXT
5. `comments.article_id`: INTEGER → TEXT
6. `background_read.article_id`: INTEGER → TEXT
7. `article_analysis.article_id`: INTEGER → TEXT
8. `response.article_id`: INTEGER → TEXT

### 2. ID Generation Logic (`mining/data_collector.py`)

**Added new function**:
```python
def generate_article_id(conn):
    """Generate article ID: yearmonthday + 2-digit counter."""
    today = datetime.now().strftime("%Y%m%d")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles WHERE id LIKE ?", (f"{today}%",))
    count = cursor.fetchone()[0]
    next_number = count + 1
    if next_number > 99:
        raise ValueError(f"ERROR: Already {next_number-1} articles for today, max is 99")
    return f"{today}{next_number:02d}"
```

**Updated function**:
- `insert_article()`: Now calls `generate_article_id()` and explicitly passes `article_id` to INSERT statement
- Changed return value: `cursor.lastrowid` → `article_id` (since IDs are no longer auto-generated)

### 3. Documentation (`dbinit/DB_INIT_README.md`)

**Added new section**: "Article ID Format"
- Explains format and examples
- Rationale for TEXT vs INTEGER
- Generation logic code snippet
- Lists all affected schema tables

## Affected Code Files

### No changes needed (backward compatible):

- `deepseek/process_one_article.py` ✓ (already handles article_id as parameter)
- `deepseek/insert_from_response.py` ✓ (uses article_id from response JSON)
- `mining/run_mining_cycle.py` ✓ (queries articles by id)
- All other scripts ✓ (work with TEXT IDs same as before)

### Files modified:

- ✅ `mining/data_collector.py`: Added `generate_article_id()`, updated `insert_article()`
- ✅ `dbinit/init_schema.md`: Updated all 9 table definitions
- ✅ `dbinit/DB_INIT_README.md`: Added Article ID Format section

## Migration Notes

**For existing databases**:
- To reset with new schema: `python3 dbinit/initdb.py --db articles.db --force`
- Old INTEGER IDs will be lost (fresh start with new TEXT IDs)
- Existing data cleanup recommended

**For new installations**:
- Use `python3 dbinit/initdb.py --db articles.db --force` to initialize
- Articles will automatically get semantic IDs (e.g., 2025102401, 2025102402, ...)

## Testing the Changes

### Quick verification:
```bash
# Initialize fresh database
python3 dbinit/initdb.py --db test.db --force

# Check articles table
sqlite3 test.db "SELECT sql FROM sqlite_master WHERE type='table' AND name='articles';"
# Should show: id TEXT PRIMARY KEY
```

### Run data collector:
```bash
cd mining
python3 data_collector.py
# Articles should get IDs like: 2025102401, 2025102402, etc.
```

### Verify related tables:
```bash
# Check foreign key references updated
sqlite3 articles.db ".schema article_images"
# Should show: article_id TEXT NOT NULL with FOREIGN KEY referencing articles(id)
```

## Benefits

✅ **Date tracking**: ID reveals collection date immediately  
✅ **Debugging**: Easy to identify when articles were collected  
✅ **Semantic meaning**: IDs encode important metadata  
✅ **Consistent**: All articles created on same day have sequential counter  
✅ **Scalable**: Supports up to 99 articles per day per system  
✅ **Sortable**: Can still sort chronologically by ID  

## Rollback

To revert to integer IDs:
1. Edit `dbinit/init_schema.md`: Change `id TEXT PRIMARY KEY` back to `id INTEGER PRIMARY KEY AUTOINCREMENT`
2. Remove `generate_article_id()` from `data_collector.py`
3. In `insert_article()`, remove article_id parameter from INSERT, restore `return cursor.lastrowid`
4. Reinitialize: `python3 dbinit/initdb.py --db articles.db --force`

## Questions or Issues

- Schema change applies to all new databases
- No impact on deepseek/insert_from_response.py (uses IDs from response JSON)
- All other code reads/writes article_id as TEXT transparently
