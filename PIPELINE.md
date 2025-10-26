# News Pipeline - Complete Documentation

**Last Updated**: October 26, 2025

## Overview

The News Pipeline is a fully automated system that:
1. **Collects** articles from RSS feeds
2. **Optimizes** images (web and mobile versions)
3. **Analyzes** articles using Deepseek AI
4. **Generates** JSON payloads for website
5. **Stores** results in database with detailed logging

The entire pipeline is orchestrated by `pipeline.py` which manages all phases and generates timestamped logs.

## Quick Start

```bash
# Complete pipeline (mine + images + deepseek + payloads + verify)
python3 pipeline.py --full --articles-per-seed 3

# Individual phases
python3 pipeline.py --mine                    # Mining only
python3 pipeline.py --images                  # Image optimization only
python3 pipeline.py --deepseek                # Deepseek processing only
python3 pipeline.py --payloads                # Generate website payloads only
python3 pipeline.py --verify                  # Verification only

# With options
python3 pipeline.py --full --articles-per-seed 3   # 3 articles per feed
python3 pipeline.py --full -v                       # Verbose output
python3 pipeline.py --full --dry-run                # Preview without changes
```

## Pipeline Architecture

```
┌─────────────────────────────────────┐
│    PHASE 1: MINING                  │
│  (mining/run_mining_cycle.py)       │
│  Collects articles from RSS feeds   │
│  ✓ 6 sources, 1-3 articles each     │
│  ✓ Auto-links images to articles    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    PHASE 2: IMAGE HANDLING          │
│  (tools/imgcompress.py)             │
│  Creates web and mobile versions    │
│  ✓ Optimizes all images             │
│  ✓ Updates database with paths      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    PHASE 3: DEEPSEEK PROCESSING     │
│  (deepseek/process_one_article.py)  │
│  + (deepseek/insert_from_response.py)
│  AI analysis and enrichment         │
│  ✓ API calls for all articles       │
│  ✓ Inserts responses into DB        │
│  ✓ Moves files to final location    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    PHASE 4: PAYLOAD GENERATION      │
│  Article: batch_generate_json_      │
│           payloads.py                │
│  Main:    mainpayload_generate.py   │
│  ✓ Article page JSONs (easy/mid/hi) │
│  ✓ Main page JSONs (13 files)       │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    PHASE 5: VERIFICATION            │
│  Final validation of results        │
│  ✓ Count articles, images, mobile   │
│  ✓ Report processing status         │
└─────────────────────────────────────┘
```

## Phase Details

### PHASE 1: MINING

**Script**: `mining/run_mining_cycle.py`

**What it does:**
- Calls `data_collector.py` to fetch articles from RSS feeds
- Downloads and stores article images
- **Auto-links images to articles** (image_id set in articles table)
- Validates content quality (2300-4500 chars)
- Filters out duplicates and inappropriate content

**Output:**
- Articles in database: `articles` table
- Images in database: `article_images` table  
- Image files on disk: `website/article_image/`

**Log file**: `log/phase_mining_YYYYMMDD_HHMMSS.log`

**Key stats logged:**
- Total articles collected
- Count by source (BBC Entertainment, BBC News, BBC Tennis, PBS NewsHour, Science Daily, TechRadar)
- Articles with images (should be 100%)

**Example output:**
```
→ Database now contains 18 articles
→   TechRadar: 3 article(s)
→   Science Daily: 3 article(s)
→   PBS NewsHour: 3 article(s)
→   BBC Tennis: 3 article(s)
→   BBC News: 3 article(s)
→   BBC Entertainment: 3 article(s)
→ Articles with images: 18/18
```

### PHASE 2: IMAGE HANDLING

**Script**: `tools/imgcompress.py`

**What it does:**
- Processes all article images
- Creates optimized web version (large)
- Creates optimized mobile version (small)
- Updates `article_images.small_location` in database

**Input:**
- Image files from `website/article_image/`

**Output:**
- Web and mobile optimized versions
- Database updated with `small_location` paths

**Log file**: `log/phase_image_handling_YYYYMMDD_HHMMSS.log`

**Key stats logged:**
- Number of images processed
- Optimization results

### PHASE 3: DEEPSEEK PROCESSING

**Scripts**: 
- `deepseek/process_one_article.py` (API calls)
- `deepseek/insert_from_response.py` (database insertion)

**What it does:**
1. Batch processes all unprocessed articles
2. Calls Deepseek API for each article with custom prompts
3. Generates analysis at 3 difficulty levels (easy, middle, high) + Chinese translation
4. Saves responses to JSON files
5. **Inserts responses into database** (new in this version!)
6. Moves response files to final location: `website/article_response/`
7. Updates `articles.deepseek_processed = 1`

**Database updates:**
- Inserts into `response` table (article_id, respons_file)
- Updates `articles` table:
  - `deepseek_processed = 1`
  - `processed_at = NOW()`

**File movement:**
- From: `deepseek/responses/article_XXXXX_response.json`
- To: `website/article_response/article_XXXXX_response.json`

**Log file**: `log/phase_deepseek_YYYYMMDD_HHMMSS.log`

**Key stats logged:**
- Unprocessed articles found
- API calls in progress
- Insertion results (inserted count, failed count)
- Final processed count in database

