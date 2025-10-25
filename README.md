# News Pipeline - Main README

**Project**: Automated News Content Pipeline  
**Status**: ✅ Production Ready  
**Last Updated**: October 25, 2025

## What This Project Does

The News Pipeline is a complete automation system that:

1. **Collects** articles from 6 RSS feeds daily
2. **Processes** images (creates web and mobile versions)
3. **Analyzes** articles using Deepseek AI (generates summaries, questions, keywords)
4. **Stores** everything in a database with full tracking

The entire process is orchestrated by `pipeline.py` and runs with zero manual intervention.

## Quick Start

### 1. Basic Pipeline Run
```bash
# Collect 1 article per feed (6 total)
python3 pipeline.py --full --articles-per-seed 1

# Or 3 articles per feed (18 total)
python3 pipeline.py --full --articles-per-seed 3

# Or use defaults (2 per feed = 12 total)
python3 pipeline.py --full
```

### 2. Run Individual Phases
```bash
python3 pipeline.py --mine              # Phase 1: Collect articles
python3 pipeline.py --images            # Phase 2: Optimize images
python3 pipeline.py --deepseek          # Phase 3: AI analysis
python3 pipeline.py --verify            # Phase 4: Verification only
```

### 3. Monitor Progress
```bash
# Watch Deepseek processing in real-time
tail -f log/phase_deepseek_*.log

# View latest pipeline results
cat log/pipeline_results_*.json | jq .

# Check database status
sqlite3 articles.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM article_images;"
```

## Documentation

### For Daily Users
- **Start here**: `PIPELINE.md` - Complete guide to running the pipeline

### For Maintenance
- **System rules**: `GROUNDRULE.md` - Architecture, database schema, constraints (READ-ONLY)
- **What's new**: `LATEST_CHANGES.md` - Recent improvements and fixes

### For Developers
- Code in: `pipeline.py`, `mining/`, `deepseek/`, `tools/`
- Each script has inline comments and error handling

## Pipeline Phases Explained

```
┌─── PHASE 1: MINING ─────────┐
│ Collect articles from RSS   │
│ Download images for each    │
│ Link articles to images     │  🎯 Auto-links images!
└───────────┬─────────────────┘
            │
┌───────────▼─────────────────┐
│ PHASE 2: IMAGE HANDLING     │
│ Create web versions         │
│ Create mobile versions      │  📱 Optimized for all screens
└───────────┬─────────────────┘
            │
┌───────────▼─────────────────┐
│ PHASE 3: DEEPSEEK ANALYSIS  │
│ Call AI for each article    │
│ Auto-insert responses       │  🤖 Fully automated!
│ Move files to final place   │
└───────────┬─────────────────┘
            │
┌───────────▼─────────────────┐
│ PHASE 4: VERIFICATION       │
│ Count articles, images      │
│ Report final status         │  ✅ Comprehensive summary
└─────────────────────────────┘
```

## Key Improvements (Oct 2025)

✅ **Automated Image Linking** - Articles automatically linked to images  
✅ **Automated Response Insertion** - No manual steps needed  
✅ **Comprehensive Logging** - Every phase creates timestamped logs  
✅ **Simplified Mining** - No API key requirement in phase 1  

## Recent Test Results

**Configuration**: 1 article per feed (6 sources = 6 articles total)

```
Phase 1 (Mining):           ✅ 6 articles collected, 6/6 with images
Phase 2 (Image Handling):   ✅ 6 images optimized (web + mobile)
Phase 3 (Deepseek):         ✅ 6 articles analyzed, 6/6 inserted
Phase 4 (Verification):     ✅ All counts verified
Database Status:            ✅ deepseek_processed = 6
```

## Database

### Location
```
/Users/jidai/news/articles.db
```

### Quick Queries
```bash
# Count all articles
sqlite3 articles.db "SELECT COUNT(*) FROM articles;"

# Count articles with images
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE image_id IS NOT NULL;"

# Count processed articles (Deepseek)
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"

# See all articles
sqlite3 articles.db ".headers on" ".mode column" "SELECT id, title, source, deepseek_processed FROM articles LIMIT 10;"
```

## File Locations

### Important Directories
```
/Users/jidai/news/
├── articles.db                      ← Database
├── pipeline.py                      ← Main script
├── mining/
│   ├── run_mining_cycle.py         ← Phase 1 entry
│   └── data_collector.py            ← Feed fetching + image download
├── deepseek/
│   ├── process_one_article.py      ← Phase 3: API calls
│   ├── insert_from_response.py      ← Phase 3: DB insertion
│   └── responses/                   ← Temp response storage
├── tools/
│   ├── imgcompress.py              ← Phase 2: Image optimization
│   └── reset_all.py                ← Database cleanup utility
├── website/
│   ├── article_image/              ← Article images (web + mobile)
│   └── article_response/           ← AI response JSON files
└── log/
    ├── phase_*.log                 ← Phase logs (timestamped)
    └── pipeline_results_*.json      ← Pipeline summary results
```

