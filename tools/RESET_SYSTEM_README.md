# Reset and Purge System - Complete Reference

**Date**: October 24, 2025  
**Status**: Production Ready

---

## Quick Start

```bash
# Preview what will be deleted (SAFE - no changes)
python3 tools/reset_all.py

# Actually execute the purge
python3 tools/reset_all.py --force

# Then start fresh pipeline
python3 pipeline.py --full
```

---

## System Overview

The reset system is designed to provide **safe, selective data purging** while preserving critical configuration:

### What Gets Deleted

**Article-Related Data** (all cleared on purge):
- `articles` - All news articles
- `article_images` - Associated images (DB records)
- `keywords` - Extracted keywords
- `questions` - Generated quiz questions
- `choices` - Quiz answer choices
- `article_summaries` - AI-generated summaries
- `article_analysis` - Analysis data
- `comments` - User comments
- `background_read` - Background reading material
- `response` - Deepseek API responses (DB records)

**Website Files** (optional):
- `website/article_image/` - Article images on disk
- `website/article_page/` - Article HTML pages
- `website/article_response/` - Response JSON files

**Processing Files** (optional):
- `deepseek/responses/` - Deepseek API responses
- `mining/responses/` - Mining collected data

### What Gets Preserved

**Configuration Tables** (NEVER deleted):
- `apikey` - API credentials
- `feeds` - RSS feed sources (13 configured)
- `categories` - Article categories (7 defined)
- `difficulty_levels` - Content difficulty ratings (4 levels)
- `users` - User accounts and profiles
- `user_difficulty_levels` - User preferences
- `user_categories` - User category preferences
- `user_preferences` - Subscription settings
- `user_awards` - User statistics

**Why Preserve?**
- No need to reconfigure feeds/categories after each purge
- User data and preferences maintained
- API keys stay in place
- System ready for immediate data collection

---

## Command Reference

### Full Purge (Recommended)

```bash
# Preview (safe, no changes)
python3 tools/reset_all.py

# Execute (requires confirmation)
python3 tools/reset_all.py --force

Result:
- ✓ All articles deleted
- ✓ All website files deleted
- ✓ All processing responses deleted
- ✓ Configuration tables PRESERVED
```

### Database Only

```bash
# Delete article data, keep website files
python3 tools/reset_all.py --db-only --force

Use case: Analyze website files without DB records
```

### Files Only

```bash
# Delete website files, keep database records
python3 tools/reset_all.py --files-only --force

Use case: Rebuild website files without re-mining articles
```

### Keep Database

```bash
# Delete everything except database
python3 tools/reset_all.py --keep-db --force

Use case: Clean up processing files, keep article records
```

### Deepseek Responses Only

```bash
# Delete only deepseek/responses/ files
python3 tools/reset_all.py --deepseek-only --force

Use case: Reprocess articles with new Deepseek version
```

### Mining Responses Only

```bash
# Delete only mining/responses/ files
python3 tools/reset_all.py --mining-only --force

Use case: Clean up mining cache
```

### Verbose Mode

```bash
# Show detailed information during purge
python3 tools/reset_all.py --force -v
```

---

## Usage Workflows

### Workflow 1: Daily Fresh Start

```bash
# Morning: Clear yesterday's data
python3 tools/reset_all.py --force

# Run today's pipeline
python3 pipeline.py --full --articles-per-seed 5

# Analyze results
ls -lh website/article_image/
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
```

### Workflow 2: Test New Configuration

```bash
# Before changing feeds/categories:
# 1. Backup current database (optional)
cp articles.db articles.db.backup

# 2. Clear article data
python3 tools/reset_all.py --force

# 3. Add new feeds via database or UI

# 4. Run pipeline with new configuration
python3 pipeline.py --full --articles-per-seed 2

# 5. If issues, restore:
# cp articles.db.backup articles.db
```

### Workflow 3: Debug Issue with Specific Date

```bash
# Using datapurge.py for fine-grained control:
# Delete specific date only (keep other articles)
python3 tools/datapurge.py --date 2025-10-24 --force

# Delete specific article:
python3 tools/datapurge.py --article-id 2025102401 --force

# Delete date range:
python3 tools/datapurge.py --date-range 2025-10-20 2025-10-24 --force
```

### Workflow 4: Rebuild Website Files

```bash
# Clear website files but keep database
python3 tools/reset_all.py --files-only --force

# Rebuild web and mobile images
python3 tools/imgcompress.py --auto --web --mobile

# Regenerate HTML pages (if applicable)
```

---

## Understanding the Output

### Dry-Run Output Example

```
⚠️  DRY RUN MODE (no data will be deleted)
    Use --force flag to actually execute purge

==============================================================
🧹 COMPLETE PURGE - Everything
==============================================================

🗑️  Deleting database records...
  ✓ article_images: 2 records
  ✓ article_summaries: 2 records
  ✓ keywords: 2 records
  ✓ articles: 3 records

✅ Database purged: 9 records deleted

📌 Preserved (not deleted):
  • apikey: 2 records
  • feeds: 13 records
  • categories: 7 records
  • difficulty_levels: 4 records

==============================================================
✅ PURGE COMPLETE
==============================================================

📊 Summary:
  • Database: 9 records
```

