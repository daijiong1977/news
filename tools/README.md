# Tools Directory

This directory contains utility scripts for managing the news database and website files.

## Quick Start Guide

### **4-Tool Ecosystem for News Pipeline**

The tools directory provides four complementary utilities for complete article lifecycle management:

| Tool | Purpose | Scope | Mode |
|------|---------|-------|------|
| **reset_all.py** | ONE-COMMAND complete purge | All data + files | ✓ Dry-run safe |
| **datapurge.py** | Delete articles & metadata | Database only | Selective per filter |
| **pagepurge.py** | Delete webpage files | Files only | Independent, no DB |
| **imgcompress.py** | Generate web/mobile images | Image processing | In-place processing |

### **Common Workflows**

#### **1. Complete Fresh Start (RECOMMENDED)**
```bash
# ONE COMMAND: Reset everything (with preview)
python3 tools/reset_all.py

# Actually execute (CAUTION!)
python3 tools/reset_all.py --force

# Result: Clean database + deleted all files
# Ready to run: python3 pipeline.py --full
```

#### **2. Selective Purge (Database Only)**
```bash
# Delete specific date (keep files)
python3 tools/reset_all.py --db-only --force

# OR use datapurge for fine-grained control
python3 tools/datapurge.py --date 2025-10-24 --force
```

#### **3. Keep Database, Clean Files**
```bash
# Delete all website files but keep articles
python3 tools/reset_all.py --keep-db --force

# OR delete just specific files
python3 tools/pagepurge.py --date 2025-10-24 --force
```

#### **4. Quick Test Run**
```bash
# Step 1: Preview what will be deleted
python3 tools/reset_all.py

# Step 2: Actually purge
python3 tools/reset_all.py --force

# Step 3: Run pipeline on fresh data
python3 pipeline.py --test

# Step 4: Review results, analyze images
ls -lh website/article_image/
```

#### **5. Image Optimization (After Data Collection)**
```bash
# Generate web and mobile versions
python3 tools/imgcompress.py --auto --dir website/article_image/ --web --mobile

# Verify all images optimized
find website/article_image/ -type f | wc -l
```

#### **4. Complete Cleanup & Archive**
```bash
# Backup before cleanup
tar czf backups/archive_$(date +%Y%m%d_%H%M%S).tar.gz website/ articles.db

# Full purge
python3 tools/datapurge.py --all --force
python3 tools/pagepurge.py --all --force
```

---

## Included Tools

### 1. reset_all.py - ONE-COMMAND Complete Purge (NEW)

**Purpose**: Complete system reset - delete everything in one command with safe dry-run preview.

🎯 **USE THIS FOR FRESH STARTS** - Recommended for resetting the entire system before pipeline runs.

#### What Gets Deleted

```
✓ Database: All articles (18 tables, cascading deletes)
✓ Website Files: article_page/, article_image/, article_response/
✓ Deepseek Responses: deepseek/responses/*.json
✓ Mining Responses: mining/responses/*.json
✓ Log Results: Optionally clean log/ directory
```

#### Key Features

- **Safe by Default**: Always shows dry-run preview first
- **Flexible Purging**: Selective options (database-only, files-only, etc.)
- **Progress Reporting**: Shows exactly what will/was deleted
- **Atomic Operations**: Foreign key handling for data integrity
- **Fast**: Deletes all data in seconds

#### Usage Examples

```bash
# Preview (DRY-RUN): Shows what will be deleted, nothing is removed
python3 tools/reset_all.py

# Execute full purge: Delete everything (CAUTION!)
python3 tools/reset_all.py --force

# Database only (keep website files)
python3 tools/reset_all.py --db-only --force

# Website files only (keep database)
python3 tools/reset_all.py --files-only --force

# Everything except database
python3 tools/reset_all.py --keep-db --force

# Deepseek responses only
python3 tools/reset_all.py --deepseek-only --force

# Mining responses only
python3 tools/reset_all.py --mining-only --force

# Verbose output
python3 tools/reset_all.py --force -v
```

