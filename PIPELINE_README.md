# News Pipeline - Complete Guide

The **pipeline.py** orchestrates the complete news data workflow from RSS feed collection to AI enrichment.

## Quick Start

### Full Pipeline (Clean + Mine + Images + Deepseek)
```bash
# Test run (preview without changes)
python3 pipeline.py --full --dry-run

# Actual execution
python3 pipeline.py --full

# With verbose output
python3 pipeline.py --full -v
```

### Individual Phases
```bash
# Just purge everything
python3 pipeline.py --purge

# Just mining
python3 pipeline.py --mine

# Just image optimization
python3 pipeline.py --images

# Just Deepseek processing
python3 pipeline.py --deepseek

# Just verification
python3 pipeline.py --verify
```

---

## Pipeline Architecture

### Phase 1: PURGE (Optional - Use Before Fresh Run)
**Purpose**: Clean slate for testing

Removes:
- ✓ All database records (articles, images, summaries, etc.)
- ✓ All website files (article_image/, article_page/, article_response/)

Uses: `tools/datapurge.py` + `tools/pagepurge.py`

```bash
python3 pipeline.py --purge
```

**When to use**:
- Before testing with fresh data
- Resetting after failed run
- Cleaning up before deployment

---

### Phase 2: MINING
**Purpose**: Collect articles from configured RSS feeds

Workflow:
1. Reads RSS feed URLs from database
2. Fetches articles from each feed
3. Parses content and metadata
4. Stores in `articles` table
5. Downloads and stores preview images in `website/article_image/`

Uses: `mining/run_mining_cycle.py`

```bash
python3 pipeline.py --mine
```

**Output**:
- New records in `articles` table
- Preview images in `website/article_image/article_*.jpg`
- Database status: `deepseek_processed = 0` (ready for processing)

**Configuration**: Update RSS feeds in database
```bash
# Add/edit feeds before running mining
sqlite3 articles.db
sqlite> UPDATE feeds SET enable = 1 WHERE feed_name = 'BBC';
```

---

### Phase 3: IMAGE HANDLING
**Purpose**: Generate optimized web and mobile versions

Workflow:
1. Scans `website/article_image/` for original images
2. **Web version**: Resizes to 1024×768, keeps original format
3. **Mobile version**: Creates `_mobile.webp`, resizes to 600×450, compresses to <50KB
4. Updates database `article_images.small_location` with mobile path

Uses: `tools/imgcompress.py`

```bash
python3 pipeline.py --images
```

**Output**:
- Original images resized in-place
- Mobile versions created: `article_1.jpg` → `article_1_mobile.webp`
- Database updated with mobile paths for email/responsive display

**Features**:
- Auto-mode: Skips already-processed images
- Checkpoint tracking: Can resume interrupted runs
- WebP compression: 50-70% size reduction

**Example results**:
```
Before: article_1.jpg (2000×1500, 150 KB)
After:  
  article_1.jpg (1024×768, 80 KB) - web version
  article_1_mobile.webp (600×450, 15 KB) - mobile version
```

---

### Phase 4: DEEPSEEK
**Purpose**: AI analysis and enrichment

Workflow:
1. Identifies unprocessed articles (`deepseek_processed = 0`)
2. For each article:
   - Calls Deepseek API with content
   - Generates summary, keywords, questions
   - Stores results in database
3. Updates `deepseek_processed = 1`

Uses: `deepseek/process_one_article.py`

```bash
# Manual processing for now
python3 deepseek/process_one_article.py [article_id]

# Or use pipeline to queue
python3 pipeline.py --deepseek
```

**Database updates**:
- `article_summaries` - AI-generated summaries by difficulty level
- `keywords` - Extracted keywords with explanations
- `questions` - Generated quiz questions
- `choices` - Multiple choice answers
- `articles.deepseek_processed = 1`

---

### Phase 5: VERIFICATION
**Purpose**: Check pipeline execution results

Queries:
- Total articles in database
- Total images collected
- Mobile versions created (`small_location` populated)
- Articles processed by Deepseek

```bash
python3 pipeline.py --verify
```

**Example output**:
```
Articles in database: 25
Images in database: 24
Mobile versions (small_location): 18
Articles processed by Deepseek: 15
```

---

## Common Workflows

### 1. Fresh Start (Complete Reset)
```bash
# Full purge and reload
python3 pipeline.py --full

# Components:
# 1. Clean database and files
# 2. Mine new articles
# 3. Optimize images
# 4. Queue Deepseek processing
```

### 2. Test Before Production
```bash
# Preview without changes
python3 pipeline.py --full --dry-run -v

# Review the output, then run for real
python3 pipeline.py --full
```

### 3. Add New Articles Only
```bash
# Skip purge, just mine new articles
python3 pipeline.py --mine

# Then optimize images
python3 pipeline.py --images

# Note: Deepseek must be run separately per article
```

### 4. Update Images for Existing Articles
```bash
# Skip purge and mining, just optimize images
python3 pipeline.py --images -v

# Check results
python3 pipeline.py --verify
```

### 5. Batch Deepseek Processing
```bash
# Find unprocessed articles
sqlite3 articles.db "SELECT id, title FROM articles WHERE deepseek_processed = 0"

# Process individually
for id in article_1 article_2 article_3; do
  python3 deepseek/process_one_article.py $id
done

# Or create batch script
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('articles.db')
cur = conn.cursor()
cur.execute("SELECT id FROM articles WHERE deepseek_processed = 0")
for (article_id,) in cur:
    print(f"Processing {article_id}...")
    # Call deepseek API here
conn.close()
EOF
```

