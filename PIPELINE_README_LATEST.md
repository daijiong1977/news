# News Pipeline Documentation

**Latest Version** - Complete orchestration system for article mining, image optimization, and AI enrichment.

---

## Overview

The pipeline (`pipeline.py`) orchestrates a complete workflow for processing news articles:

1. **PURGE**: Clean database and website files for fresh start
2. **MINING**: Collect articles from RSS feeds
3. **IMAGE**: Generate web and mobile versions of images
4. **DEEPSEEK**: AI analysis and enrichment
5. **VERIFY**: Validate pipeline results

---

## Quick Start

### Default Run (2 articles per seed)
```bash
python3 pipeline.py --full
```

### Custom Articles Per Seed
```bash
python3 pipeline.py --full --articles-per-seed 5
```

### Preview Without Changes (Dry-Run)
```bash
python3 pipeline.py --full --dry-run
```

### Verbose Output
```bash
python3 pipeline.py --full -v
```

---

## Phase Details

### PHASE 1: PURGE

**Command**: `python3 pipeline.py --purge`

Cleans all data to start fresh:
- Database records deleted (articles, images, analysis, etc.)
- Website files deleted (article_image/, article_response/, article_page/)
- Deepseek responses cleaned
- Mining responses cleaned

**Safety**:
- Requires manual confirmation (prevents accidental deletion)
- Dry-run mode available for preview

**When to use**:
- Before each fresh pipeline run
- To test pipeline from scratch
- When cleaning up failed runs

---

### PHASE 2: MINING

**Command**: `python3 pipeline.py --mine`

Collects articles from configured RSS feeds.

**Key Parameter**: `--articles-per-seed N`
- Controls how many articles to collect per feed
- Default: 2
- Range: 1 or higher
- Example: `--articles-per-seed 5`

**What happens**:
1. Reads feed URLs from `feeds` table
2. Fetches articles from each feed
3. Stores articles in database with semantic ID (YYYYMMDD+counter)
4. Downloads preview images for each article
5. Saves images to `website/article_image/`

**Database**:
- Populates: `articles` table
- Populates: `article_images` table (with original images)

**Output**:
- Articles in database (semantic IDs like 2025102401)
- Original preview images in `website/article_image/`
- Status: articles ready for image processing

**Examples**:

```bash
# Default: 2 articles per seed
python3 pipeline.py --mine

# Collect 5 articles per feed
python3 pipeline.py --mine --articles-per-seed 5

# Collect 10 articles per feed (aggressive mining)
python3 pipeline.py --mine --articles-per-seed 10

# Quick test: 1 article per seed
python3 pipeline.py --mine --articles-per-seed 1
```

---

### PHASE 3: IMAGE HANDLING

**Command**: `python3 pipeline.py --images`

Generates web and mobile versions of all article images.

**Workflow**:
- **Web Version**: Resize to 1024×768 (keep original format, no compression)
- **Mobile Version**: Resize to 600×450, convert to WebP, compress to <50KB

**Features**:
- Auto-mode: Skips already-processed images
- Checkpoint tracking: Resumes from last image if interrupted
- Database auto-update: Stores mobile image path in `small_location`
- Aspect ratio preserved: Never upscales

**Output**:
- Original images resized (overwritten in-place)
- Mobile versions created (filename_mobile.webp)
- Database updated: `article_images.small_location` populated

**Example**:
```bash
# Generate all web and mobile versions
python3 pipeline.py --images

# Preview only
python3 pipeline.py --images --dry-run

# Verbose progress
python3 pipeline.py --images -v
```

**File Structure**:
```
Before:
  website/article_image/
    article_1.jpg (2000x1500, 150 KB)
    article_2.png (3000x2000, 200 KB)

After:
  website/article_image/
    article_1.jpg (1024x614, 80 KB) - resized
    article_1_mobile.webp (600x368, 35 KB) - new
    article_2.png (1024x683, 95 KB) - resized
    article_2_mobile.webp (600x400, 45 KB) - new
```

---

### PHASE 4: DEEPSEEK

**Command**: `python3 pipeline.py --deepseek`

AI-powered article analysis and enrichment using Deepseek API.

**Processing**:
- Analyzes article content
- Generates summaries (multiple difficulty levels)
- Extracts keywords and definitions
- Creates quiz questions and answers
- Generates background reading
- Provides analysis in multiple languages

**Features**:
- Batch processing with progress tracking
- Error handling and retry logic
- Automatic status tracking in database
- Incremental processing (skips already-processed articles)

**Database Updates**:
- `article_summaries`: Generated summaries
- `keywords`: Extracted keywords and explanations
- `questions`: Quiz questions with difficulty levels
- `choices`: Quiz answer options
- `comments`: Content commentary
- `background_read`: Background material
- `article_analysis`: Content analysis
- `response`: API response tracking

