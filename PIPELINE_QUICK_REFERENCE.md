# Pipeline Quick Reference

## Complete Pipeline Command Examples

### Standard Run (2 articles per feed)
```bash
python3 pipeline.py --full
```

### Custom Mining Volume
```bash
# Light collection (1 article per feed)
python3 pipeline.py --full --articles-per-seed 1

# Standard collection (2 articles per feed - default)
python3 pipeline.py --full --articles-per-seed 2

# Medium collection (5 articles per feed)
python3 pipeline.py --full --articles-per-seed 5

# Heavy collection (10+ articles per feed)
python3 pipeline.py --full --articles-per-seed 10
```

### With Flags
```bash
# Dry-run preview
python3 pipeline.py --full --dry-run

# Verbose output
python3 pipeline.py --full -v

# Combined
python3 pipeline.py --full --articles-per-seed 5 --dry-run -v
```

## Individual Phase Commands

```bash
# Phase 1: Purge everything
python3 pipeline.py --purge

# Phase 2: Mining only (5 articles per feed)
python3 pipeline.py --mine --articles-per-seed 5

# Phase 3: Image processing only
python3 pipeline.py --images

# Phase 4: Deepseek AI enrichment
python3 pipeline.py --deepseek

# Phase 5: Verify results
python3 pipeline.py --verify
```

## Key Parameter: `--articles-per-seed`

Controls how many articles are collected per RSS feed seed.

| Value | Use Case | Time | Notes |
|-------|----------|------|-------|
| 1 | Testing | <1 min | Minimal data |
| 2 | Development | ~2 min | Default, balanced |
| 5 | Production | ~5 min | Good volume |
| 10+ | Aggressive | 10+ min | Large dataset |

## Output Files

**Database**: `articles.db`
- Articles table
- Images table  
- Analysis results

**Images**: `website/article_image/`
- Original images (resized to 1024×768)
- Mobile versions (600×450 WebP, <50KB)

**Results**: `pipeline_results_YYYYMMDD_HHMMSS.json`
- Pipeline execution log
- Phase statuses
- Timing information

## Data Structure

**Articles Table**
```
article_id (TEXT) - Semantic ID: YYYYMMDD+counter
title (TEXT)
content (TEXT)
source (TEXT)
image_id (INT) - Links to article_images
deepseek_processed (BOOL) - AI enrichment status
```

**Article Images Table**
```
article_id (TEXT)
image_name (TEXT) - Original filename
local_location (TEXT) - Web version path
small_location (TEXT) - Mobile version path
```

## Troubleshooting Checklist

- [ ] Database exists: `ls articles.db`
- [ ] Feeds configured: `sqlite3 articles.db "SELECT COUNT(*) FROM feeds;"`
- [ ] API key set: `sqlite3 articles.db "SELECT * FROM apikey WHERE name='deepseek';"`
- [ ] Disk space available: `df -h`
- [ ] Network connectivity: `ping 8.8.8.8`
- [ ] RSS feeds accessible: Open feed URLs in browser

## Next Steps After Pipeline

1. **Review Results**
   ```bash
   cat pipeline_results_*.json | jq .
   ```

2. **Check Database**
   ```bash
   sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
   ```

3. **View Images**
   ```bash
   ls -lh website/article_image/
   ```

4. **Verify Web Coverage**
   - Check `website/article_page/` for HTML pages
   - Check `website/article_response/` for JSON responses

5. **Monitor Deepseek Progress**
   ```bash
   sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"
   ```

## Performance Tips

1. **Start Small**: Test with `--articles-per-seed 1` first
2. **Monitor Resources**: Use `top` or Activity Monitor while running
3. **Adjust for Network**: Fewer seeds if network is slow
4. **Batch Processing**: Run phases independently if needed
5. **Schedule Off-Peak**: Run during low-usage hours

## Common Workflows

**Quick Test**
```bash
python3 pipeline.py --full --articles-per-seed 1 --dry-run -v
```

**Daily Update**
```bash
python3 pipeline.py --mine --articles-per-seed 2
python3 pipeline.py --images
python3 pipeline.py --deepseek
```

**Weekly Bulk**
```bash
python3 pipeline.py --full --articles-per-seed 10 -v
```

**Recovery from Failure**
```bash
python3 pipeline.py --verify
# Fix the issue, then re-run that phase
python3 pipeline.py --images  # or --deepseek, etc.
```

## Documentation

- **Complete Guide**: `PIPELINE_README_LATEST.md`
- **Tools Reference**: `tools/README.md`
- **Database Schema**: `dbinit/init_schema.md`
- **Checklist**: `PIPELINE_CHECKLIST.md`

---

**Version**: October 24, 2025  
**Latest Feature**: `--articles-per-seed` parameter for flexible mining volume
