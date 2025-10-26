# Database Initialization Guide

This directory contains the database schema and initialization scripts for the `articles.db` SQLite database.

## Directory Contents

- **`init_schema.md`** — Master schema file containing all CREATE TABLE statements in markdown format
- **`init_data.json`** — Seed data in JSON format for lookup tables (categories, difficulty_levels, feeds, apikey, etc.)
- **`initdb.py`** — Python script that reads the schema and data files and initializes the database
- **`migration_20251026_payload_tracking.sql`** — Migration to add payload tracking fields to response table

## Article ID Format

**Format**: `yearmonthday + 2-digit counter` (TEXT, NOT INTEGER)

**Examples**:
- `2025102401` — First article collected on October 24, 2025
- `2025102402` — Second article collected on October 24, 2025
- `2025102501` — First article collected on October 25, 2025

**Why TEXT instead of INTEGER?**
- Allows for semantic article identifiers that encode the collection date
- Easier debugging and tracing (can identify when article was collected from ID alone)
- Supports up to 99 articles per day per system
- Still sortable and indexable in SQL

**Generation Logic** (in `mining/data_collector.py`):
```python
def generate_article_id(conn):
    """Generate article ID: yearmonthday + 2-digit counter"""
    today = datetime.now().strftime("%Y%m%d")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles WHERE id LIKE ?", (f"{today}%",))
    count = cursor.fetchone()[0]
    next_number = count + 1
    return f"{today}{next_number:02d}"
```

**Related Schema Changes**:
- `articles.id`: Changed from `INTEGER PRIMARY KEY AUTOINCREMENT` to `TEXT PRIMARY KEY`
- All foreign keys referencing `articles.id` updated to `TEXT`:
  - `article_images.article_id`
  - `article_summaries.article_id`
  - `keywords.article_id`
  - `questions.article_id`
  - `comments.article_id`
  - `background_read.article_id`
  - `article_analysis.article_id`
  - `response.article_id`

## Quick Start

### Initialize a Fresh Database

To create or recreate the `articles.db` from scratch:

```bash
cd /Users/jidai/news/dbinit
python3 initdb.py --db ../articles.db --force
```

**Important**: The `--force` flag will:
1. Back up your existing `articles.db` to `backups/articles.db.backup_<timestamp>.sqlite`
2. Delete the existing `articles.db`
3. Create a fresh database with all tables
4. Populate lookup tables with seed data from `init_data.json`

### Test Without Touching Real Database

To test schema changes safely:

```bash
python3 initdb.py --db test_articles.sqlite --schema init_schema.md --data init_data.json
```

This creates a temporary test database without affecting the production database.

## How to Modify Schema

### Adding a New Table

1. **Edit `init_schema.md`**:
   - Add a new section with a markdown heading (e.g., `### my_new_table`)
   - Include a SQL code block with the `CREATE TABLE` statement
   
   Example:
   ```markdown
   ### my_new_table
   ```
   CREATE TABLE my_new_table (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL,
       value TEXT
   )
   ```
   ```

2. **Test it**:
   ```bash
   python3 initdb.py --db test_articles.sqlite --schema init_schema.md --data init_data.json
   ```

3. **Apply to production**:
   ```bash
   python3 initdb.py --db ../articles.db --force
   ```

### Modifying an Existing Table

1. **Edit the CREATE TABLE statement in `init_schema.md`**:
   - Add columns by adding new lines in the table definition
   - Remove columns by deleting the column lines
   - Modify constraints, defaults, or data types as needed

2. **Test and apply** (same steps as adding a table above)

### Deleting a Table

1. **Remove the entire section from `init_schema.md`** (both the heading and code block)

2. **Test and apply** (same steps as adding a table above)

## How to Modify Seed Data

### Adding or Updating Seed Data

1. **Edit `init_data.json`**:
   - The file contains a JSON object with table names as keys
   - Each value is an array of row objects
   
   Example structure:
   ```json
   {
     "apikey": [
       { "name": "DeepSeek", "value": "sk-..." },
       { "name": "buttondown", "value": "743996df-..." }
     ],
     "categories": [
       { "category_id": 1, "category_name": "News", ... }
     ]
   }
   ```

2. **Add new rows**:
   - Add objects to the appropriate table array
   
   Example:
   ```json
   "categories": [
     { "category_id": 1, "category_name": "News", "description": "...", ... },
     { "category_id": 8, "category_name": "Politics", "description": "...", ... }
   ]
   ```

3. **Test and apply**:
   ```bash
   python3 initdb.py --db test_articles.sqlite --schema init_schema.md --data init_data.json
   python3 initdb.py --db ../articles.db --force
   ```