---

## Tools Overview

| Tool | Purpose | Type | Scope |
|------|---------|------|-------|
| **datapurge.py** | Delete articles & metadata | Database | Atomic, cascade |
| **pagepurge.py** | Delete webpage files | Files | Independent |
| **imgcompress.py** | Web + mobile images | Processing | Auto with checkpoints |

See `/tools/README.md` for detailed tool documentation.

---

## Database Schema Integration

### Key Tables Updated by Pipeline

**articles**
- `id` - Semantic article ID (YYYYMMDD + counter)
- `title, content` - Article text
- `deepseek_processed` - 0 = pending, 1 = done
- `deepseek_failed` - Error count if processing fails

**article_images**
- `article_id, image_name` - Which article, which image
- `local_location` - Original image path
- `small_location` - Mobile optimized version (set by imgcompress)

**article_summaries**
- Generated by Deepseek API
- Multiple summaries per article (one per difficulty level)

**keywords, questions, choices, comments**
- Generated by Deepseek enrichment

---

## Error Handling

### If Phase Fails

**Database Purge Fails**
```bash
# Check database
sqlite3 articles.db ".schema"

# Verify file permissions
ls -l articles.db

# Try manual purge
python3 tools/datapurge.py --all --force -v
```

**Mining Fails**
```bash
# Check RSS feed URLs
sqlite3 articles.db "SELECT * FROM feeds WHERE enable = 1"

# Test mining directly
python3 mining/run_mining_cycle.py -v

# Check network/firewall
curl -I https://feeds.example.com/rss
```

**Image Processing Fails**
```bash
# Check image directory
ls -la website/article_image/

# Test imgcompress directly
python3 tools/imgcompress.py --input website/article_image/article_1.jpg --web --mobile -v

# Check disk space
df -h
```

**Deepseek API Fails**
```bash
# Check API key
sqlite3 articles.db "SELECT * FROM apikey WHERE name = 'deepseek'"

# Test Deepseek directly
python3 deepseek/process_one_article.py [article_id] -v

# Check API rate limits, account status
```

---

## Output & Results

### Pipeline Results File
After each run, a JSON results file is saved:
```
pipeline_results_20251024_222606.json
```

Contains:
- Start/end times
- All phases executed
- Success/failure for each step
- Counts (articles, images, processed)
- Any errors or warnings

### View Results
```bash
# Last run
cat pipeline_results_*.json | tail -1 | python3 -m json.tool

# Check specific phase
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1"
```

---

## Performance Tips

### For Large Article Batches
1. **Mining**: Runs in background, depends on feed response time
2. **Images**: Parallelizable but does one at a time (optimize if slow)
3. **Deepseek**: Most time-consuming - use batch processing

### Speed Up Image Processing
```bash
# Run on existing images only (skip check)
python3 tools/imgcompress.py --dir website/article_image/ --mobile --auto

# Verbose to see progress
python3 tools/imgcompress.py --dir website/article_image/ --mobile --auto -v
```

### Batch Deepseek Processing
Create a batch file `batch_deepseek.py`:
```python
import sqlite3
import subprocess
from pathlib import Path

conn = sqlite3.connect('articles.db')
cur = conn.cursor()
cur.execute("SELECT id FROM articles WHERE deepseek_processed = 0")

for (article_id,) in cur:
    print(f"\n{'='*60}")
    print(f"Processing: {article_id}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        ['python3', 'deepseek/process_one_article.py', article_id],
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"Failed: {article_id}")

conn.close()
```

Then run:
```bash
python3 batch_deepseek.py
```

---

## Troubleshooting

### Database Locked
```bash
# Check for running processes
lsof articles.db

# Kill if stuck
pkill -f "python3.*articles.db"

# Verify integrity
sqlite3 articles.db "PRAGMA integrity_check"
```

### Disk Space Issues
```bash
# Check available space
df -h

# Estimated size
du -sh website/ deepseek/ mining/

# Archive old data
tar czf backups/archive_$(date +%Y%m%d).tar.gz website/
```

### Memory Issues (Large Batches)
- Process in smaller batches: `--date-range 2025-10-01 2025-10-07`
- Increase swap: `fallocate -l 2G /swapfile`
- Use machine with more RAM for production

---

## Production Deployment

### Recommended Schedule (Cron)

```bash
# Daily mining at 2 AM
0 2 * * * cd /path/to/news && python3 pipeline.py --mine >> logs/mining.log 2>&1

# Daily image optimization at 3 AM
0 3 * * * cd /path/to/news && python3 pipeline.py --images >> logs/images.log 2>&1

# Weekly Deepseek batch at Sunday midnight
0 0 * * 0 cd /path/to/news && python3 batch_deepseek.py >> logs/deepseek.log 2>&1

# Weekly verification (email results)
0 4 * * 0 cd /path/to/news && python3 pipeline.py --verify >> logs/verify.log 2>&1
```

### Environment Variables
```bash
# Set API keys
export DEEPSEEK_API_KEY="sk-..."
export DATABASE_URL="sqlite:///articles.db"

# Run pipeline
python3 pipeline.py --full
```

---

## Next Steps

1. **Test pipeline**: `python3 pipeline.py --full --dry-run`
2. **Run mining**: `python3 pipeline.py --mine`
3. **Optimize images**: `python3 pipeline.py --images -v`
4. **Verify results**: `python3 pipeline.py --verify`
5. **Process with Deepseek**: `python3 deepseek/process_one_article.py [id]`

For detailed tool documentation, see `/tools/README.md`
