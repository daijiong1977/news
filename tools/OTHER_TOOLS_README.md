# DATAPURGE Tool - Article Data Removal

## Overview

Remove a specific article and all its associated data from the system.

**One-liner:** Delete one article and everything related to it.

---

## Purpose & Use Cases

### Primary Use
- Remove problematic articles
- Delete unwanted content
- Clean up test articles
- Fix corrupted article records

### When to Use
- Article has corrupted data
- Want to re-fetch specific article
- Article data needs refresh
- Cleaning up test content

---

## Usage

### Basic Syntax

```bash
python3 tools/datapurge.py <article_id>
```

### Examples

```bash
# Remove specific article
python3 tools/datapurge.py article_2025102401

# Expected output:
# ✓ Removed article_2025102401 from database
# ✓ Deleted response file
# ✓ Deleted images
```

---

## What Gets Deleted

- Article record from database
- Response JSON file
- Downloaded images (small & big)
- Generated HTML page

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Article not found` | Wrong ID or already deleted | Check article ID format |
| `Permission denied` | No write permissions | Check directory permissions |

---

**Last Updated:** October 25, 2025

---

# IMGCOMPRESS Tool - Image Optimization

## Overview

Compress and optimize all downloaded images for web delivery.

**One-liner:** Reduce image file sizes while maintaining quality.

---

## Purpose & Use Cases

### Primary Use
- Optimize images for web
- Reduce storage space
- Improve page load times
- Maintain image quality

### When to Use
- After downloading new images
- Before deploying to production
- To free up disk space
- Regular maintenance

---

## Usage

### Basic Syntax

```bash
python3 tools/imgcompress.py
```

### Options

- `--quality <value>` - JPEG quality (1-100, default: 85)
- `--force` - Re-compress already processed images

### Examples

```bash
# Standard compression
python3 tools/imgcompress.py

# Higher quality
python3 tools/imgcompress.py --quality 90

# Re-compress all
python3 tools/imgcompress.py --force
```

---

## Output

- Original size vs compressed size
- Compression ratio
- Files processed
- Space saved

---

**Last Updated:** October 25, 2025

---

# PAGEPURGE Tool - HTML Page Cleanup

## Overview

Remove all generated HTML preview pages.

**One-liner:** Clean up all generated article preview pages.

---

## Purpose & Use Cases

### Primary Use
- Remove generated HTML files
- Clean page cache
- Fix broken page references
- Regenerate pages

### When to Use
- Before re-generating pages
- Cleaning up old previews
- Fixing page generation errors
- Maintenance cleanup

---

## Usage

### Basic Syntax

```bash
python3 tools/pagepurge.py
```

### Examples

```bash
# Remove all generated pages
python3 tools/pagepurge.py

# Expected:
# ✓ Removed 25 HTML pages
# ✓ Cleaned article directory
```

---

**Last Updated:** October 25, 2025
