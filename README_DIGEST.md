# Daily News Digest System

A comprehensive setup to aggregate RSS feeds, extract full article content, and send daily email digests.

## Features

- ✅ Configure 3-5+ RSS feed sources with a friendly CLI
- ✅ Extract top 3 articles per source from the last 24 hours
- ✅ Pull full article content from original links (not just summaries)
- ✅ Structured output in HTML and JSON formats
- ✅ Google Gmail integration with App Passwords for secure email delivery
- ✅ Configure multiple recipient emails
- ✅ Full ISO timestamp support for all articles

## Quick Start

### 1. Initial Configuration

Run the interactive setup tool:

```bash
python3 setup_config.py
```

This will guide you through:
- **Adding RSS Sources**: Add 3-5 news sources with their RSS feed URLs
- **Gmail SMTP Setup**: Configure your Gmail account for sending emails
- **Email Recipients**: Add recipient email addresses
- **Digest Settings**: Customize how many articles, time lookback, etc.

### 2. Generate Daily Digest

Simply run:

```bash
python3 generate_daily_digest.py
```

This will:
- Fetch all enabled RSS sources
- Get the top 3 articles from the last 24 hours per source
- Extract full content from each article link
- Generate `daily_digest.html` (formatted for reading) and `daily_digest.json` (for integration)

### 3. Send via Email (Optional)

To send the digest to configured recipients:

```bash
python3 generate_daily_digest.py --send-email
```

## Configuration File (config.json)

The system saves all settings in `config.json`:

```json
{
  "rss_sources": [
    {
      "name": "Source Name",
      "url": "https://example.com/rss",
      "enabled": true
    }
  ],
  "smtp": {
    "enabled": false,
    "gmail_address": "your-email@gmail.com",
    "gmail_app_password": ""
  },
  "recipients": ["recipient1@example.com", "recipient2@example.com"],
  "digest_settings": {
    "articles_per_source": 3,
    "hours_lookback": 24,
    "include_images": true,
    "output_html": "daily_digest.html",
    "output_json": "daily_digest.json"
  }
}
```

## Google Gmail Setup (for Email Sending)

To enable email delivery via Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Google will provide a 16-character password
3. **In setup_config.py**:
   - Select option 2 (Configure Google SMTP Email)
   - Enter your Gmail address
   - Enter the 16-character app password
   - Test the connection

## JSON Output Format

Each article includes:

```json
{
  "source": "Source Name",
  "title": "Article Title",
  "link": "https://original-article-link.com",
  "pub_date": "2025-10-19T17:50:40-04:00",
  "snippet": "Brief summary from RSS",
  "content": "Full extracted article content..."
}
```

## HTML Output Format

Generated `daily_digest.html` includes:
- Professional styling with responsive design
- Articles grouped by source
- Clickable links to original articles
- ISO timestamps for each article
- First 10 paragraphs of content per article

## Daily Automation (Cron)

To run the digest daily at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 9:00 AM every day)
0 9 * * * cd /Users/jidai/news && python3 generate_daily_digest.py --send-email >> /Users/jidai/news/digest.log 2>&1
```

## Command-Line Options

```bash
# Generate digest only (no email)
python3 generate_daily_digest.py

# Send email after generation
python3 generate_daily_digest.py --send-email

# Override output files
python3 generate_daily_digest.py --html-output custom.html --json-output custom.json
```

## File Structure

```
/Users/jidai/news/
├── config.json                       # Main configuration file
├── setup_config.py                   # Interactive configuration tool
├── generate_daily_digest.py          # Main digest generator
├── generate_pbs_rss_digest.py        # PBS-specific generator (optional)
├── generate_swimmingworld_rss_digest.py  # Swimming World generator (optional)
├── daily_digest.html                 # Generated HTML digest
├── daily_digest.json                 # Generated JSON digest
└── digest.log                        # Cron log (if automated)
```

## Example Workflow

1. **First time**: `python3 setup_config.py` - Configure your sources and email
2. **Daily**: `python3 generate_daily_digest.py --send-email` - Generate and send
3. **Open**: Open `daily_digest.html` in your browser to preview

## Supported RSS Feeds

Currently configured and tested:
- **PBS NewsHour**: https://www.pbs.org/newshour/feeds/rss/headlines
- **Swimming World Magazine**: https://www.swimmingworldmagazine.com/news/feed/

Other feeds can be added via the setup tool. The system automatically:
- Handles gzip/deflate compression
- Parses multiple XML formats
- Extracts article content intelligently
- Normalizes timestamps to ISO format

## Troubleshooting

### No articles found
- Check that RSS sources are enabled in config
- Verify RSS feed URLs are correct
- Check that articles exist within the 24-hour lookback window

### Email not sending
- Verify SMTP is enabled in config
- Test connection in setup_config.py (option 2 → option 4)
- Check email recipients are configured
- Ensure Gmail 2FA is enabled and app password is correct

### Slow extraction
- Some sites require deep page parsing
- System sleeps 0.3 seconds between requests to be respectful
- You can run during off-peak hours for faster processing

## Development

To add a new RSS source:

1. Run `setup_config.py` → option 1 (Add RSS source)
2. Enter source name and feed URL
3. Next run will include it automatically

To customize content extraction:

- Edit the `extract_article_content()` function in `generate_daily_digest.py`
- The system uses `ParagraphExtractor` and `PlainTextExtractor` from `generate_us_news_page.py`
- Adjust regex patterns to match your target sites

## License

Built for personal news aggregation and distribution.
