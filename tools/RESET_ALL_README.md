# RESET_ALL Tool - Complete System Reset

## Overview

Comprehensive cleanup tool that removes all generated files and resets the pipeline to initial state.

**One-liner:** Wipe all generated content and start fresh (⚠️ destructive operation).

---

## Purpose & Use Cases

### Primary Use
- Fresh start for pipeline
- Complete cleanup before re-running
- Remove corrupted or problematic data
- Full database reset
- Clear cache and temporary files

### When to Use
- Starting completely over
- After major debugging
- To fix data integrity issues
- Before large-scale re-processing
- When you need a clean slate

### When NOT to Use
- During active pipeline run
- If you want to keep response files
- For incremental updates
- If you only need to remove some files

---

## ⚠️ DESTRUCTIVE WARNING

**This tool permanently deletes data:**
- ❌ All response files
- ❌ All processed articles
- ❌ Database is reset
- ❌ Generated images and pages
- ❌ Processing history

**No undo after execution!**

---

## Requirements

- Python 3.6+
- Write permissions to:
  - `/var/www/news/articles.db`
  - `/var/www/news/website/`
  - `/var/www/news/deepseek/responses/`
  - Other generated directories

---

## Installation

No installation needed. Tool is part of the tools directory.

---

## Usage

### Basic Syntax

```bash
python3 tools/reset_all.py --force
```

**`--force` flag is REQUIRED** to prevent accidental execution.

### Options

| Flag | Purpose | Required |
|------|---------|----------|
| `--force` | Confirm deletion (safety check) | YES |
| `--help` | Show help message | NO |

### Examples

#### Example 1: Confirm Execution
```bash
$ python3 tools/reset_all.py --force

🧹 RESET ALL - Complete System Cleanup
=========================================

⚠️  WARNING: This will DELETE all:
   - Response files
   - Processed articles
   - Generated images
   - Database content
   - Deepseek responses

📁 Directories to clean:
   ✓ website/article_image
   ✓ website/article_response
   ✓ website/responses
   ✓ deepseek/responses
   ✓ responses

🔄 Cleaning...
   ✓ Cleaned: website/article_image (0 files)
   ✓ Cleaned: website/article_response (0 files)
   ✓ Cleaned: website/responses (8 files removed)
   ✓ Cleaned: deepseek/responses (0 files)
   ✓ Cleaned: responses (0 files)

💾 Resetting database...
   ✓ Database reset to initial state
   ✓ Schema verified

✅ Complete System Reset Done!
   Ready for fresh pipeline run
```

#### Example 2: Missing --force Flag
```bash
$ python3 tools/reset_all.py

❌ ERROR: --force flag is required
   This prevents accidental data deletion.
   
   Run with: python3 tools/reset_all.py --force
```

---

## What Gets Deleted

### Directories Cleaned

| Directory | Contents | Impact |
|-----------|----------|--------|
| `website/article_image/` | Downloaded images | 🔴 Regenerated in next run |
| `website/article_response/` | Old response format | 🔴 Not recreated |
| `website/responses/` | Deepseek responses | 🔴 Will be regenerated |
| `deepseek/responses/` | Legacy responses | 🔴 Not used anymore |
| `responses/` | Archive responses | 🔴 Lost |

### Database Reset

**All tables cleared:**
- `articles` - Emptied but schema preserved
- `api_keys` - Reset to defaults
- `response` - Emptied

**On completion:**
- Schema is verified intact
- Database is ready for fresh data

---

## Output Explanation

### File Cleanup Section
```
🔄 Cleaning...
   ✓ Cleaned: website/article_image (X files removed)
```
- Shows each directory processed
- Reports number of files deleted
- Confirms successful deletion

### Database Reset Section
```
💾 Resetting database...
   ✓ Database reset to initial state
   ✓ Schema verified
```
- Backs up existing database (if possible)
- Clears all content
- Verifies schema integrity

---

## Error Handling

### Possible Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing --force flag` | Safety check | Add `--force` to command |
| `Permission denied` | Insufficient permissions | Use `sudo` or fix directory ownership |
| `Database locked` | Pipeline running | Stop pipeline first |
| `Directory not found` | Path issue | Check directory structure |

### Handling Errors

```bash
# If permission denied:
sudo python3 tools/reset_all.py --force

# If database locked:
# Stop the pipeline first, then retry:
pkill -f "python3 pipeline.py"
python3 tools/reset_all.py --force

# Check permissions:
ls -la /var/www/news/
```

---

## Before & After

### Before Running reset_all.py
```
articles.db: 33 articles (8 processed)
website/responses/: 8 response files
website/article_image/: 16 image files
Processing Status: Partially complete
```

