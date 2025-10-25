# Mining Pipeline - Complete Documentation

## Overview

The mining pipeline is responsible for collecting articles from RSS feeds and preparing them for Deepseek analysis. It handles data collection, content cleaning, image downloading, and article quality filtering.

**What Mining Does**:
1. ✅ **Fetches articles from RSS feeds** → stored in `articles` table
2. ✅ **Cleans and validates content** → removes boilerplate, bylines, promos
3. ✅ **Downloads and stores images** → saved to `website/article_image/`
4. ✅ **Applies age-13 filtering** → removes banned content
5. ✅ **Selects articles for processing** → marks best candidates
6. ❌ **Does NOT call Deepseek API** ← That's a separate pipeline stage

## Architecture

```
RSS Feeds (external sources)
       ↓
   [data_collector.py] - RSS feed crawler & data collection
       ↓
  articles.db (articles table)
       ↓
Image & Content Processing
       ↓
[run_mining_cycle.py] - Article selection & optional API processing
       ↓
[mining pipeline ready] - Articles prepared for Deepseek analysis
```

## Core Components

### 1. `data_collector.py` - Main Collector

**Purpose**: Fetches articles from RSS feeds, cleans content, downloads images, and stores in database

**Key Features**:
- Fetches articles from RSS feeds listed in `feeds` table
- HTML parsing and paragraph extraction
- Content cleaning with filters (bylines, promos, boilerplate removal)
- **Dynamic image directory**: Images now saved to `website/article_image/` (server-agnostic)
- Age-13 content filtering
- Quality thresholds validation
- Database insertion with category mapping

**Processing Steps**:
1. Load feeds from database
2. For each feed:
   - Fetch RSS XML
   - Parse article entries
   - Download article content (HTML)
   - Extract and clean paragraphs
   - Download and store article image
   - Validate content quality
   - Insert into articles table
3. Automatic categorization based on feed mapping

**Image Handling** (Updated):
- **Location**: `website/article_image/` (dynamic path, server-agnostic)
- **Filename format**: `article_{id}_{hash}{ext}`
- **Image sources priority**:
  1. OpenGraph meta (`og:image`)
  2. Twitter meta (`twitter:image`)
  3. Link rel image_src
  4. Picture/source tags
  5. Article img elements
- **Filters applied**:
  - Skip PNGs (usually logos/placeholders)
  - Skip favicon/logo/placeholder URLs
  - Minimum byte thresholds (configurable):
    - Quick: 2 KB (fast previews)
    - Batch: 70 KB (batch processing)
    - Collection: 100 KB (full collection)
  - Prefer same-origin images
  - Prefer high-resolution candidates

### 2. `run_mining_cycle.py` - Mining Orchestrator (Active)

**Purpose**: Main entry point for the mining pipeline

**Features**:
- Loads source-specific thresholds from `thresholds.json`
- Integrates with `data_collector.py`
- Groups articles by feed/source
- Selects top N articles per source using sampling
- Dry-run mode (preview only)
- Live mode with optional Deepseek API calls
- Database updating via `insert_from_response.py`

**Usage**:

```bash
# Dry-run mode (preview only, no changes)
python3 run_mining_cycle.py

# Live mode (process and update database)
python3 run_mining_cycle.py --apply
```

**Workflow**:
1. Calls `data_collector.collect_articles()`
2. Queries unprocessed articles grouped by source
3. Samples N articles per source (configurable)
4. For each article:
   - Claims article (marks as in_progress)
   - Dry-run: saves placeholder, releases claim
   - Live: calls Deepseek API, runs inserter, updates DB

## Configuration

### `thresholds.json` - Quality & Mining Parameters

```json
{
  "paragraph_min_length": 30,                    // Min chars per paragraph
  "cleaned_chars_min_global": 2300,              // Min cleaned content length
  "cleaned_chars_max_global": 4500,              // Max cleaned content length
  "sport_strict_min_chars": 1500,                // Sports articles min (strict)
  "sport_relaxed_min_chars": 1200,               // Sports articles min (relaxed)
  "collect_preview_min_image_bytes": 100000,     // Collection threshold: 100 KB
  "batch_min_image_bytes": 70000,                // Batch threshold: 70 KB
  "quick_min_image_bytes": 2000,                 // Quick threshold: 2 KB
  "per_feed_timeout": 240,                       // Timeout per feed (seconds)
  "num_per_source": 5,                           // Articles to mine per source
  "sample_rate": 10,                             // 1-in-N sampling rate
  "random_seed": 42                              // For reproducible selection
}
```

**Key Settings**:
- `cleaned_chars_min_global` / `cleaned_chars_max_global`: Content quality range
- `num_per_source`: How many articles to select per feed
- `per_feed_timeout`: Prevents long-running feeds from blocking pipeline
- `sample_rate`: 1-in-N articles selected (1/10 = 10% selected)
- Image byte thresholds: Adjust based on desired image quality

### `age13_banned.txt` - Content Filter

**Location**: `mining/age13_banned.txt`

