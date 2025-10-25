# CHECK_STATUS Tool - Comprehensive Status Checker

## Overview

Real-time status checker for the news pipeline that displays comprehensive statistics about article processing, files, and progress.

**One-liner:** Get a full view of what's processed, what's remaining, and what files exist.

---

## Purpose & Use Cases

### Primary Use
- Monitor pipeline progress in real-time
- Track article processing status
- Verify files are being created correctly
- Detect JSON parsing errors
- Validate database integrity

### When to Use
- After running the pipeline
- To check if processing is complete
- To debug missing files
- To validate multi-pass retry results
- To verify no parse errors occurred

---

## Requirements

- Python 3.6+
- SQLite3 database (articles.db)
- Directory structure:
  - `/var/www/news/articles.db` (database)
  - `/var/www/news/website/responses/` (response files)
  - `/var/www/news/website/article_image/` (images)

---

## Installation

No installation needed. Script is part of the tools directory.

```bash
cd /var/www/news
python3 tools/check_status.py
```

---

## Usage

### Basic Syntax

```bash
python3 tools/check_status.py
```

No arguments needed - tool auto-detects all paths and queries database.

### Options

Currently no command-line options. Tool runs in auto-mode.

**Future Options (Planned):**
- `--verbose` - Show detailed file listings
- `--json` - Output as JSON for parsing
- `--watch` - Auto-refresh every N seconds

### Examples

#### Example 1: Check Current Status
```bash
$ python3 tools/check_status.py
```

Output:
```
======================================================================
📊 NEWS PIPELINE STATUS CHECK
======================================================================
⏰ Timestamp: 2025-10-25 16:06:23

📦 DATABASE STATISTICS:
----------------------------------------------------------------------
  Total Articles:    33
  ✅ Processed:       8 (24.2%)
  ⏳ Remaining:       25 (75.8%)

📁 FILE STATISTICS:
----------------------------------------------------------------------
  Response JSON:     8 files
  Image Small:       0 files
  Image Big:         0 files
  Raw Response:      0 files (parse errors)

📈 SUMMARY:
----------------------------------------------------------------------
  ✅ No JSON parse errors detected
  ✅ All 8 processed articles have response files

  Progress: [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 24.2%

======================================================================
```

#### Example 2: Run After Full Completion
```bash
$ python3 tools/check_status.py
```

Expected output when all done:
```
  Total Articles:    33
  ✅ Processed:       33 (100.0%)
  ⏳ Remaining:       0 (0.0%)
  ...
  ✅ All 33 processed articles have response files
  Progress: [██████████████████████████████████████████████████] 100.0%
```

---

## Output Explanation

### Database Statistics Section

| Metric | Meaning |
|--------|---------|
| **Total Articles** | All articles in database (some may be incomplete) |
| **✅ Processed** | Articles with `deepseek_processed=1` (analyzed by Deepseek) |
| **⏳ Remaining** | Articles with `deepseek_processed=0` (waiting for processing) |

**Note:** Total = Processed + Remaining

### File Statistics Section

| File Type | Description | Expected Count |
|-----------|-------------|-----------------|
| **Response JSON** | Deepseek analysis responses | Should equal Processed count |
| **Image Small** | Thumbnail images | Should equal downloaded articles |
| **Image Big** | Full-size images | Should equal downloaded articles |
| **Raw Response** | Malformed JSON saved for debugging | Should be 0 (unless errors) |

### Summary Section

- ✅ Green check: All good, no issues
- ⚠️ Warning: Mismatch or issue detected
- Raw response files listed indicate JSON parse errors

### Progress Bar

Visual representation of processing completion:
- Filled: `█` - Processed articles
- Empty: `░` - Remaining articles

---

## Columns & Metrics

### Database Queries Run

1. **Total Count:** `SELECT COUNT(*) FROM articles`
2. **Processed:** `SELECT COUNT(*) FROM articles WHERE deepseek_processed=1`
3. **Remaining:** `SELECT COUNT(*) FROM articles WHERE deepseek_processed=0`