### After Running reset_all.py
```
articles.db: 0 articles (0 processed)
website/responses/: 0 files
website/article_image/: 0 files
Processing Status: Ready for fresh start
```

---

## Safety Features

### Protected Against Accidental Execution
1. ✅ Requires `--force` flag
2. ✅ Shows warning before proceeding
3. ✅ Lists what will be deleted
4. ✅ Asks for confirmation (planned)

### Data Preservation
- ✅ Backs up database (if possible)
- ✅ Preserves schema structure
- ✅ Keeps configuration files

---

## Recovery & Undo

### If You Didn't Mean To Run It

**Immediate action (within minutes):**
```bash
# Check for backup database
ls -la /var/www/news/backups/articles.db.*

# If backup exists, restore:
cp /var/www/news/backups/articles.db.backup /var/www/news/articles.db
```

**Git recovery (if tracked):**
```bash
# Files in git are tracked, can be recovered
git log --follow -- website/responses/
```

---

## Common Workflows

### Workflow 1: Start Fresh from Scratch
```bash
# 1. Reset everything
python3 tools/reset_all.py --force

# 2. Verify reset
python3 tools/check_status.py

# 3. Run fresh pipeline
./run_pipeline.sh
```

### Workflow 2: Fix Data Corruption
```bash
# 1. Stop any running pipeline
pkill -f "python3 pipeline.py"

# 2. Reset system
python3 tools/reset_all.py --force

# 3. Verify database integrity
python3 -c "import sqlite3; sqlite3.connect('articles.db').execute('SELECT COUNT(*) FROM articles')"

# 4. Restart pipeline
./run_pipeline.sh
```

### Workflow 3: Targeted Cleanup
```bash
# Instead of reset_all, use specific tools:

# Delete specific article:
python3 tools/datapurge.py article_2025102401

# Clean images only:
python3 tools/imgcompress.py

# Purge pages only:
python3 tools/pagepurge.py
```

---

## Performance Notes

### Execution Time
- **Normal:** 2-5 seconds
- **With many files:** 10-30 seconds
- **Database reset:** < 1 second

### Resource Usage
- Minimal CPU
- Minimal RAM
- I/O dependent on file count

---

## Troubleshooting

### Issue: Tool Hangs

**Solution:**
```bash
# Check if database is locked
lsof /var/www/news/articles.db

# Kill process holding lock:
kill -9 <PID>

# Retry reset
python3 tools/reset_all.py --force
```

### Issue: "Permission denied" Error

**Solution:**
```bash
# Check current permissions
ls -la /var/www/news/

# Fix ownership if needed:
sudo chown -R ec2-user:ec2-user /var/www/news/

# Try again:
python3 tools/reset_all.py --force
```

### Issue: Database Schema Lost

**This shouldn't happen, but if it does:**
```bash
# Reinitialize database schema:
cd /var/www/news
python3 dbinit/init_db.py

# Verify:
python3 tools/check_status.py
```

---

## Advanced Usage

### Dry Run (Check What Would Be Deleted)

**Planned feature** - currently not available. Workaround:
```bash
# Just list what would be deleted:
find /var/www/news/website/responses/ -type f
find /var/www/news/website/article_image/ -type f
find /var/www/news/deepseek/responses/ -type f
```

### Selective Reset

If you only want to clean specific areas:
```bash
# Clean only image directory:
rm -rf /var/www/news/website/article_image/*

# Clean only responses:
rm -rf /var/www/news/website/responses/*

# Then verify:
python3 tools/check_status.py
```

---

## Related Tools

- **check_status.py** - Verify reset was successful (see [CHECK_STATUS_README.md](./CHECK_STATUS_README.md))
- **datapurge.py** - Remove single articles (see [DATAPURGE_README.md](./DATAPURGE_README.md))

---

## Command Reference

```bash
# Complete reset with safety check
python3 tools/reset_all.py --force

# Reset on remote server
ssh -i key.pem user@host "cd /var/www/news && python3 tools/reset_all.py --force"

# Reset and immediately verify
python3 tools/reset_all.py --force && python3 tools/check_status.py

# Reset and start fresh pipeline
python3 tools/reset_all.py --force && ./run_pipeline.sh
```

---

## Backup Before Reset

**Recommended:** Always backup before destructive operations:
```bash
# Backup database
cp /var/www/news/articles.db /var/www/news/backups/articles.db.before_reset_$(date +%s)

# Backup responses
tar -czf /var/www/news/backups/responses_backup_$(date +%Y%m%d).tar.gz /var/www/news/website/responses/

# Then reset
python3 tools/reset_all.py --force
```

---

**Last Updated:** October 25, 2025
**Author:** News Pipeline Team
**Status:** ✅ Production Ready
**Caution Level:** 🔴 High - Destructive Operation