**Purpose**: Newline-separated list of banned words/phrases for age-13 filtering

**Behavior**: Articles containing banned words are dropped entirely (case-insensitive, whole-word matching)

**Example entries**: `rape`, `rapist`, `fuck`, `blowjob`, `pedophile`, `incest`, `murder`, `suicide`

**Usage**: Applied during content collection via `data_collector.py`

## Content Filtering

### Global Filters (Applied by `clean_paragraphs()`)

1. **HTML Unescape**: Normalize entities and punctuation
2. **Short Paragraph Removal**: < 30 characters (configurable)
3. **Byline Detection**: Removes author names and repeated names
   - Author name patterns (e.g., "By John Smith")
   - Repeated two-word names (e.g., "Nick Schifrin Nick Schifrin")
   - Short all-caps names (likely bylines)
4. **Promo Filtering**: Removes promotional content
   - Emoji-led promos: ✅, 🔒, 🔥, ⭐, ✨, 💥, 🚨, 🎉
   - Sales language: "off", "save", "discount", "buy now"
   - Affiliate terms: "sign up", "sponsored", "vpn", "nordvpn"
5. **Boilerplate Removal**: Removes publisher footers
   - Publisher statements: "Follow TechRadar"
   - Funding statements: "Funding:"
   - Trailing footers (addresses, copyright)
6. **Related Links**: Removes "Related:" paragraphs
7. **Duplicates**: Removes consecutive duplicate paragraphs
8. **Content Length**: Validates minimum/maximum ranges

### Article Type Filters

1. **Video Detection**: 
   - Skips articles with "Watch:", "video:", "full episode"
   - Application: News/entertainment feeds

2. **Transcript Detection**: 
   - Skips interview/Q&A format articles
   - Detects speaker patterns and "transcript + audio"
   - Removes repeated "Name: quote" patterns

3. **Games/Filler Detection**: 
   - Skips puzzles, wordle-style pieces
   - Removes low-value content

### Age-13 Banned-Word Filter (Strict Removal)

**Behavior**: Case-insensitive, whole-word-ish matching

**Regex pattern**: `(?i)(?<!\w)(word1|word2|...)(?!\w)`

**Impact**: Articles matching ANY banned term are dropped entirely (not cleaned, not included in outputs)

## Database Schema (Key Tables)

### articles
```sql
id                    INTEGER PRIMARY KEY
title                 TEXT
source                TEXT
url                   TEXT UNIQUE
description           TEXT
content               TEXT          -- Cleaned paragraph content
pub_date              TEXT
crawled_at            TEXT
category_id           INTEGER       -- Links to categories table
image_id              INTEGER       -- Links to article_images table

-- Deepseek processing fields
deepseek_processed    BOOLEAN       -- 1 = successfully processed
deepseek_failed       INTEGER       -- failure count
deepseek_last_error   TEXT          -- error message
deepseek_in_progress  INTEGER       -- being processed
processed_at          TEXT          -- timestamp
```

### article_images
```sql
image_id              INTEGER PRIMARY KEY
article_id            INTEGER
image_name            TEXT          -- Filename (e.g., article_1_abc123.jpg)
original_url          TEXT          -- Source URL
local_location        TEXT          -- Full path to file
new_url               TEXT          -- (optional) CDN/served URL
```

### feeds
```sql
feed_id               INTEGER PRIMARY KEY
feed_name             TEXT
feed_url              TEXT
category_id           INTEGER       -- Links to categories
enable                BOOLEAN       -- Whether to fetch this feed
created_at            TEXT
```

## Workflow

### Standard Mining Workflow

```
1. Run data_collector.py (or scheduled via cron)
   ↓
2. Parse RSS feeds from feeds table
   ↓
3. For each article:
   - Extract content from article HTML
   - Clean paragraphs (remove boilerplate, bylines, etc.)
   - Apply age-13 banned word filter
   - Download image → website/article_image/
   - Validate quality thresholds
   - Insert into articles table
   ↓
4. Run run_mining_cycle.py
   ↓
5. Select top N articles per source
   ↓
6. Ready for Deepseek processing
```

### Article Selection Logic

**Sampling Method**: 1-in-N random selection
- `sample_rate = 10` means 10% of articles selected
- `num_per_source = 5` means up to 5 articles per feed selected
- Reproducible: uses `random_seed` for consistent results

**Article Claiming**: Prevents concurrent processing
- `deepseek_in_progress = 1` when processing
- Released on dry-run or after inserter completes
- Prevents duplicate processing

### Image Organization

**Before**: Images saved to `article_images/` (root level)

**After (Updated)**: Images saved to `website/article_image/` (dynamic path)

**Benefits**:
- Organized with website structure
- Dynamic paths work on any server
- Consistent with `article_response/` organization
- Easier deployment

## File Organization