#### Purge Options

| Option | Effect |
|--------|--------|
| (none) | Full purge with dry-run preview |
| `--force` | Actually execute the purge |
| `--db-only` | Delete database records only |
| `--files-only` | Delete website files only |
| `--deepseek-only` | Delete deepseek responses only |
| `--mining-only` | Delete mining responses only |
| `--keep-db` | Delete everything except database |
| `-v, --verbose` | Detailed progress output |

#### Example Workflow: Complete Fresh Start

```bash
# Step 1: Preview what will be deleted
$ python3 tools/reset_all.py
⚠️  DRY RUN MODE (no data will be deleted)
📊 Summary:
  • Database: 41 records
  • Website files: 11 files
  • Deepseek responses: 6 files
  • Mining responses: 1 files

# Step 2: Review and confirm, then execute
$ python3 tools/reset_all.py --force
✅ PURGE COMPLETE
📊 Summary:
  • Database: 41 records deleted
  • Website files: 11 files deleted
  • Deepseek responses: 6 files deleted
  • Mining responses: 1 files deleted

# Step 3: Now ready for fresh pipeline run
$ python3 pipeline.py --full --articles-per-seed 5
```

#### Comparison: reset_all.py vs datapurge.py vs pagepurge.py

| Task | Tool | Command |
|------|------|---------|
| Complete reset | reset_all.py | `reset_all.py --force` |
| Delete specific date (DB only) | datapurge.py | `datapurge.py --date 2025-10-24 --force` |
| Delete specific date (files) | pagepurge.py | `pagepurge.py --date 2025-10-24 --force` |
| Keep database, clean everything else | reset_all.py | `reset_all.py --keep-db --force` |

---

### 2. datapurge.py - Database Purging Utility

**Purpose**: Remove articles and all related data from the database ONLY.

⚠️  **DATABASE ONLY** - This tool deletes database records only. It does NOT delete files in the website/ directory.

#### Supported Filters

- `--article-id <ID>` — Delete specific article (e.g., 2025102401)
- `--date <YYYY-MM-DD>` — Delete all articles from date
- `--week <YYYY-week-WW>` — Delete articles from ISO week (e.g., 2025-week-43)
- `--date-range <START> <END>` — Delete articles between dates
- `--before <YYYY-MM-DD>` — Delete all articles before date
- `--after <YYYY-MM-DD>` — Delete all articles after date

#### Data Purged (Database Records Only)

When deleting an article, the following database records are also removed:
- `article_images` — Article preview images (DB records only, files preserved)
- `keywords` — Extracted keywords and explanations
- `questions` — Generated quiz questions
- `choices` — Quiz answer choices
- `comments` — User comments
- `background_read` — Background reading material
- `article_analysis` — Analysis data
- `article_summaries` — Generated summaries
- `response` — Deepseek API responses (DB records only, files preserved)

#### Files Preserved

These files are **NOT** deleted by datapurge.py:
- ✓ `website/article_image/` — Article preview images (files on disk)
- ✓ `website/article_response/` — Article response JSON files
- ✓ `website/article_page/` — Article HTML pages
- ✓ `deepseek/responses/` — API response files
- ✓ `mining/responses/` — Mining response files

To delete these files, use `pagepurge.py` or manually clean up (see File Cleanup section).

#### Usage Examples

```bash
# Dry-run: See what would be deleted (NO deletion)
python3 tools/datapurge.py --article-id 2025102401
python3 tools/datapurge.py --date 2025-10-24
python3 tools/datapurge.py --week 2025-week-43

# Actually delete specific article (requires confirmation)
python3 tools/datapurge.py --article-id 2025102401 --force

# Delete all articles from a date (requires confirmation)
python3 tools/datapurge.py --date 2025-10-24 --force

# Delete articles from ISO week
python3 tools/datapurge.py --week 2025-week-42 --force

# Delete articles in date range
python3 tools/datapurge.py --date-range 2025-10-15 2025-10-20 --force

# Delete articles before cutoff date
python3 tools/datapurge.py --before 2025-10-01 --force

# Delete articles after date
python3 tools/datapurge.py --after 2025-10-20 --force

# Show preview without deleting
python3 tools/datapurge.py --date 2025-10-24 --preview
```

