# News Pipeline - Complete Documentation (Latest)

**Version**: October 24, 2025  
**Status**: Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Pipeline Overview](#pipeline-overview)
3. [Phase Details](#phase-details)
4. [Command Reference](#command-reference)
5. [Parameters](#parameters)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)
8. [Architecture](#architecture)

---

## Quick Start

### Full Pipeline (Default)
```bash
cd /Users/jidai/news
python3 pipeline.py --full
```

### With Custom Mining Volume
```bash
# 5 articles per feed
python3 pipeline.py --full --articles-per-seed 5

# 10 articles per feed
python3 pipeline.py --full --articles-per-seed 10
```

### Preview (Dry-Run)
```bash
python3 pipeline.py --full --dry-run -v
```

---

## Pipeline Overview

The pipeline orchestrates a complete workflow:

```
┌─────────────────────────────────────────────────────────┐
│                   PIPELINE.PY                           │
├─────────────────────────────────────────────────────────┤
│ Phase 1: PURGE        │ Clean database & files          │
│ Phase 2: MINING       │ Collect from RSS feeds          │
│ Phase 3: IMAGE        │ Generate web & mobile versions  │
│ Phase 4: DEEPSEEK     │ AI enrichment & analysis        │
│ Phase 5: VERIFY       │ Validate results                │
└─────────────────────────────────────────────────────────┘
```

### Key Feature: `--articles-per-seed`

Controls mining volume (default: 2):
- `1` - Quick test
- `2` - Standard (default)
- `5` - Production
- `10+` - Aggressive collection

---

## Phase Details

### PHASE 1: PURGE

**Command**: `python3 pipeline.py --purge`

Cleans all data for fresh start:
- ✓ Database purge (articles, images, analysis)
- ✓ Website files purge (article_image/, article_page/, article_response/)
- ✓ Deepseek responses cleaned
- ✓ Mining responses cleaned

**Tools Used**:
- `tools/datapurge.py` - Database purging
- `tools/pagepurge.py` - File purging

**Safety**:
- Requires manual confirmation
- Dry-run mode available

---

### PHASE 2: MINING

**Command**: `python3 pipeline.py --mine`

Collects articles from configured RSS feeds.

**Key Parameter**: `--articles-per-seed N`
- Default: 2
- Controls articles per feed
- Example: `python3 pipeline.py --mine --articles-per-seed 5`

**What Happens**:
1. Reads feed URLs from `feeds` table
2. Fetches articles from each feed
3. Creates semantic article IDs (YYYYMMDD+counter)
4. Stores in `articles` table
5. Downloads preview images
6. Saves to `website/article_image/`

**Database Updates**:
- Populates: `articles` table
- Populates: `article_images` table

**Output**:
- Articles with semantic IDs (2025102401, etc.)
- Original preview images
- Ready for image processing

---

### PHASE 3: IMAGE HANDLING

**Command**: `python3 pipeline.py --images`

Generates web and mobile versions.

**Two Versions**:

| Aspect | Web | Mobile |
|--------|-----|--------|
| Dimensions | 1024×768 | 600×450 |
| Format | Original | WebP |
| Compression | None | <50KB |
| Filename | Original | `_mobile.webp` |
| DB Column | `local_location` | `small_location` |

**Features**:
- Auto-mode: Skips processed
- Checkpoint tracking: Resumable
- Aspect ratio preserved: Never upscales
- Database auto-update

**Output**:
- Web versions (resized, original format)
- Mobile versions (600×450 WebP, <50KB)
- Database `small_location` populated

**Example**:
```
Before: article_1.jpg (2000×1500, 150 KB)
After:
  - article_1.jpg (1024×614, 80 KB) resized
  - article_1_mobile.webp (600×368, 35 KB) new
```

---

### PHASE 4: DEEPSEEK

**Command**: `python3 pipeline.py --deepseek`

AI-powered article enrichment.

**Processing**:
- Content analysis
- Multi-level summaries (difficulty levels)
- Keyword extraction with explanations
- Quiz generation with answers
- Background reading materials
- Multi-language analysis

**Database Updates**:
- `article_summaries` - Generated summaries
- `keywords` - Extracted keywords
- `questions` - Quiz questions
- `choices` - Answer options
- `comments` - Content commentary
- `background_read` - Background material
- `article_analysis` - Analysis data
- `response` - API response tracking

**Status Tracking**:
- `deepseek_processed` - Completion flag
- `deepseek_in_progress` - Current status
- `deepseek_failed` - Failure count
- `deepseek_last_error` - Error details

---

### PHASE 5: VERIFY

**Command**: `python3 pipeline.py --verify`

Validates pipeline results.

**Checks**:
- ✓ Article count
- ✓ Images collected
- ✓ Web versions resized
- ✓ Mobile versions created
- ✓ Database entries
- ✓ Deepseek processing status

**Output**: Health report with counts

---

## Command Reference

### Full Pipeline
```bash
# Standard run (2 articles per seed)
python3 pipeline.py --full

# Custom mining volume
python3 pipeline.py --full --articles-per-seed 5

# Dry-run preview
python3 pipeline.py --full --dry-run

# Verbose output
python3 pipeline.py --full -v

# Combined
python3 pipeline.py --full --articles-per-seed 10 --dry-run -v
```

### Individual Phases
```bash
# Purge only
python3 pipeline.py --purge

# Mining only
python3 pipeline.py --mine --articles-per-seed 5

# Image only
python3 pipeline.py --images

# Deepseek only
python3 pipeline.py --deepseek

# Verify only
python3 pipeline.py --verify
```

---

## Parameters

### Global Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--full` | flag | - | Complete pipeline |
| `--purge` | flag | - | Purge phase only |
| `--mine` | flag | - | Mining phase only |
| `--images` | flag | - | Image phase only |
| `--deepseek` | flag | - | Deepseek phase only |
| `--verify` | flag | - | Verification only |
| `--articles-per-seed` | int | 2 | Articles per feed |
| `--dry-run` | flag | - | Preview mode |
| `-v, --verbose` | flag | - | Detailed output |

### Mining Parameter: `--articles-per-seed`

**Values**:
- `1` - One article per feed (quick test, <1 min)
- `2` - Two articles per feed (default, ~2 min)
- `5` - Five articles per feed (production, ~5 min)
- `10+` - Ten or more articles (aggressive, 10+ min)

**Recommendation by Use Case**:

| Use Case | Value | Time | Data Size |
|----------|-------|------|-----------|
| Testing | 1 | <1 min | Minimal |
| Development | 2-3 | 1-3 min | Small |
| Production | 5-10 | 5-10 min | Medium |
| Aggressive | 15-20 | 15-20 min | Large |

---

## Common Workflows

### Workflow 1: Quick Test (1 minute)
```bash
python3 pipeline.py --full --articles-per-seed 1
```

### Workflow 2: Daily Update (Default)
```bash
python3 pipeline.py --full
```

### Workflow 3: Weekly Bulk Collection
```bash
python3 pipeline.py --full --articles-per-seed 10
```

### Workflow 4: Manual Phase Control
```bash
# Step 1: Mine only
python3 pipeline.py --mine --articles-per-seed 5

# Step 2: Process images
python3 pipeline.py --images -v

# Step 3: Run Deepseek
python3 pipeline.py --deepseek

# Step 4: Verify
python3 pipeline.py --verify
```

### Workflow 5: Dry-Run Testing
```bash
# Preview everything
python3 pipeline.py --full --dry-run -v

# If looks good, run for real
python3 pipeline.py --full -v
```

### Workflow 6: Error Recovery
```bash
# Check status
python3 pipeline.py --verify

# Re-run failed phase
python3 pipeline.py --images
python3 pipeline.py --deepseek

# Verify again
python3 pipeline.py --verify
```

---

## Troubleshooting

### Mining Fails

**Check**:
```bash
# Verify feeds configured
sqlite3 articles.db "SELECT feed_name, feed_url FROM feeds WHERE enable=1;"

# Check network
ping 8.8.8.8
```

**Solution**:
```bash
# Try with fewer articles
python3 pipeline.py --mine --articles-per-seed 1
```

### Image Processing Fails

**Check**:
```bash
# Verify images exist
ls website/article_image/ | wc -l

# Check disk space
df -h
```

**Solution**:
```bash
# Re-run image phase
python3 pipeline.py --images -v
```

### Deepseek Processing Fails

**Check**:
```bash
# Verify API key
sqlite3 articles.db "SELECT * FROM apikey WHERE name='deepseek';"

# Check article count
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
```

**Solution**:
```bash
# Update API key if needed
sqlite3 articles.db "UPDATE apikey SET value='your_key' WHERE name='deepseek';"

# Re-run Deepseek
python3 pipeline.py --deepseek
```

### Database Locked

**Solution**:
```bash
# Close any other connections, then try again
python3 pipeline.py --full
```

---

## Architecture

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `pipeline.py` | Orchestration | `/Users/jidai/news/` |
| `run_mining_cycle.py` | Article collection | `mining/` |
| `imgcompress.py` | Image optimization | `tools/` |
| `process_one_article.py` | Deepseek API calls | `deepseek/` |
| `datapurge.py` | Database cleanup | `tools/` |
| `pagepurge.py` | File cleanup | `tools/` |

### Data Flow

```
[RSS Feeds]
    ↓
[mining/run_mining_cycle.py]
    ↓
[articles.db: articles + article_images]
    ↓
[tools/imgcompress.py]
    ↓
[website/article_image/ (web + mobile)]
    ↓
[deepseek/process_one_article.py]
    ↓
[articles.db: enriched with summaries, keywords, Q&A]
```

### Database Schema (Key Tables)

**articles**
```
id (TEXT) - Semantic ID: YYYYMMDD+counter
title, content, source, url
deepseek_processed (BOOL)
```

**article_images**
```
article_id (TEXT)
image_name (TEXT)
local_location (TEXT) - Web version path
small_location (TEXT) - Mobile version path
```

### Output Files

**After Each Run**:
- `articles.db` - Updated database (synced to git)
- `website/article_image/` - Resized images (synced to git)
- `log/pipeline_results_YYYYMMDD_HHMMSS.json` - Execution log (not synced to git)
- `log/*.txt`, `log/*.log` - Intermediate logs and reports (not synced to git)

See [log/README.md](log/README.md) for details on intermediate files.

---

## Results & Monitoring

### Check Pipeline Results

```bash
# View last results (in log directory)
cat log/pipeline_results_*.json | jq .

# Article count
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"

# Image count
sqlite3 articles.db "SELECT COUNT(*) FROM article_images;"

# Mobile versions
sqlite3 articles.db "SELECT COUNT(*) FROM article_images WHERE small_location IS NOT NULL;"

# Deepseek progress
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"
```

### Monitoring Verbose Output

```bash
# Save output to log directory
python3 pipeline.py --full -v > log/pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1

# Monitor in real-time
tail -f log/pipeline_*.log
```

---

## Best Practices

1. **Always Backup**
   ```bash
   cp articles.db articles.db.backup_$(date +%Y%m%d)
   ```

2. **Preview First**
   ```bash
   python3 pipeline.py --full --dry-run -v
   ```

3. **Start Small**
   ```bash
   python3 pipeline.py --full --articles-per-seed 1
   ```

4. **Monitor Progress**
   ```bash
   python3 pipeline.py --full -v
   ```

5. **Verify Results**
   ```bash
   python3 pipeline.py --verify
   ```

---

## Tools Documentation

For detailed tool usage, see:
- **Image Tool**: `tools/README.md`
- **Database Schema**: `dbinit/init_schema.md`
- **Quick Reference**: `PIPELINE_QUICK_REFERENCE.md`

---

## Summary

| Phase | Command | Purpose | Output |
|-------|---------|---------|--------|
| Purge | `--purge` | Clean data | Fresh database |
| Mining | `--mine` | Collect articles | Database + images |
| Image | `--images` | Resize + compress | Web + mobile versions |
| Deepseek | `--deepseek` | AI enrichment | Analysis data |
| Verify | `--verify` | Check status | Health report |

**Default Full Pipeline**: `python3 pipeline.py --full`

---

**Last Updated**: October 24, 2025  
**Maintained by**: Development Team
