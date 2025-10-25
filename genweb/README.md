# Genweb - Website Generator

Generates the website homepage with latest articles from each category.

## Purpose

- Reads processed articles from database
- Loads response JSON files for each article
- Loads article images
- Generates HTML index.html with responsive design
- Organizes articles by category (4-6 latest per category)

## Usage

### Local Generation
```bash
cd /Users/jidai/news
python3 genweb/generate_website.py
```

### On Server
```bash
cd /var/www/news
python3 genweb/generate_website.py
```

## Output

Generated HTML file: `website/generated/index.html`

## How It Works

1. **Database Query**: Reads all processed articles (deepseek_processed=1)
2. **Category Detection**: Finds all unique categories
3. **Response Loading**: For each article, loads the JSON response file
4. **Image Matching**: Finds corresponding article images
5. **HTML Generation**: Creates responsive card layout with Tailwind CSS
6. **Output**: Writes to website/generated/index.html

## Input Files

- `articles.db` - Article database with metadata
- `website/responses/article_*_response.json` - Deepseek analysis responses
- `website/article_image/article_*.jpg` - Article images
- `website/main/main_template.html` - Base HTML template

## Output Files

- `website/generated/index.html` - Final generated website

## Features

- ✅ Responsive design (mobile/tablet/desktop)
- ✅ Category-based organization
- ✅ Article cards with images
- ✅ Dark/light theme support
- ✅ Latest articles first
- ✅ Summary from Deepseek analysis
- ✅ Read More buttons

## Article Card Layout

Each card displays:
- Article image (or placeholder)
- Title
- Time since published
- Source
- Summary (from Deepseek analysis)
- Read More button

## Configuration

Edit these variables in generate_website.py:
- `limit: int = 6` - Articles per category
- `OUTPUT_DIR` - Where to save generated HTML
- `TEMPLATE_PATH` - Base template to use

## Status

- ✅ Basic generation working
- ✅ Category detection
- ✅ Response file loading
- ✅ HTML output

## Next Steps

- [ ] Add article detail pages
- [ ] Add search functionality
- [ ] Add filtering by date
- [ ] Add caching for performance
- [ ] Deploy to web server

**Last Updated:** October 25, 2025