#### Options

- `--force` — Actually delete (default: dry-run, preview only)
- `--preview` — Show preview of articles to be deleted
- `-v, --verbose` — Verbose output with detailed deletion info
- `-h, --help` — Show help message

#### Safety Features

- ✓ **Dry-Run by Default** — Must use `--force` to actually delete
- ✓ **User Confirmation** — Requires "yes" response before deletion
- ✓ **Article Preview** — Shows title, source, date before deletion
- ✓ **Database Transactions** — Atomic operations, rolls back on error
- ✓ **Cascade Protection** — Automatically handles all related data
- ✓ **Error Handling** — Comprehensive error messages

#### Backup & Recovery

Always backup before purging:

```bash
# Backup database
cp articles.db articles.db.backup_$(date +%s).sqlite

# Restore from backup if needed
cp articles.db.backup_<timestamp>.sqlite articles.db
```

---

### 3. pagepurge.py - Webpage File Purging Utility

**Purpose**: Remove webpage files from website/ directory by article_id or date.

---

### 4. imgcompress.py - Image Compression Utility

**Purpose**: Optimize images to under 50KB for email newsletters.

Compresses JPG, PNG, and WebP images while maintaining visual quality. Perfect for reducing email attachment sizes and improving load times.

**Key Feature**: Parses article_id directly from filenames — does NOT require database access (works even after database purging).

#### How It Works

- Scans website/ directories for files named `article_<ID>_*`
- Extracts article_id from filename pattern
- Works with both old integer IDs (e.g., `article_1_`, `article_17_`) and semantic IDs (e.g., `article_2025102401_`)
- Deletes matching files from all website directories

#### Supported Filters

- `--article-id <ID>` — Delete files for specific article (e.g., 2025102401)
- `--date <YYYY-MM-DD>` — Delete files from articles on that date
- `--week <YYYY-week-WW>` — Delete files from articles in ISO week
- `--date-range <START> <END>` — Delete files from date range
- `--before <YYYY-MM-DD>` — Delete files from articles before date
- `--after <YYYY-MM-DD>` — Delete files from articles after date

#### Files Deleted From

When deleting by article_id, files are removed from:
- `website/article_page/` — Article HTML pages
- `website/article_image/` — Article preview images
- `website/article_response/` — Article response JSON files

#### Usage Examples

```bash
# Dry-run: See what would be deleted (NO deletion)
python3 tools/pagepurge.py --article-id 2025102401
python3 tools/pagepurge.py --date 2025-10-24
python3 tools/pagepurge.py --week 2025-week-43

# Actually delete files for specific article (requires confirmation)
python3 tools/pagepurge.py --article-id 2025102401 --force

# Delete all files from a date (requires confirmation)
python3 tools/pagepurge.py --date 2025-10-24 --force

# Delete files from ISO week
python3 tools/pagepurge.py --week 2025-week-42 --force

# Delete files in date range
python3 tools/pagepurge.py --date-range 2025-10-15 2025-10-20 --force

# Show preview without deleting
python3 tools/pagepurge.py --date 2025-10-24 --preview

# Verbose output showing each file
python3 tools/pagepurge.py --article-id 2025102401 -v --force
```

#### Options

- `--force` — Actually delete (default: dry-run, preview only)
- `--preview` — Show preview of files to be deleted
- `-v, --verbose` — Verbose output showing each file
- `-h, --help` — Show help message

#### Why Use pagepurge.py?

1. **Independent of Database** — Works even after database purging
2. **Filename Parsing** — No database queries needed
3. **Flexible ID Support** — Works with both integer and semantic article IDs
4. **Safe by Default** — Dry-run mode, requires confirmation

#### Workflow: Complete Purge