**Example output:**
```
→ Found 18 unprocessed article(s)
→ Processing 18 article(s) with Deepseek API...
→ Inserting Deepseek responses into database...
→ Insertion complete: 18 inserted, 0 failed
→ Total processed in database: 18 article(s)
```

### PHASE 4: VERIFICATION

**What it does:**
- Counts articles in database
- Counts images in database  
- Counts mobile versions created
- Counts deepseek processed articles
- Reports final status

**Log file**: Included in main pipeline results JSON

## Logging System

### Log Files Location
All logs are stored in `/Users/jidai/news/log/` directory

### Log File Types

1. **Phase logs** (timestamped):
   - `phase_mining_YYYYMMDD_HHMMSS.log`
   - `phase_image_handling_YYYYMMDD_HHMMSS.log`
   - `phase_deepseek_YYYYMMDD_HHMMSS.log`
   - `phase_article_payloads_YYYYMMDD_HHMMSS.log`
   - `phase_main_payloads_YYYYMMDD_HHMMSS.log`

2. **Pipeline results** (JSON):
   - `pipeline_results_YYYYMMDD_HHMMSS.json`

### Log Content

Each log file contains:
```
[2025-10-25T00:33:47.661115] Starting mining phase (articles per seed: 1)
[2025-10-25T00:33:50.123456] → Mining cycle complete
[2025-10-25T00:33:50.234567] Command: python3 /Users/jidai/news/mining/run_mining_cycle.py
[2025-10-25T00:33:55.345678] Exit code: 0
[2025-10-25T00:33:55.456789] STDOUT: [full output captured]
```

### Viewing Logs

```bash
# View latest mining log
tail -50 log/phase_mining_*.log

# View specific phase
cat log/phase_deepseek_*.log | grep "insertion"

# View pipeline summary
cat log/pipeline_results_*.json | jq .

# Watch deepseek progress (while running)
tail -f log/phase_deepseek_*.log
```

## Database Schema Changes

### Key Tables

**articles**
- `id` - Article ID (TEXT PRIMARY KEY)
- `title`, `source`, `url`, `content` - Article data
- `image_id` - **Link to article_images** (auto-set by mining phase!)
- `deepseek_processed` - Flag (0/1)
- `processed_at` - Timestamp when deepseek completed

**article_images**
- `image_id` - Auto-increment ID
- `article_id` - Reference to articles.id
- `image_name`, `original_url` - Original image info
- `local_location` - Path to web version
- `small_location` - Path to mobile version

**response**
- `response_id` - Auto-increment ID
- `article_id` - Reference to articles.id
- `respons_file` - Path to response JSON file

## Data Flow

```
RSS Feeds
    ↓
data_collector.py (mining phase)
    ↓
articles table + article_images table + image files
    ↓
imgcompress.py (image handling phase)
    ↓
Web + mobile versions created, small_location updated
    ↓
process_one_article.py (deepseek API)
    ↓
Response JSON files created
    ↓
insert_from_response.py (NEW! automatic insertion)
    ↓
response table populated + articles.deepseek_processed=1
    ↓
Response files moved to website/article_response/
```

## Important Fixes & Improvements

### Fix 1: Image Linking (Mining Phase)
**Before**: Images downloaded but articles not linked to images
**After**: `data_collector.py` now automatically sets `image_id` in articles table
**Result**: "Articles with images: 18/18" ✅

### Fix 2: Automated Response Insertion (Deepseek Phase)
**Before**: Deepseek responses saved but not inserted into database (manual step needed)
**After**: `insert_from_response.py` automatically called after API processing
**Result**: Full end-to-end pipeline without manual steps ✅

### Fix 3: Comprehensive Logging
**Before**: Limited visibility into what's happening
**After**: Every phase creates detailed timestamped logs with full output capture
**Result**: Easy debugging and progress tracking ✅

## Command Reference

```bash
# Full pipeline with default settings (2 articles per seed)
python3 pipeline.py --full

# Full pipeline with 1 article per seed (6 total articles)
python3 pipeline.py --full --articles-per-seed 1

# Full pipeline with 3 articles per seed (18 total)
python3 pipeline.py --full --articles-per-seed 3

# Verbose output
python3 pipeline.py --full -v

# Dry-run (preview without changes)
python3 pipeline.py --full --dry-run

# Individual phases only
python3 pipeline.py --mine
python3 pipeline.py --images
python3 pipeline.py --deepseek
python3 pipeline.py --verify

# Mining + images only (skip deepseek)
python3 pipeline.py --mine --images
```

## Troubleshooting

### Pipeline hangs
- Check logs in `log/phase_deepseek_*.log`
- Deepseek API calls can take 10-30 seconds per article
- Check network connectivity to api.deepseek.com

### Images not showing "with images"
- Ensure mining phase completed successfully
- Check if image_id is set: `sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE image_id IS NOT NULL;"`

### Deepseek responses not inserted
- Check `log/phase_deepseek_*.log` for errors
- Verify response files exist in `deepseek/responses/`
- Check database for response table entries

## Performance Notes

- Mining: ~3-5 seconds per article
- Image handling: ~1-2 seconds per image
- Deepseek API: ~10-30 seconds per article (network dependent)
- Full pipeline (18 articles): ~10-15 minutes

## Next Steps

Recommended optimizations:
1. Add parallel processing for image optimization
2. Add batch API calls to Deepseek (reduce API latency)
3. Add retry logic for failed API calls
4. Add progress bar for long operations
5. Make deepseek processing optional/skippable

