# Enhanced Website Generator - Documentation

## Overview

`enhance_generate.py` is an optimized alternative to `generate_website.py` that dramatically reduces initial page load size by using dynamic payload loading instead of embedding all article content in a single HTML file.

## Problem Solved

**Original approach (generate_website.py):**
- Single monolithic HTML file with all 4 difficulty levels embedded
- File size: ~593KB
- All content loads upfront, even for unused difficulty levels
- Slower initial page render

**Enhanced approach (enhance_generate.py):**
- Lightweight main HTML with default difficulty level
- Separate JSON payload files for each difficulty level
- Main HTML: 50.2KB (92% reduction!)
- Payloads loaded on-demand when user changes difficulty
- Faster initial page load, better perceived performance

## Architecture

```
website/main/
├── index.html                          (50.2KB - lightweight default page)
│   └── Uses fetch() to load payloads dynamically
├── payloads/
│   ├── articles_easy.json              (18.5KB - Relax level)
│   ├── articles_mid.json               (27.6KB - Enjoy level, preloaded)
│   ├── articles_hard.json              (36.7KB - Research level)
│   └── articles_cn.json                (28.3KB - CN level)
└── article_image/
    └── (WebP images - lazy-loaded when rendered)

Total footprint:
├── Initial page load: 50.2KB
├── Additional payloads: 111.2KB (lazy-loaded)
└── Total with all payloads: 161.4KB (73% reduction from 593KB)
```

## How It Works

### 1. Page Load (50.2KB)
- User visits news.6ray.com
- `index.html` loads with default "Enjoy" (mid-level) articles
- Embedded JavaScript provides dynamic loading capability

### 2. User Changes Difficulty Level
- User clicks difficulty dropdown (Relax, Enjoy, Research, CN)
- JavaScript `loadArticles(levelName)` function triggers
- Fetches corresponding `articles_<level>.json` from `/payloads/` directory

### 3. Dynamic Rendering
```javascript
fetch('./payloads/articles_mid.json')
  .then(response => response.json())
  .then(data => {
    // Render articles from JSON data
    grid.innerHTML = renderArticleCards(data.articles);
  });
```

### 4. Benefits
- ✅ Faster initial page load (92% smaller)
- ✅ Smooth UX - no page reload when changing difficulty
- ✅ Lazy loading - only fetch what user needs
- ✅ Images lazy-load via CSS `background-image` property
- ✅ All 4 levels still fully available

## Usage

### Run Enhanced Generator

```bash
cd /Users/jidai/news
python3 genweb/enhance_generate.py
```

### Output

```
======================================================================
🚀 ENHANCED WEBSITE GENERATOR - DYNAMIC PAYLOAD LOADING
======================================================================

📚 Loading articles...
✓ Found 3 categories:
  - News (ID: 1): 6 articles
  - Science (ID: 2): 6 articles
  - Fun (ID: 3): 6 articles

📦 Generating JSON payloads...
  ✓ Relax (easy): 18 articles, 18.5KB
  ✓ Enjoy (mid): 18 articles, 27.6KB
  ✓ Research (hard): 18 articles, 36.7KB
  ✓ cn (cn): 18 articles, 28.3KB
  Total payload size: 111.2KB

📄 Main HTML (/Users/jidai/news/website/main/)
  - index.html: 50.2KB (includes default Enjoy level)
  - Reduction: ~542.8KB saved vs monolithic (92% smaller)
```

## Generated Files

### index.html
- Lightweight HTML with embedded CSS and JavaScript
- Contains default difficulty level articles (Enjoy/mid)
- Includes `loadArticles()` function for dynamic switching
- Automatically loads payloads when dropdown changes

### articles_easy.json
```json
{
  "articles": [
    {
      "id": "2025102504",
      "title": "Article Title (Easy version)",
      "summary": "Simplified summary for Relax level...",
      "source": "BBC News",
      "time_ago": "13 hours ago",
      "image_url": "../article_image/article_2025102504_mobile.webp",
      "category": "News"
    },
    ...
  ]
}
```

Same structure for `articles_mid.json`, `articles_hard.json`, and `articles_cn.json`.

## Integration with EC2

### Deploy to EC2

```bash
# On EC2
cd /var/www/news
git pull origin main
python3 genweb/enhance_generate.py

# Verify files
ls -lh website/main/
ls -lh website/main/payloads/
```

### Nginx Configuration (Already Configured)

The existing Nginx config already serves:
- Main HTML: `/var/www/news/website/main/index.html`
- Payloads: `/var/www/news/website/main/payloads/*.json`
- Images: `/var/www/news/website/article_image/*.webp`

No additional Nginx changes needed!

## Comparison

| Metric | Original | Enhanced |
|--------|----------|----------|
| Initial HTML | 593KB | 50.2KB |
| With all payloads | 593KB | 161.4KB |
| Reduction | - | **92%** |
| Page load time | Slower | Much faster |
| UX when switching difficulty | Reload page | Instant (no reload) |
| User sees default level | Yes (Enjoy) | Yes (Enjoy) |

## Important Notes

### ✅ Keep Both Generators
- **generate_website.py**: Original monolithic approach (still works)
- **enhance_generate.py**: New optimized approach
- No need to replace - can use either as needed

### ✅ Same Database Source
Both generators read from:
- `articles.db` - article metadata
- `website/responses/` - Deepseek responses (difficulty levels)
- `website/article_image/` - WebP images

### ✅ Same Article Selection
- 3 articles per source per category
- Balanced representation across sources
- Latest articles first

### ✅ Dynamic Loading JavaScript
The embedded script includes:
- `loadArticles(levelName)` - Main loading function
- `levelMap` - Maps display names to file keys
- HTML escaping for security
- Error handling with console logging

### ⚠️ Browser Requirements
- Requires JavaScript enabled
- Uses `fetch()` API (all modern browsers)
- Fallback: Users can manually refresh page if needed

## Troubleshooting

### Issue: Payloads not loading
- Verify payload files exist: `ls -la website/main/payloads/`
- Check browser console for fetch errors
- Verify relative path: `./payloads/articles_*.json`

### Issue: Images not showing
- Verify image files exist: `ls -la website/article_image/`
- Check CSS `background-image` property in browser dev tools
- Images use `../article_image/` relative path

### Issue: Styling broken
- Ensure Tailwind CDN is still linked in HTML
- Check browser console for CSS errors
- Verify no CSS conflicts with dynamic loading

## Future Enhancements

1. **Preload popular payloads**: Use `<link rel="prefetch">` for Enjoy/mid
2. **Service Worker caching**: Cache payloads locally for offline access
3. **Compression**: Gzip payloads server-side for 50%+ size reduction
4. **Pagination**: Split each level into multiple paginated payloads
5. **Real-time updates**: Use WebSocket to push new articles
6. **Content versioning**: Add ETag/hash to detect payload updates

## Files Modified/Created

- ✅ `/Users/jidai/news/genweb/enhance_generate.py` - New enhanced generator
- ✅ `/Users/jidai/news/website/main/index.html` - Generated lightweight HTML
- ✅ `/Users/jidai/news/website/main/payloads/articles_*.json` - Generated payloads

## Stats

- **Development time**: Done ✓
- **Testing**: Local verified ✓
- **Production ready**: Yes ✓
- **Backward compatible**: Yes (original generator still works)

---

Generated: 2025-10-25 21:29:35