```bash
# Step 1: Purge database records
python3 tools/datapurge.py --date 2025-10-24 --force

# Step 2: Purge website files
python3 tools/pagepurge.py --date 2025-10-24 --force
```

---

### 4. imgcompress.py - Image Optimization Utility

**Purpose**: Generate web and mobile versions of images with automatic optimization.

Creates two versions of each image: a web-optimized version and a mobile-optimized WebP version. Perfect for responsive web design and reducing mobile data usage.

#### Workflow

**Version 1: Web Version**
- Resizes to fit within 1024×768 (preserves aspect ratio)
- Keeps original format (JPG stays JPG, PNG stays PNG, WebP stays WebP)
- No compression (just resizing)
- Keeps original filename
- Good for desktop/tablet web display

**Version 2: Mobile Version**
- Resizes to fit within 600×450 (preserves aspect ratio)
- Converts to WebP format (better compression)
- Compresses to <50KB via binary search on quality
- Creates new file with `_mobile.webp` suffix
- Updates `small_location` in database for email/mobile embedding
- Example: `article_1.jpg` → `article_1_mobile.webp`

#### Supported Formats

- JPG / JPEG → JPG (web) or WebP (mobile)
- PNG → PNG (web) or WebP (mobile)
- WebP → WebP (web and mobile)

#### Usage Examples

```bash
# Resize single image for web only (1024×768, keep format)
python3 tools/imgcompress.py --input image.jpg --web

# Create mobile version only (600×450, <50KB WebP)
python3 tools/imgcompress.py --input image.jpg --mobile

# Create both web and mobile versions for single image
python3 tools/imgcompress.py --input image.jpg --web --mobile

# Process all images in directory (auto-mode, skip processed, track progress)
python3 tools/imgcompress.py --dir website/article_image/ --auto --web --mobile

# Resume auto-processing from last checkpoint
python3 tools/imgcompress.py --dir website/article_image/ --auto --resume --web --mobile

# Create only mobile versions for directory (verbose output)
python3 tools/imgcompress.py --dir website/article_image/ --mobile -v

# Preview what would be done (no actual changes)
python3 tools/imgcompress.py --dir website/article_image/ --web --mobile --dry-run
python3 tools/imgcompress.py --dir website/article_image/ -v

```

#### Dimension Specifications

**Web Version (1024×768)**
- Aspect ratio preserved
- No upscaling (smaller images kept as-is)
- Suitable for: Desktop browsers, tablets, web pages
- Reduces bandwidth while maintaining visual quality

**Mobile Version (600×450, <50KB WebP)**
- Aspect ratio preserved
- No upscaling
- Compressed to under 50KB via quality reduction
- WebP format for better compression
- Suitable for: Email newsletters, mobile web, social media
- Automatic database integration for easy embedding

#### Auto-Mode Features

**Smart Processing Workflow**:
1. Scans all images in directory
2. Skips images that already have `_mobile` versions
3. Processes only original images (article_1.jpg, article_2.png, etc.)
4. **Automatically updates database** `article_images.small_location` with mobile image path
5. Saves checkpoint after each image processed
6. Can resume from checkpoint on next run

**Checkpoint Tracking**:
- Stores `.imgcompress_checkpoint.json` in workspace root
- Tracks last processed image filename
- Allows resuming if process is interrupted
- Includes timestamp and processing stats

**Database Integration**:
- When mobile versions are created, the tool automatically updates `article_images` table
- Column `small_location` stores the path to the mobile WebP
- Perfect for embedding in email templates and mobile web
- Use in templates: `<img src="{article.small_location}" />` for mobile version
- Example: `small_location = /path/to/article_1_mobile.webp`
- Only updates when processing images in `website/article_image/` directory

**Example Auto-Mode Workflow**:

```bash
# Initial run: create web and mobile versions
$ python3 tools/imgcompress.py --auto --dir website/article_image/ --web --mobile -v
[OK] Already processed: article_1_mobile.webp
Found 5 image file(s) to process

[1/5] Processing: article_1.jpg
  Web: article_1.jpg (45.4 KB)
    Already fits 972x547 within 1024x768
  Mobile: article_1.jpg → article_1_mobile.webp
    Resized: 972x547 → 600x336
    ✓ Mobile version: 38.5 KB (quality=85)

[2/5] Processing: article_2.png
  Web: article_2.png (120.0 KB)
    Resized: 1500x900 → 1024x614
  Mobile: article_2.png → article_2_mobile.webp
    Resized: 1500x900 → 600x360
    ✓ Mobile version: 45.2 KB (quality=80)

✓ Web versions: 0.2 MB total
✓ Mobile versions: 0.1 MB total
✓ Processed 2 file(s)

# Later: add new images, resume
$ python3 tools/imgcompress.py --auto --dir website/article_image/ --resume --web --mobile -v
Resuming from: article_2.png
Found 1 image file(s) to process

[1/1] Processing: article_3.jpg
  Web: article_3.jpg (98.0 KB)
    Resized: 2000x1200 → 1024x614
  Mobile: article_3.jpg → article_3_mobile.webp
    Resized: 2000x1200 → 600x360
    ✓ Mobile version: 42.1 KB (quality=85)

✓ Web versions: 0.1 MB total
✓ Mobile versions: 0.04 MB total
✓ Processed 1 file(s)
```

#### Options

- `--input FILE` — Single image file to process
- `--dir DIR` — Directory containing images
- `--web` — Generate web version (1024×768)
- `--mobile` — Generate mobile version (600×450, <50KB WebP)
- `--auto` — Auto-mode: skip processed, track progress
- `--resume` — Resume from last checkpoint (requires --auto)
- `--dry-run` — Preview without processing
- `-v, --verbose` — Detailed output showing dimensions and compression

#### File Outputs

After processing:
- **Original file**: Unchanged or resized for web (same name)
- **Mobile version**: Created with `_mobile.webp` suffix
- **Database**: `small_location` column updated with mobile path

Example:
```
Before: article_1.jpg (2000×1200, 150 KB)
After:  article_1.jpg (1024×614, 150 KB - resized in-place)
        article_1_mobile.webp (600×360, 38 KB - new file)

# Add to cron job to auto-compress new images daily
# (Add to crontab: 0 0 * * * cd /news && python3 tools/imgcompress.py --auto --dir website/article_image/ --resume)

# Or run manually when adding new articles
python3 tools/imgcompress.py --auto --dir website/article_image/ --resume -v
```

#### Real-World Example

```
Original images in website/article_image/:
- article_1_eb0787e930ba.jpg   93.8 KB
- article_17_b32ebf1d139f.jpg  97.7 KB
- article_18_a5a080e26276.webp 102.0 KB
Total: 293.5 KB

After compression:
- article_1_eb0787e930ba.jpg   45.4 KB  (-52%)
- article_17_b32ebf1d139f.jpg  45.9 KB  (-53%)
- article_18_a5a080e26276.jpg  45.6 KB  (-55%)
Total: 136.9 KB

Reduction: 157 KB saved (53% smaller) - Perfect for email!
```

#### Compression Optimization Notes

- **Quality Range**: 40-85 JPEG quality
- **Scaling Range**: 0.1x to 1.0x original size
- **Max Iterations**: 20 attempts to find optimal compression
- **Minimum Size**: 100x100 pixels
- **Minimum Target**: 10KB (configurable)

#### File Format Conversions

| Input | Output | Notes |
|-------|--------|-------|
| JPG | JPG | Optimized in-place |
| PNG | JPG | Converted for better compression |
| WebP | JPG | Converted for compatibility |

---

## File Cleanup

If you prefer manual file cleanup instead of using pagepurge.py:

#### Find Orphaned Images

```bash
# List all orphaned images (images without database records)
find website/article_image/ -name "article_*.jpg" -o -name "article_*.png" -o -name "article_*.webp" | while read file; do
  id=$(echo "$file" | grep -oE 'article_[0-9]+' | grep -oE '[0-9]+')
  sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE id='$id'" | grep -q "^0$" && echo "$file"
done
```

