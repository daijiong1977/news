# Payload Generation Scripts

This directory contains scripts to generate JSON payloads for the News Oh,Ye! website.

## Overview

The website uses dynamic JSON payloads to load articles without regenerating HTML files. There are two types of payloads:

1. **Main Page Payloads** - For index.html (main news page)
2. **Article Page Payloads** - For article.html (individual article detail pages)

---

## Scripts

### 1. `mainpayload_generate.py`

**Purpose:** Generates JSON payloads for the main page (index.html)

**What it does:**
- Creates 13 JSON files per payload directory:
  - 12 article list files: `articles_{category}_{level}.json`
    - Categories: news, science, fun
    - Levels: easy, middle, high, cn
  - 1 archive index: `archive_available_dates.json`
- Creates timestamped directory: `website/main/payloads_YYYYMMDD_HHMMSS/`
- Updates symlink: `website/main/payloads_latest` → newest directory

**Usage:**
```bash
# Generate main page payloads
python3 genpayload/mainpayload_generate.py
```

**Output Example:**
```
website/main/payloads_20251026_152000/
├── articles_news_easy.json
├── articles_news_middle.json
├── articles_news_high.json
├── articles_news_cn.json
├── articles_science_easy.json
├── articles_science_middle.json
├── articles_science_high.json
├── articles_science_cn.json
├── articles_fun_easy.json
├── articles_fun_middle.json
├── articles_fun_high.json
├── articles_fun_cn.json
└── archive_available_dates.json

website/main/payloads_latest → payloads_20251026_152000/
```

**When to run:**
- After daily article processing (Deepseek analysis complete)
- When you want to update the main page with new articles
- Automatically via cron for daily updates

---

### 2. `batch_generate_json_payloads.py`

**Purpose:** Generates JSON payloads for article detail pages (article.html)

**What it does:**
- Creates individual payload directories for each article
- Generates 3 difficulty levels per article: easy.json, middle.json, high.json
- Includes comprehensive article data (quizzes, keywords, perspectives, ground rules)
- Tracks generation status in database (incremental updates)

**Usage:**
```bash
# Generate payloads for all articles
python3 genpayload/batch_generate_json_payloads.py

# Generate payloads for specific articles only
python3 genpayload/batch_generate_json_payloads.py --articles 2025102601 2025102602

# Force regenerate (ignore already generated status)
python3 genpayload/batch_generate_json_payloads.py --force

# Dry run (preview without generating)
python3 genpayload/batch_generate_json_payloads.py --dry-run
```

**Output Example:**
```
```

**Output Example:**
```
website/article_response/payload_2025102601/
├── easy.json
├── middle.json
└── high.json

website/article_response/payload_2025102602/
├── easy.json
├── middle.json
```
```

**When to run:**
- After Deepseek processing completes for new articles
- When you want to regenerate specific article payloads
- Incrementally (only generates missing payloads by default)

---

## Workflow Integration

### Daily Automated Workflow

```bash
# 1. Run pipeline (mining + images + deepseek)
python3 pipeline.py --full --articles-per-seed 3

# 2. Generate article page payloads
python3 genpayload/batch_generate_json_payloads.py

# 3. Generate main page payloads
python3 genpayload/mainpayload_generate.py
```

### Manual Payload Updates

```bash
# Regenerate everything
python3 genpayload/batch_generate_json_payloads.py --force
python3 genpayload/mainpayload_generate.py

# Update specific articles
python3 genpayload/batch_generate_json_payloads.py --articles 2025102601 2025102602
python3 genpayload/mainpayload_generate.py
```

---

## Payload Structure

### Main Page Payload (articles_news_middle.json)
```json
{
  "articles": [
    {
      "id": "2025102601",
      "title": "Article Title",
      "summary": "Article summary text...",
      "source": "BBC News",
      "time_ago": "2 hours ago",
      "image_url": "../article_image/article_2025102601_hash_mobile.webp",
      "category": "News"
    }
  ]
}
```

### Article Page Payload (easy.json)
```json
{
  "id": "2025102601",
  "title": "Article Title",
  "title_zh": "中文标题",
  "summary": "Summary text...",
  "summary_zh": "中文摘要...",
  "keyword": [
    {
      "word": "democracy",
      "definition": "A system of government...",
      "chinese": "民主",
      "pronunciation": "mín zhǔ"
    }
  ],
  "quiz": [
    {
      "question": "What is the main topic?",
      "options": ["A", "B", "C", "D"],
      "correct": 0,
      "explanation": "The answer is A because..."
    }
  ],
  "perspective": [...],
  "ground": [...]
}
```

---

## Database Tables Used

### Main Page Payloads
- `articles` - Article metadata (title, source, category)
- `article_images` - Image locations
- Deepseek response files in `website/article_response/`

### Article Page Payloads
- `articles` - Article metadata
- `article_images` - Image locations  
- `article_summaries` - Easy/middle/high summaries
- `article_keywords` - Vocabulary with definitions
- `article_quizzes` - Quiz questions and answers
- `article_perspectives` - Different viewpoints
- `article_ground_rules` - Ground rules and context
- `deepseek_feedback` - Payload generation tracking

---

## Troubleshooting

### Payloads not updating on website

**Solution:** Check if `payloads_latest` symlink points to newest directory
```bash
ls -la website/main/payloads_latest
```

### Missing articles in payload

**Check:**
1. Article exists in database: `sqlite3 articles.db "SELECT id, title FROM articles;"`
2. Deepseek response exists: `ls website/article_response/response_<articleid>.json`
3. Article has all difficulty levels in database

### Archive dates not showing
```

**Check:**
1. `archive_available_dates.json` exists in payload directory
2. Payload directory timestamps match expected dates
3. Run `mainpayload_generate.py` to regenerate archive index

---

## Notes

- **No HTML Regeneration:** These scripts only generate JSON payloads
- **HTML Templates:** Backed up in `webback/` directory (index.html, archive.html, article.html)
- **Old Generators:** Moved to `unused/genweb/` and `unused/genpage/` (for reference only)
- **Symlink:** `payloads_latest` always points to newest payload directory for consistent URLs

---

**Last Updated:** October 26, 2025