**Example**:
```bash
# Process all articles with Deepseek
python3 pipeline.py --deepseek

# Verbose output showing progress
python3 pipeline.py --deepseek -v

# Preview only
python3 pipeline.py --deepseek --dry-run
```

---

### PHASE 5: VERIFY

**Command**: `python3 pipeline.py --verify`

Validates that all pipeline phases completed successfully.

**Checks**:
- ✓ Article count in database
- ✓ Images collected
- ✓ Web versions resized
- ✓ Mobile versions created
- ✓ Database entries populated
- ✓ Deepseek processing status

**Output**: Health report with counts and status

---

## Complete Pipeline Workflows

### Workflow 1: Fresh Start (Default)
```bash
python3 pipeline.py --full
```
Executes: Purge → Mine (2 articles/seed) → Images → Deepseek → Verify

### Workflow 2: Custom Mining Volume
```bash
python3 pipeline.py --full --articles-per-seed 10
```
Executes: Purge → Mine (10 articles/seed) → Images → Deepseek → Verify

### Workflow 3: Testing (Small Dataset)
```bash
python3 pipeline.py --full --articles-per-seed 1
```
Executes: Purge → Mine (1 article/seed) → Images → Deepseek → Verify

Fastest pipeline for testing - minimal data to process

### Workflow 4: Aggressive Mining (Large Dataset)
```bash
python3 pipeline.py --full --articles-per-seed 20
```
Executes: Purge → Mine (20 articles/seed) → Images → Deepseek → Verify

Takes longer but collects comprehensive data

### Workflow 5: Preview Only (No Changes)
```bash
python3 pipeline.py --full --dry-run --articles-per-seed 5
```
Shows what would happen without making actual changes

### Workflow 6: Verbose Monitoring
```bash
python3 pipeline.py --full -v --articles-per-seed 5
```
Detailed output at every step for debugging

### Workflow 7: Manual Phase Control
```bash
# Only mining
python3 pipeline.py --mine --articles-per-seed 5

# Only image processing (after external mining)
python3 pipeline.py --images

# Only Deepseek (after external image processing)
python3 pipeline.py --deepseek

# Only verify results
python3 pipeline.py --verify
```

---

## Parameters Reference

### Global Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--full` | flag | - | Run complete pipeline (all phases) |
| `--purge` | flag | - | Run purge phase only |
| `--mine` | flag | - | Run mining phase only |
| `--images` | flag | - | Run image processing only |
| `--deepseek` | flag | - | Run Deepseek processing only |
| `--verify` | flag | - | Run verification only |
| `--articles-per-seed` | int | 2 | Articles to collect per feed |
| `--dry-run` | flag | - | Preview without making changes |
| `-v, --verbose` | flag | - | Detailed output all phases |

### Mining Phase Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--articles-per-seed` | int | 2 | Number of articles per feed seed |

Adjust this value based on:
- Feed size: Larger feeds support more articles
- Processing power: More articles = longer processing
- Storage: More articles = more database/disk space
- Testing: Use 1-2 for quick tests

**Recommended Values**:
- Testing: `1-2`
- Development: `3-5`
- Production: `5-20`
- Aggressive: `20+`

---

## Output & Results

### Pipeline Results File

Each run saves results to:
```
pipeline_results_YYYYMMDD_HHMMSS.json
```

Contains:
- Phase execution status
- Timing information
- Article counts
- Error details
- Verification results

**Example**:
```json
{
  "start_time": "2025-10-24T22:30:00",
  "phases": [
    {
      "phase": "purge",
      "start_time": "2025-10-24T22:30:05",
      "steps": [
        {
          "step": "database_purge",
          "success": true
        },
        {
          "step": "website_purge",
          "success": true
        }
      ]
    },
    {
      "phase": "mining",
      "articles_per_seed": 5,
      "articles_collected": 45
    }
  ],
  "dry_run": false,
  "verbose": false,
  "articles_per_seed": 5
}
```

---

## Common Scenarios

### Scenario 1: Quick Daily Update
```bash
# Mine 2 articles per feed, process images, enrich with Deepseek
python3 pipeline.py --mine --articles-per-seed 2
python3 pipeline.py --images
python3 pipeline.py --deepseek
```

### Scenario 2: Weekly Bulk Collection
```bash
# Collect 10 articles per feed, process all
python3 pipeline.py --full --articles-per-seed 10
```

### Scenario 3: Manual Testing
```bash
# Dry-run with verbose output
python3 pipeline.py --full --articles-per-seed 1 --dry-run -v

# If looks good, run for real
python3 pipeline.py --full --articles-per-seed 1 -v
```

