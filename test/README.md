# Test Directory

This directory contains testing and verification tools for the mining pipeline.

## Files

### `generate_article_report.py`
Python script that generates a comprehensive HTML report showing all articles from the database with:
- Article metadata (ID, title, source, URL, dates)
- Processing status (unprocessed/processed/failed)
- Article images (downloaded from RSS feeds)
- Full article content text
- Statistics and summary by source

**Usage:**
```bash
cd /Users/jidai/news
python3 test/generate_article_report.py
```

This creates `articles_report.html` which can be opened in any web browser.

### `articles_report.html`
The generated HTML report. Open this file in your browser to:
1. View all articles with their featured images
2. Read the full content of each article
3. Verify content lengths and quality
4. Check article sources and processing status
5. Verify image downloads were successful

## Workflow

1. Run the mining pipeline to collect articles:
   ```bash
   cd /Users/jidai/news/mining
   python3 -u run_mining_cycle.py
   ```

2. Generate the verification report:
   ```bash
   cd /Users/jidai/news
   python3 test/generate_article_report.py
   ```

3. Open `test/articles_report.html` in your browser to verify:
   - All articles collected successfully
   - Images downloaded and displaying
   - Content text is complete and properly formatted
   - Metadata is correct

## Key Statistics

The report header shows:
- **Total Articles**: Number of articles in database
- **Unprocessed**: Articles waiting for Deepseek API processing
- **Processed**: Articles successfully processed by Deepseek API
- **Failed**: Articles that failed during API processing

## Report Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Article Cards**: Each article displayed in a clean card format
- **Image Preview**: Featured image from each article
- **Status Badges**: Visual indicators for processing status
- **Search Friendly**: HTML structure optimized for browser Find (Ctrl+F / Cmd+F)
- **Direct Links**: Click article URLs to view original sources

## Notes

- Images are loaded from `mining/article_images/` directory
- Report is self-contained (includes all CSS inline)
- No external dependencies required to view
- Can be saved and shared as a single HTML file