**Interpretation:**
- Will delete 9 article records total (3 articles + related data)
- Will preserve 26 configuration records (2+13+7+4)
- Database integrity maintained (foreign keys respected)

---

## Safety Features

1. **Dry-Run by Default**
   - Always shows preview first
   - Actual deletion requires `--force` flag
   - Safe to run multiple times

2. **Foreign Key Integrity**
   - Deletes in correct order
   - Disables FK checks only during operation
   - Re-enables after completion

3. **Atomic Operations**
   - Either fully succeeds or fully rolls back
   - No partial deletes

4. **Clear Reporting**
   - Shows exact counts being deleted
   - Shows what will be preserved
   - Progress during execution

---

## Troubleshooting

### Issue: Tool says "0 records" but I expect data

**Solution:** Verify database has data:
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"
```

### Issue: Want to delete only specific articles

**Solution:** Use datapurge.py instead:
```bash
# Delete articles from specific date
python3 tools/datapurge.py --date 2025-10-24 --force

# Delete specific article
python3 tools/datapurge.py --article-id 2025102401 --force

# Delete date range
python3 tools/datapurge.py --date-range 2025-10-15 2025-10-20 --force
```

### Issue: Accidentally deleted important data

**Solution:** Restore from backup:
```bash
# If you made a database backup beforehand:
cp articles.db.backup articles.db
```

**Prevention:** Always run dry-run first:
```bash
python3 tools/reset_all.py  # Preview
# Verify output looks correct
python3 tools/reset_all.py --force  # Execute
```

---

## Integration with Pipeline

### Recommended Pipeline Flow

```bash
# Step 1: Preview the purge
python3 tools/reset_all.py

# Step 2: Execute if satisfied
python3 tools/reset_all.py --force

# Step 3: Run complete pipeline
python3 pipeline.py --full --articles-per-seed 5 -v

# Step 4: Verify results
cat log/pipeline_results_*.json | jq .
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"
```

---

## Related Tools

| Tool | Purpose | When to Use |
|------|---------|------------|
| `reset_all.py` | Complete purge (smart) | Before each pipeline run |
| `datapurge.py` | Selective article deletion | Delete specific dates only |
| `pagepurge.py` | Delete website files | Clean up artifacts |
| `imgcompress.py` | Generate web/mobile images | After mining new articles |

---

## Configuration Files Not Touched

The following are NEVER modified by purge tools:

- `.env` - Environment variables
- `.gitignore` - Git configuration
- `articles.db` schema - Table structure preserved
- Configuration tables - Always kept
- Feed list - Always preserved
- User accounts - Always preserved
- API keys - Always preserved

---

## Performance Notes

- **Full purge**: ~1-2 seconds
- **Database-only purge**: ~1 second
- **Website files purge**: ~1-5 seconds (depends on count)
- **Safe preview**: Instant (no disk operations)

---

## Best Practices

1. ✅ **Always preview first** before using `--force`
2. ✅ **Make backups** before major changes
3. ✅ **Run with verbose** (`-v`) to see progress
4. ✅ **Check database** after purge to verify
5. ✅ **Use selective deletion** (datapurge.py) for fine-grained control
6. ❌ **Don't manually edit database** during purge operation
7. ❌ **Don't interrupt** the purge process (Ctrl+C during non-dry-run)

---

## Examples

### Example 1: Fresh Start Each Morning

```bash
#!/bin/bash
# daily_purge.sh

echo "🧹 Starting daily fresh purge..."
python3 /Users/jidai/news/tools/reset_all.py --force

echo "✅ Database cleared (configuration preserved)"
echo "📊 Stats:"
sqlite3 /Users/jidai/news/articles.db << 'EOF'
.mode column
.headers on
SELECT 'Articles' as Type, COUNT(*) as Count FROM articles
UNION ALL
SELECT 'Feeds', COUNT(*) FROM feeds
UNION ALL
SELECT 'Categories', COUNT(*) FROM categories;
EOF

echo "🚀 Ready for pipeline run"
```

### Example 2: Selective Date Purge

```bash
# Remove articles from yesterday only
YESTERDAY=$(date -v-1d +%Y-%m-%d)
python3 tools/datapurge.py --date $YESTERDAY --force
```

### Example 3: Archive and Purge

```bash
# Backup database before purge
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp articles.db "backups/articles.db.${BACKUP_DATE}"

# Purge
python3 tools/reset_all.py --force

echo "Backed up to: backups/articles.db.${BACKUP_DATE}"
```

---

## Support

For issues or questions:
1. Check `tools/README.md` for tool-specific documentation
2. Run with `--help` for command options
3. Run with `-v` (verbose) for detailed output
4. Examine `log/` directory for pipeline results

---

**Last Updated**: October 24, 2025  
**Version**: 1.0  
**Status**: Production Ready