### Scenario 4: Recover From Failure
```bash
# Check what failed
python3 pipeline.py --verify

# Re-run image processing
python3 pipeline.py --images

# Re-run Deepseek
python3 pipeline.py --deepseek

# Verify again
python3 pipeline.py --verify
```

### Scenario 5: Performance Testing
```bash
# Test with different mining volumes
python3 pipeline.py --full --articles-per-seed 1
python3 pipeline.py --full --articles-per-seed 5
python3 pipeline.py --full --articles-per-seed 10

# Compare results and timing
```

---

## Troubleshooting

### Mining Fails
**Check**:
- RSS feed URLs valid in `feeds` table
- Network connectivity
- API rate limits
- Disk space available

**Solution**:
```bash
# Verify feeds
sqlite3 articles.db "SELECT feed_name, feed_url FROM feeds WHERE enable=1;"

# Try again with fewer articles
python3 pipeline.py --mine --articles-per-seed 1
```

### Image Processing Fails
**Check**:
- Images in `website/article_image/`
- Disk space available
- Pillow library installed

**Solution**:
```bash
# Verify images exist
ls website/article_image/ | head -10

# Try again
python3 pipeline.py --images
```

### Deepseek Processing Fails
**Check**:
- API key configured in database
- API rate limits
- Network connectivity
- Articles exist in database

**Solution**:
```bash
# Check article count
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"

# Verify API key
sqlite3 articles.db "SELECT * FROM apikey WHERE name='deepseek';"

# Try again
python3 pipeline.py --deepseek
```

### Database Locked
**Symptom**: "database is locked" error

**Solution**:
```bash
# Close any other database connections
# Try again
python3 pipeline.py --full
```

---

## Best Practices

### 1. Always Backup Before Large Runs
```bash
# Backup database
cp articles.db articles.db.backup_$(date +%Y%m%d)

# Run pipeline
python3 pipeline.py --full --articles-per-seed 10
```

### 2. Use Dry-Run for Preview
```bash
# Always preview first
python3 pipeline.py --full --dry-run

# Then run for real
python3 pipeline.py --full
```

### 3. Monitor Progress
```bash
# Use verbose output for debugging
python3 pipeline.py --full -v > pipeline.log 2>&1

# Monitor log file
tail -f pipeline.log
```

### 4. Test Individual Phases
```bash
# Test mining
python3 pipeline.py --mine --articles-per-seed 1

# Verify mining worked
python3 pipeline.py --verify

# Then proceed to next phase
python3 pipeline.py --images
```

### 5. Adjust Articles Per Seed Based on Needs
```bash
# Development/testing: fewer articles
python3 pipeline.py --full --articles-per-seed 2

# Production: more articles
python3 pipeline.py --full --articles-per-seed 10
```

---

## Architecture

### Components

1. **pipeline.py** (Orchestrator)
   - Coordinates all phases
   - Manages parameters
   - Tracks results
   - Handles error recovery

2. **mining/run_mining_cycle.py** (Mining)
   - Collects articles from RSS feeds
   - Downloads images
   - Supports `--articles-per-seed` parameter

3. **tools/imgcompress.py** (Image)
   - Generates web versions (1024×768)
   - Generates mobile versions (600×450 WebP <50KB)
   - Updates database

4. **deepseek/process_one_article.py** (Deepseek)
   - AI analysis
   - Content enrichment
   - Database updates

### Data Flow

```
[Pipeline Start]
      ↓
[PURGE] ← Cleans database & files
      ↓
[MINE] ← Collects articles (--articles-per-seed)
      ↓
[IMAGES] ← Resizes & compresses
      ↓
[DEEPSEEK] ← AI enrichment
      ↓
[VERIFY] ← Health check
      ↓
[Results] ← JSON report saved
```

---

## Configuration

### Mining Configuration

Edit feed URLs and settings:
```bash
sqlite3 articles.db
> SELECT * FROM feeds;
> SELECT * FROM categories;
```

### Image Configuration

Edit in `tools/imgcompress.py`:
```python
WEB_MAX_DIMENSIONS = (1024, 768)      # Web size
MOBILE_MAX_DIMENSIONS = (600, 450)     # Mobile size
MOBILE_TARGET_SIZE = 50000             # 50KB limit
```

### Deepseek Configuration

Edit API settings:
```bash
sqlite3 articles.db
> SELECT * FROM apikey WHERE name='deepseek';
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| Latest | 2025-10-24 | Added `--articles-per-seed` parameter for mining control |
| v1.0 | 2025-10-24 | Initial pipeline orchestration |

---

## Support

For issues or questions:

1. Check `PIPELINE_CHECKLIST.md` for prerequisites
2. Review logs in `pipeline_results_*.json`
3. Check individual tool documentation in `tools/README.md`
4. Review database schema in `dbinit/init_schema.md`

---

**Last Updated**: October 24, 2025