### File Counts

Uses glob patterns to count:
- Responses: `article_*_response.json`
- Small Images: `image_small_*.jpg`
- Big Images: `image_big_*.jpg`
- Raw Responses: `raw_response_article_*.txt`

---

## Error Handling

### Possible Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `❌ Error reading database` | Database locked or corrupted | Check file permissions, restart pipeline |
| `❌ Error counting files in /path` | Directory doesn't exist or no read permission | Check directory exists, verify permissions |
| `⚠️ Response files != Processed DB` | Files missing but DB says processed | Check `/var/www/news/website/responses/` |

### What to Check if Errors Occur

1. **Database access:**
   ```bash
   ls -la /var/www/news/articles.db
   ```

2. **Response directory:**
   ```bash
   ls -la /var/www/news/website/responses/
   ```

3. **Permissions:**
   ```bash
   stat /var/www/news/articles.db
   ```

---

## Performance Notes

- **Execution Time:** < 1 second (normal)
- **Resource Usage:** Minimal CPU and memory
- **Database Impact:** Read-only, no locks
- **Scaling:** Performance remains consistent up to 1000+ articles

### Optimization Tips

- Run frequently without concern for performance
- Safe to run while pipeline is actively processing
- Can be integrated into monitoring systems

---

## Integration Examples

### Shell Script Loop (Check Every 30s)
```bash
#!/bin/bash
while true; do
    clear
    python3 /var/www/news/tools/check_status.py
    sleep 30
done
```

### Cron Job (Check Every 5 Minutes)
```bash
*/5 * * * * cd /var/www/news && python3 tools/check_status.py >> /var/log/news-status.log
```

### As Part of Monitoring Dashboard
The tool's clean output is designed for easy parsing in monitoring systems.

---

## Troubleshooting

### Issue: "Could not read database"

**Solution:**
```bash
# Check if database exists
ls -lh /var/www/news/articles.db

# Check if it's readable
file /var/www/news/articles.db

# Test with direct query
cd /var/www/news && python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
print('Database OK')
"
```

### Issue: File counts don't match processed count

**Possible causes:**
1. Files are in a different location
2. File naming convention changed
3. Processing completed but files not yet written

**Solution:**
```bash
# Find all response files
find /var/www/news/website/responses/ -name "*response*"

# Check file creation times
ls -lhtr /var/www/news/website/responses/ | tail -10
```

### Issue: Shows raw response errors

**Meaning:** Some articles had JSON parse errors

**Solution:**
```bash
# View raw response files
ls -lh /var/www/news/website/responses/raw_response_*

# Check first raw response
head -50 /var/www/news/website/responses/raw_response_article_*.txt

# These will be retried in next pipeline run
```

---

## Recent Updates

### Version 1.0 (2025-10-25)
- Initial release
- Database statistics
- File counting with multiple patterns
- Progress visualization
- Error detection and reporting

### Planned Features
- JSON output mode for scripting
- Real-time refresh option
- Detailed file listings
- Historical trend tracking

---

## Related Tools

- **reset_all.py** - Reset and clean everything (see [RESET_ALL_README.md](./RESET_ALL_README.md))
- **datapurge.py** - Remove specific articles (see [DATAPURGE_README.md](./DATAPURGE_README.md))

---

## Command Reference

```bash
# View full status
python3 tools/check_status.py

# Check status on EC2 server
ssh -i key.pem user@host "cd /var/www/news && python3 tools/check_status.py"

# Capture output to file
python3 tools/check_status.py > status_report.txt

# Monitor every 30 seconds (Ctrl+C to stop)
watch -n 30 'cd /var/www/news && python3 tools/check_status.py'
```

---

**Last Updated:** October 25, 2025
**Author:** News Pipeline Team
**Status:** ✅ Production Ready
