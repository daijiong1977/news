# Website Generator (genweb)

Generates the website `index.html` from the article database and response files, with interactive tab navigation and language switching support.

## Features

✓ **Tab Navigation**: News/Science/Fun categories (in correct order)
✓ **Article Filtering**: Clicking tabs shows only articles from that category
✓ **Language Toggle**: CN/EN button switches between English and Chinese content
✓ **Template Preservation**: Keeps original design, styling, and layout
✓ **Smart Data Injection**: Articles injected into single grid with category awareness
✓ **Responsive Design**: All Tailwind CSS classes preserved

## Output

- **File**: `website/generated/index.html`
- **Size**: ~35 KB with 13 articles
- **Categories**: News (4), Science (3), Fun (6)

## How to Run

```bash
cd /Users/jidai/news
python3 genweb/generate_website.py
```

## How It Works

### 1. Article Loading
- Reads `articles.db` for articles marked `deepseek_processed = 1`
- Groups by category (News/Science/Fun)
- Limits to 6 articles per category
- Loads response JSON for summaries and metadata

### 2. Template Injection
- Reads original `website/main/main_template.html`
- Generates article cards with data attributes
- Replaces grid content while preserving structure
- Keeps tabs, buttons, header, footer intact

### 3. Script Addition
- Adds tab switching logic (shows/hides articles by category)
- Adds language toggle for EN/CN
- Stores content in `data-*` attributes for efficient switching

## Article Card Structure

Each article card contains:
```html
<div data-article-id="2025102501" 
     data-title-en="English Title"
     data-title-zh="Chinese Title"
     data-summary-en="English summary..."
     data-summary-zh="Chinese summary...">
```

## Tab Switching Logic

- **Default**: News tab active
- **Click Science**: Shows only Science articles (3)
- **Click Fun**: Shows only Fun articles (6)
- **Click News**: Shows only News articles (4)

## Language Toggle

- **CN Button**: Click to switch to Chinese
  - Updates all visible article titles
  - Updates all visible article summaries
  - Changes button text to "EN"
- **Click again**: Returns to English

## Database Requirements

Articles must have:
- `deepseek_processed = 1` (processed by Deepseek)
- `category_id` (1=News, 2=Science, 3=Fun)
- `zh_title` (Chinese title)
- `processed_at` (timestamp)

Response JSON must have:
- `article_analysis.levels.easy.summary` (English)
- `article_analysis.levels.zh.summary` (Chinese)

## Image Handling

- Looks for article images: `article_{id}_*.jpg`
- Falls back to gray placeholder if not found
- Uses first JPG found for each article

## Customization

### Change article limit per category
```python
articles = loader.get_articles_by_category(cat_id, limit=10)
```

### Change template source
```python
TEMPLATE_PATH = os.path.join(BASE_DIR, 'website', 'main', 'main_template.html')
```

### Modify card HTML
Edit `HTMLGenerator.generate_article_card()` method

## Troubleshooting

- **No articles shown**: Check `deepseek_processed = 1` in database
- **Wrong tab order**: Verify categories in database (ID 1=News, 2=Science, 3=Fun)
- **No Chinese content**: Check response JSON has `levels.zh.summary`
- **Images missing**: Verify file names match `article_{id}_*.jpg` pattern
- **Tabs not working**: Check browser console for JavaScript errors

## Generated Files

```
website/
└── generated/
    └── index.html (34 KB, ~13 articles)
```

## Status

- ✅ Tab navigation working correctly
- ✅ Language toggle functional
- ✅ Template structure preserved
- ✅ All 13 articles loading
- ✅ Article filtering by category
- ✅ Chinese/English content switching

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