## Understanding the Initialization Process

### What `initdb.py` Does

1. **Parses `init_schema.md`**:
   - Extracts all SQL statements from markdown code blocks
   - Looks for statements that start with `CREATE TABLE`

2. **Creates Tables**:
   - Executes each `CREATE TABLE IF NOT EXISTS` statement
   - This makes the initialization idempotent (safe to run multiple times)

3. **Loads Seed Data**:
   - Reads `init_data.json`
   - For each table in the JSON, inserts rows using `INSERT OR REPLACE`
   - This ensures existing rows are updated if re-running the script

### Command-Line Options

```bash
python3 initdb.py [OPTIONS]

OPTIONS:
  --force              Backup and remove existing DB before recreating (destructive)
  --db PATH           Path to sqlite DB (default: ../articles.db)
  --schema PATH       Path to schema markdown file (default: ./init_schema.md)
  --data PATH         Path to JSON seed data file (default: ./init_data.json)
```

## Current Schema (18 Tables)

1. **article_analysis** — Analysis data for articles by difficulty level
2. **article_images** — Images associated with articles
3. **article_summaries** — Summaries of articles
4. **articles** — Main articles table
5. **background_read** — Background reading material
6. **apikey** — API keys (DeepSeek, buttondown, etc.)
7. **categories** — Article categories (News, Science, etc.)
8. **choices** — Multiple choice options for questions
9. **comments** — User comments on articles
10. **difficulty_levels** — Reading difficulty levels (Relax, Enjoy, Research, Chinese)
11. **feeds** — RSS feed sources
12. **keywords** — Keywords extracted from articles
13. **questions** — Questions about articles
14. **user_awards** — User achievement/award tracking
15. **user_categories** — User preferences for categories
16. **user_difficulty_levels** — User preferences for difficulty levels
17. **user_preferences** — General user preferences
18. **users** — User accounts

## Current Seed Data

### apikey Table
- **DeepSeek**: API key for DeepSeek LLM service
- **buttondown**: API key for Buttondown email service

### categories Table (7 rows)
- News, Science, Fun, Technology, Business, Sports, Entertainment

### difficulty_levels Table (4 rows)
- Relax (3-5), Enjoy (6-8), Research (9-12), Chinese (9-12)

### feeds Table (13 rows)
- Various RSS feeds for News, Science, Business, Sports, Entertainment categories

## Common Workflows

### Workflow 1: Add a New Column to Existing Table

1. Edit the CREATE TABLE statement in `init_schema.md` for that table
2. Add the new column definition
3. Run: `python3 initdb.py --db ../articles.db --force`

### Workflow 2: Add a New Lookup Table with Seed Data

1. Add table definition to `init_schema.md`
2. Add seed data array to `init_data.json`
3. Run: `python3 initdb.py --db ../articles.db --force`

### Workflow 3: Update Seed Data Only (Keep Schema)

1. Edit the JSON arrays in `init_data.json`
2. **Don't use `--force`** (keep existing tables):
   ```bash
   python3 initdb.py --db ../articles.db
   ```
   This will update rows but keep existing schema and data tables

### Workflow 4: Backup Current Database

1. The initializer automatically creates timestamped backups:
   ```bash
   python3 initdb.py --db ../articles.db --force
   # Creates: backups/articles.db.backup_20251024T153045Z.sqlite
   ```

## Troubleshooting

### "Schema file not found"
- Make sure you're in the `dbinit/` directory or provide the full path to `init_schema.md`

### "Data file not found"
- Make sure `init_data.json` exists in the `dbinit/` directory

### "FOREIGN KEY constraint failed"
- Check that referenced tables exist and have matching data
- Example: Feeds reference categories by `category_id`, ensure those categories exist

### "table X already exists"
- This is normal during re-initialization with `--force`
- The script uses `CREATE TABLE IF NOT EXISTS`, so existing tables are skipped safely

## Notes

- **Idempotent Design**: You can run the initializer multiple times; it won't cause errors
- **Backup Safety**: Always backs up the existing DB before `--force` recreation
- **No Dependencies**: Only requires Python 3 and sqlite3 (both built-in)
- **JSON Format**: Keep `init_data.json` valid JSON; use JSON validators if unsure
- **Markdown Format**: `init_schema.md` uses markdown with SQL code blocks (triple backticks)

## Advanced: Manual SQL Queries

To query the database directly:

```bash
sqlite3 ../articles.db
sqlite> SELECT * FROM categories;
sqlite> SELECT * FROM apikey;
sqlite> .tables  # List all tables
sqlite> .schema  # Show all CREATE TABLE statements
```

---

**Last Updated**: 2025-10-24