#### Find Orphaned Responses

```bash
# List all orphaned response files
find website/article_response/ -name "article_*_response.json" | while read file; do
  id=$(echo "$file" | grep -oE 'article_[0-9]+' | grep -oE '[0-9]+')
  sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE id='$id'" | grep -q "^0$" && echo "$file"
done
```

#### Manual File Deletion

```bash
# Delete specific article files
rm -f website/article_image/article_123_*
rm -f website/article_response/article_123_*
rm -f website/article_page/article_123*

# Delete all files from a date range
rm -f website/article_image/article_{1,2,3,4,5}_*
rm -f website/article_response/article_{1,2,3,4,5}_*
```

---

## Performance Notes

### datapurge.py Performance

- Small batch (< 10 articles): ~100ms
- Medium batch (10-100 articles): ~500ms to 2s
- Large batch (100+ articles): 5-30s depending on related records
- Cascade delete is atomic — all or nothing

### pagepurge.py Performance

- Small batch (< 100 files): ~50ms
- Medium batch (100-1000 files): ~200ms to 1s
- Large batch (1000+ files): 1-10s depending on storage speed
- File deletion is per-file, not atomic

### imgcompress.py Performance

- Single image: 1-3 seconds per image (depends on size/iterations)
- Batch processing: 50-200ms per image
- Binary search typically converges in 8-15 iterations
- Larger images (4000x3000+) may take 3-5 seconds
- PNG/WebP conversion adds ~500ms overhead

---

## Troubleshooting

### datapurge.py

**Issue**: "Database is locked" error
- Solution: Ensure no other processes are using the database
- Check: `lsof articles.db` to see open processes

**Issue**: "No articles found matching filter"
- Solution: Verify the date format (YYYY-MM-DD)
- Check: `python3 tools/datapurge.py --date 2025-10-24 --preview`

**Issue**: Deletion cancelled even though --force was used
- Solution: Type exactly "yes" (lowercase) at the confirmation prompt

### pagepurge.py

**Issue**: "No files found matching filter"
- Solution: Verify the article_id format
- Check: List files manually: `ls -la website/article_image/ | grep article_<ID>`

**Issue**: Files weren't deleted even with --force
- Solution: Verify file permissions: `ls -la website/article_image/`
- Check: Verify the files exist and article_id format is correct

**Issue**: Finding orphaned files after manual deletion
- Solution: Use the file cleanup scripts above
- Or run: `python3 tools/pagepurge.py --article-id <ID> --preview` to verify

### imgcompress.py

**Issue**: "No module named PIL"
- Solution: Install Pillow: `pip install Pillow`
- Check: `python3 -c "from PIL import Image"`

**Issue**: Compressed size still exceeds target
- Solution: Try smaller target size: `--target-size 40000`
- Or: Image may have too much visual content; consider --target-size 60000

**Issue**: Compression is too slow
- Solution: PNG/WebP conversion is slower; process JPG first
- Check: `--dry-run` to preview before processing

**Issue**: Image quality looks degraded
- Solution: This is expected at 50KB; quality/file-size tradeoff
- Option: Use larger target size: `--target-size 75000`

---

## Future Enhancements

- [ ] Add `--delete-files` option to datapurge.py for combined purging
- [ ] Add orphaned file detection utility
- [ ] Add archive mode for soft deletes (rename instead of delete)
- [ ] Add data export before delete feature
- [ ] Add parallel deletion for large batches
- [ ] Add S3 support for backup/archive
- [ ] Add batch image compression with parallel processing
- [ ] Add image watermarking option
- [ ] Add WebP native support (without conversion)
- [ ] Add GIF support for animated images

---

## Related Documentation

- `/dbinit/DB_INIT_README.md` — Database schema and article ID format
- `/mining/mining_latest.md` — Article collection and ID generation
- `/deepseek/deepseek_analyze_latest.md` — Article processing pipeline
- `/.gitignore` — Files excluded from git (backups/, unused/, etc.)