## Commands Reference

### Common Operations
```bash
# Full pipeline with defaults
python3 pipeline.py --full

# Full pipeline with 1 article per feed
python3 pipeline.py --full --articles-per-seed 1

# Full pipeline with 3 articles per feed
python3 pipeline.py --full --articles-per-seed 3

# Verbose output
python3 pipeline.py --full -v

# Dry-run (preview without changes)
python3 pipeline.py --full --dry-run

# Mining only
python3 pipeline.py --mine

# Mining + images (skip deepseek)
python3 pipeline.py --mine --images

# Reset database (start fresh)
python3 tools/reset_all.py --force
```

### Troubleshooting Commands
```bash
# Check if database exists
ls -lh articles.db

# View recent logs
ls -lt log/ | head -5

# Count recent articles
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE crawled_at > datetime('now', '-1 day');"

# Check for processing errors
grep -i "error\|failed" log/phase_deepseek_*.log

# View API key (if set)
sqlite3 articles.db "SELECT * FROM apikey WHERE name='DeepSeek';"
```

## Logging System

### Log Files Created Per Run
```
log/phase_mining_20251025_153000.log
log/phase_image_handling_20251025_153000.log
log/phase_deepseek_20251025_153000.log
log/pipeline_results_20251025_153000.json
```

### Log Content Example
```
[2025-10-25T15:30:00.123456] Starting mining phase (articles per seed: 1)
[2025-10-25T15:30:05.234567] → Mining cycle complete
[2025-10-25T15:30:05.345678] Command: python3 /Users/jidai/news/mining/run_mining_cycle.py
[2025-10-25T15:30:08.456789] Exit code: 0
[2025-10-25T15:30:08.567890] Database now contains 6 articles
[2025-10-25T15:30:08.678901] Articles with images: 6/6
```

## Performance

### Typical Execution Times
- **Mining Phase**: 3-5 seconds per article
- **Image Handling**: 1-2 seconds per image
- **Deepseek Phase**: 10-30 seconds per article (network dependent)
- **Full Pipeline (6 articles)**: ~3-5 minutes
- **Full Pipeline (18 articles)**: ~10-15 minutes

## Troubleshooting

### Problem: Pipeline hangs
**Solution**: Check if Deepseek API is responding
```bash
tail -f log/phase_deepseek_*.log
```

### Problem: Images not showing
**Solution**: Check image linking
```bash
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE image_id IS NOT NULL;"
# Should return same count as total articles
```

### Problem: Deepseek responses not inserted
**Solution**: Check logs for insertion errors
```bash
grep -i "insertion\|insert\|failed" log/phase_deepseek_*.log
```

### Problem: Database looks corrupt
**Solution**: Reset and start fresh
```bash
python3 tools/reset_all.py --force
python3 pipeline.py --full --articles-per-seed 1
```

## System Requirements

- Python 3.7+
- SQLite3
- Internet connection (for RSS feeds and Deepseek API)
- ~500MB disk space for images and responses

## Dependencies

### Python packages (installed automatically)
- requests (HTTP calls)
- beautifulsoup4 (HTML parsing)
- pillow (image processing)
- sqlite3 (standard library)

## Maintenance

### Recommended Maintenance Tasks

**Daily**:
- Check logs for errors: `grep -i error log/phase_deepseek_*.log`
- Verify article count: `sqlite3 articles.db "SELECT COUNT(*) FROM articles;"`

**Weekly**:
- Review pipeline performance
- Check disk space: `du -sh website/ log/`
- Archive old logs if needed

**Monthly**:
- Full database check: `sqlite3 articles.db ".integrity_check"`
- Backup database: `cp articles.db articles.db.backup`

### Database Cleanup

Reset everything (articles, images, responses) but keep configuration:
```bash
python3 tools/reset_all.py --force
```

## Support & Documentation

### Quick Reference Documents
- `PIPELINE.md` - Complete pipeline documentation
- `GROUNDRULE.md` - System architecture and rules (READ-ONLY)
- `LATEST_CHANGES.md` - Recent improvements and what's new

### Getting Help
1. Check logs: `log/phase_*.log`
2. Read PIPELINE.md for detailed guides
3. Check GROUNDRULE.md for system architecture
4. Review LATEST_CHANGES.md for recent fixes

## Project Status

✅ **Production Ready**
- All phases functional
- Automated end-to-end
- Comprehensive logging
- Tested and validated

🔄 **Continuous Improvement**
- Monitoring for edge cases
- Ready for optimizations
- Scalable architecture

## Version History

| Version | Date | Status |
|---------|------|--------|
| 2.0 | Oct 25, 2025 | Current - Full automation + logging |
| 1.0 | Oct 23, 2025 | Initial release |

## License

Internal project for news content management

---

**Quick Start**: `python3 pipeline.py --full --articles-per-seed 1`

**Documentation**: Start with `PIPELINE.md` for detailed guides

**Issues**: Check `log/` directory for detailed error messages

**Questions**: Read `GROUNDRULE.md` for system architecture