```
mining/
├── data_collector.py          # Main collector
├── run_mining_cycle.py        # Mining orchestrator (ACTIVE)
├── mining_latest.md           # This documentation (CURRENT)
├── thresholds.json            # Configuration
├── age13_banned.txt           # Age-13 filter (moved from config/)
└── responses/                 # (optional) Preview outputs
       └── response_article_*.json

website/
├── article_page/              # Reserved for article pages
├── article_image/             # **Article images (updated location)**
└── article_response/          # Deepseek response files

articles.db                    # SQLite database
```

## Usage Guide

### Collect Articles from RSS

```bash
cd /Users/jidai/news
source .venv/bin/activate

# Import all configured feeds
python3 mining/data_collector.py

# Check status
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
```

### Mine Articles for Processing

```bash
# Dry-run (preview what would happen)
python3 mining/run_mining_cycle.py

# Apply mining (mark articles for processing)
python3 mining/run_mining_cycle.py --apply

# Check mining results
sqlite3 articles.db "SELECT id, title, deepseek_in_progress FROM articles LIMIT 10;"
```

### View Image Storage

```bash
# Check collected images
ls -lh website/article_image/ | head -20

# Count total images
ls -1 website/article_image/ | wc -l

# View image records in database
sqlite3 articles.db "SELECT image_id, article_id, image_name FROM article_images LIMIT 10;"
```

## Deployment Notes

### Server Path Compatibility

All image paths are **dynamically computed**:
- Works in `/home/user/news/mining/`
- Works in `/var/www/news/mining/`
- Works in `/opt/news/mining/`
- No hardcoded paths to modify

### Image Directory Creation

Directories are automatically created:
```python
Path(output_dir).mkdir(parents=True, exist_ok=True)
```

So `website/article_image/` will be created automatically on first run.

## Performance Characteristics

- **Per-feed processing**: 30-120 seconds (depending on feed size)
- **Per-article processing**: 5-15 seconds
- **Image download**: 1-5 seconds per article
- **Batch processing 50 articles**: ~5-10 minutes

## Troubleshooting

### No Articles Collected

```sql
-- Check if feeds are enabled
SELECT * FROM feeds WHERE enable = 1;

-- Check if articles were inserted
SELECT COUNT(*) FROM articles;
```

### Images Not Downloaded

```bash
# Check directory exists
ls -ld website/article_image/

# Check for errors in article_images table
SELECT COUNT(*) FROM article_images;

# Verify permissions
ls -l website/ | grep article_image
```

### Content Too Short/Long

Adjust thresholds in `thresholds.json`:
```json
{
  "cleaned_chars_min_global": 2000,    // Lower minimum
  "cleaned_chars_max_global": 5000     // Raise maximum
}
```

## Filters and Heuristics Reference

### Image Selection Rules

- **Preference order**: OpenGraph → Twitter → image_src → srcset → article imgs
- **Filtering**: Skip PNGs, favicons, logos, placeholders
- **Byte gates**: Quick (2KB) → Batch (70KB) → Collection (100KB)
- **Srcset parsing**: Selects largest width or highest DPI

### Content Cleaning Rules

- **Paragraph minimum**: 30 characters (removes bylines/tags)
- **Byline patterns**: Author names, repeated names, all-caps
- **Promo patterns**: Emoji leads, sale language, affiliate terms
- **Boilerplate patterns**: Publisher statements, footers, copyright
- **Length validation**: Global min 2300 chars, max 4500 chars

## Quick Start

```bash
# 1. Collect articles from all feeds
python3 mining/data_collector.py

# 2. Preview mining results (dry-run)
python3 mining/run_mining_cycle.py

# 3. Apply mining and optionally call Deepseek
python3 mining/run_mining_cycle.py --apply

# 4. Verify results
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1;"
```

## Next Steps in Pipeline

After mining collects and processes articles:

1. **Deepseek API Processing** (separate pipeline):
   - Run: `python3 deepseek/process_one_article.py`
   - Analyzes article content with Deepseek AI
   - Generates responses in all 4 levels
   - Saves to `website/article_response/`

2. **Database Integration**:
   - Run: `python3 deepseek/insert_from_response.py`
   - Updates response table
   - Updates articles table with processing status

3. **Frontend Display**:
   - Use responses in `website/article_response/`
   - Display on student learning interface

## Key Improvements in Latest Version

✅ **Dynamic Image Paths**: Images now use server-agnostic dynamic paths (`website/article_image/`)

✅ **Organized Structure**: Images stored alongside responses in `website/` directory

✅ **Consistent Naming**: Matches pattern with `article_response/` organization

✅ **Scalable Architecture**: Works across different server deployments without modifications

✅ **Age-13 Filter**: Moved to `mining/` directory with mining tools for better organization

✅ **Single Documentation**: `mining_latest.md` consolidates all mining knowledge (replaces 4 old docs)

✅ **Active Script**: `run_mining_cycle.py` is the maintained entry point (removed redundant `run_mining_round.py`)

## Related Documentation

- **Deepseek Analysis**: See `deepseek/deepseek_analyze_latest.md`
- **Database Schema**: See `dbinit/init_schema.md`
- **API Integration**: See `deepseek/README.md`
