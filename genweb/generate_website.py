#!/usr/bin/env python3
"""
Website Generator - Injects article cards with difficulty levels.
- Random pickup of latest 6 articles per category (if > 6)
- Dropdown levels: Relax (easy) / Enjoy (mid) / Research (hard)
- Content sourced from Deepseek response JSON by difficulty level
- CN content from CN block in response
"""

import json
import sqlite3
import os
import sys
import re
import random
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'articles.db')
RESPONSES_DIR = os.path.join(BASE_DIR, 'website', 'responses')
IMAGES_DIR = os.path.join(BASE_DIR, 'website', 'article_image')
OUTPUT_DIR = os.path.join(BASE_DIR, 'website', 'generated')
MAIN_DIR = os.path.join(BASE_DIR, 'website', 'main')
WEBSITE_DIR = os.path.join(BASE_DIR, 'website')
GENWEB_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(GENWEB_DIR, 'main_template.html')

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(MAIN_DIR).mkdir(parents=True, exist_ok=True)
Path(WEBSITE_DIR).mkdir(parents=True, exist_ok=True)

# Difficulty level mapping
DIFFICULTY_MAPPING = {
    'easy': 'Relax',
    'mid': 'Enjoy',
    'hard': 'Research'
}


class ArticleLoader:
    """Load articles from database and response files."""
    
    def __init__(self, db_path, responses_dir, images_dir):
        self.db_path = db_path
        self.responses_dir = responses_dir
        self.images_dir = images_dir
    
    def get_response_data(self, article_id) -> Optional[Dict]:
        """Load response JSON for an article."""
        try:
            response_file = os.path.join(
                self.responses_dir, 
                f'article_{article_id}_response.json'
            )
            
            if not os.path.exists(response_file):
                return None
            
            with open(response_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading response for {article_id}: {e}", file=sys.stderr)
            return None
    
    def get_article_image(self, article_id) -> Optional[str]:
        """Get optimized _mobile.webp image for an article (1024×768, <60KB)."""
        try:
            # Look for _mobile.webp version (optimized, 1024×768, <60KB)
            for img_file in Path(self.images_dir).glob(f'article_{article_id}_*_mobile.webp'):
                return f"../article_image/{img_file.name}"
            
            # Fallback to original jpg if _mobile.webp not found
            for img_file in Path(self.images_dir).glob(f'article_{article_id}_*.jpg'):
                if '_mobile' not in img_file.name:
                    return f"../article_image/{img_file.name}"
            
            # Fallback to any webp without _mobile
            for img_file in Path(self.images_dir).glob(f'article_{article_id}_*.webp'):
                if '_mobile' not in img_file.name:
                    return f"../article_image/{img_file.name}"
            
            return None
        except Exception as e:
            print(f"⚠️  Error finding image for {article_id}: {e}", file=sys.stderr)
            return None
    
    def get_articles_by_category(self, category_id: int, per_source_limit: int = 3) -> List[Dict]:
        """Get latest 3 articles from each source in a category (balanced source representation)."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get all unique sources in this category
            cur.execute("""
                SELECT DISTINCT source FROM articles 
                WHERE deepseek_processed = 1 AND category_id = ?
                ORDER BY source
            """, (category_id,))
            
            sources = [row['source'] for row in cur.fetchall()]
            all_articles = []
            
            # For each source, get latest N articles
            for source in sources:
                cur.execute("""
                    SELECT id, title, description, source, 
                           deepseek_processed, crawled_at, processed_at, zh_title, pub_date
                    FROM articles 
                    WHERE deepseek_processed = 1 AND category_id = ? AND source = ?
                    ORDER BY pub_date DESC
                    LIMIT ?
                """, (category_id, source, per_source_limit))
                
                articles = [dict(row) for row in cur.fetchall()]
                all_articles.extend(articles)
            
            conn.close()
            
            # Re-sort by pub_date DESC to get chronological order
            all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
            
            # Enrich with response data and images
            for article in all_articles:
                article['response'] = self.get_response_data(article['id'])
                article['image'] = self.get_article_image(article['id'])
            
            return all_articles
        except Exception as e:
            print(f"❌ Error loading articles by category: {e}", file=sys.stderr)
            return []
    
    def extract_content(self, response: Dict, level: str = 'easy') -> tuple:
        """Extract title and summary from response based on difficulty level.
        
        Returns: (title, summary)
        """
        if not response or 'article_analysis' not in response:
            return '', ''
        
        # Map our level names to the actual keys in the response
        level_map = {
            'easy': 'easy',
            'mid': 'middle',
            'hard': 'high',
            'cn': 'zh'
        }
        
        response_level = level_map.get(level, level)
        levels = response.get('article_analysis', {}).get('levels', {})
        
        if response_level in levels:
            content = levels[response_level]
            title = content.get('title', '')
            summary = content.get('summary', '')
            return title, summary
        
        return '', ''
    
    def extract_cn_content(self, response: Dict) -> tuple:
        """Extract Chinese title and summary from CN block in response.
        
        Returns: (title_zh, summary_zh)
        """
        if not response or 'article_analysis' not in response:
            return '', ''
        
        levels = response.get('article_analysis', {}).get('levels', {})
        cn_data = levels.get('zh', {})
        
        title_zh = cn_data.get('title', '')
        summary_zh = cn_data.get('summary', '')
        
        return title_zh, summary_zh


class HTMLGenerator:
    """Generate HTML article cards with difficulty levels."""
    
    @staticmethod
    def generate_article_card(article: Dict, level: str = 'easy', category: str = '') -> str:
        """Generate HTML for a single article card with difficulty level content."""
        article_id = article['id']
        source = article.get('source', 'News Source')
        image_url = article.get('image', '')
        response = article.get('response', {})
        # Use pub_date (original article publication date)
        pub_date = article.get('pub_date', '')
        
        # Time formatting - use pub_date (RFC 2822 format)
        try:
            if pub_date:
                # Parse RFC 2822 format: "Fri, 24 Oct 2025 08:46:37 GMT"
                dt = parsedate_to_datetime(pub_date.strip())
                hours_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() // 3600
                if hours_ago > 0:
                    if hours_ago == 1:
                        time_ago = "1 hour ago"
                    elif hours_ago < 24:
                        time_ago = f"{int(hours_ago)} hours ago"
                    else:
                        days_ago = hours_ago // 24
                        time_ago = f"{int(days_ago)} days ago" if days_ago > 1 else "1 day ago"
                else:
                    time_ago = "Just now"
            else:
                time_ago = "Recently"
        except Exception as e:
            print(f"⚠️  Error parsing date '{pub_date}': {e}", file=sys.stderr)
            time_ago = "Recently"
        
        # Extract content by difficulty level
        loader = ArticleLoader(None, None, None)
        title_level, summary_level = loader.extract_content(response, level)
        title_cn, summary_cn = loader.extract_cn_content(response)
        
        # Fallback to original if not found
        if not title_level:
            title_level = article.get('title', '')
        if not summary_level:
            summary_level = article.get('description', '')[:100]
        
        # Shorten summaries for data attributes (for backward compatibility)
        summary_short = (summary_level[:500] + "...") if len(summary_level) > 500 else summary_level
        summary_cn_short = (summary_cn[:500] + "...") if len(summary_cn) > 500 else summary_cn
        
        # ALSO extract content for ALL levels (for switching)
        level_data = {}
        for lv in ['easy', 'mid', 'hard']:
            title, summary = loader.extract_content(response, lv)
            if not title:
                title = article.get('title', '')
            if not summary:
                summary = article.get('description', '')[:500]
            level_data[lv] = {
                'title': title,
                'summary': summary  # Store FULL summary, no truncation
            }
        # Add CN data
        level_data['cn'] = {
            'title': title_cn,
            'summary': summary_cn  # Store FULL summary, no truncation
        }
        
        # Build data attributes for all levels
        level_attrs = ''
        for lv, data in level_data.items():
            # Escape quotes for HTML attributes
            escaped_title = data['title'].replace('"', '&quot;').replace("'", "&#39;")
            escaped_summary = data['summary'].replace('"', '&quot;').replace("'", "&#39;")
            level_attrs += f' data-title-{lv}="{escaped_title}" data-summary-{lv}="{escaped_summary}"'
        
        # Image styling - use relative path or background color
        if image_url:
            # Use relative path without file:// prefix for HTTP compatibility
            image_style = f'background-image: url("{image_url}");'
        else:
            image_style = 'background-color: #e4e4e7;'
        
        return f'''<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{article_id}" data-category="{category}" data-level="{level}"{level_attrs}>
<div class="w-full bg-center bg-no-repeat aspect-video bg-cover" style='{image_style}'></div>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{title_level}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{time_ago}</p>
<span class="font-bold">·</span>
<p>{source}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed article-summary" style="overflow-wrap: break-word; word-break: break-word;">{summary_level}</p>
</div>
</div>'''


def generate_website():
    """Generate website with difficulty level filtering."""
    print("\n" + "=" * 70)
    print("🌐 GENERATING WEBSITE WITH DIFFICULTY LEVELS")
    print("=" * 70 + "\n")
    
    print("📚 Loading articles...")
    loader = ArticleLoader(DB_PATH, RESPONSES_DIR, IMAGES_DIR)
    
    # Get categories with processed articles in correct order
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT c.category_id, c.category_name
        FROM categories c
        INNER JOIN articles a ON a.category_id = c.category_id
        WHERE a.deepseek_processed = 1
        ORDER BY c.category_id ASC
    """)
    
    categories = [(row[0], row[1]) for row in cur.fetchall()]
    conn.close()
    
    if not categories:
        print("❌ No categories with processed articles found")
        return False
    
    print(f"✓ Found {len(categories)} categories:")
    articles_by_category = {}
    total_articles = 0
    
    for cat_id, cat_name in categories:
        articles = loader.get_articles_by_category(cat_id, per_source_limit=3)
        articles_by_category[cat_name] = articles
        total_articles += len(articles)
        print(f"  - {cat_name} (ID: {cat_id}): {len(articles)} articles")
    
    # Read template
    print("\n📖 Reading template...")
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False
    
    # Generate article cards for all difficulty levels
    print("\n🎨 Generating article cards...")
    
    # Create cards for each difficulty level
    cards_by_level = {}
    for level_key in ['easy', 'mid', 'hard', 'cn']:
        all_cards = []
        
        # Order: News, Science, Fun
        for cat_name in ['News', 'Science', 'Fun']:
            cat_articles = articles_by_category.get(cat_name, [])
            if cat_articles:
                cards = [HTMLGenerator.generate_article_card(article, level_key, cat_name) for article in cat_articles]
                all_cards.extend(cards)
        
        cards_by_level[level_key] = "\n".join(all_cards)
        level_display = DIFFICULTY_MAPPING.get(level_key, level_key)
        print(f"  - {level_display} ({level_key}): {len(all_cards)} cards")
    
    # Start with 'mid' (Enjoy) as default
    default_cards = cards_by_level['mid']
    
    # Replace the grid content in template
    pattern = r'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">(.*?)</div>\s*</main>'
    replacement = f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">\n{default_cards}\n</div>\n</main>'
    output_html = re.sub(pattern, replacement, template, flags=re.DOTALL, count=1)
    
    # Add comprehensive script for difficulty level switching, tab navigation, and language toggle
    script = '''
<script>
const levelCards = {
    'easy': `''' + cards_by_level['easy'].replace('`', '\\`') + '''`,
    'mid': `''' + cards_by_level['mid'].replace('`', '\\`') + '''`,
    'hard': `''' + cards_by_level['hard'].replace('`', '\\`') + '''`,
    'cn': `''' + cards_by_level['cn'].replace('`', '\\`') + '''`
};

const levelMapping = {
    'Relax': 'easy',
    'Enjoy': 'mid',
    'Research': 'hard'
};

const categoryMap = {
    'News': 1,
    'Science': 2,
    'Fun': 3
};

let currentLanguage = 'en';
let currentLevel = 'easy';
let currentCategory = 'News';

// Read URL parameters on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check for level parameter in URL
    const params = new URLSearchParams(window.location.search);
    const urlLevel = params.get('level');
    if (urlLevel && ['easy', 'mid', 'hard', 'cn'].includes(urlLevel)) {
        currentLevel = urlLevel;
        // Update dropdown to match URL level
        const dropdown = document.querySelector('select');
        if (dropdown) {
            const levelMap = {
                'easy': 'Relax',
                'mid': 'Enjoy',
                'hard': 'Research',
                'cn': 'CN'
            };
            dropdown.value = levelMap[urlLevel] || 'Enjoy';
        }
        // Update CN button state
        const cnButton = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.trim() === 'CN');
        if (cnButton && urlLevel === 'cn') {
            cnButton.classList.add('bg-primary', 'text-white');
            cnButton.classList.remove('bg-subtle-light', 'text-subtle-light', 'dark:bg-subtle-dark', 'dark:text-subtle-dark');
        }
        filterAndUpdateCards();
    }
    
    // Tab navigation for News/Science/Fun
    const tabLinks = document.querySelectorAll('a[href="#"]');
    tabLinks.forEach((link, index) => {
        const tabText = link.textContent.trim();
        if (tabText === 'News' || tabText === 'Science' || tabText === 'Fun') {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Update active tab styling
                tabLinks.forEach(tl => {
                    tl.classList.remove('border-b-primary', 'text-primary');
                    tl.classList.add('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
                });
                this.classList.add('border-b-primary', 'text-primary');
                this.classList.remove('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
                
                // Update current category
                currentCategory = tabText;
                filterAndUpdateCards();
            });
        }
    });
    
    // Difficulty level dropdown handler
    const dropdown = document.querySelector('select');
    if (dropdown) {
        dropdown.addEventListener('change', function() {
            const selectedText = this.options[this.selectedIndex].text;
            let levelKey = levelMapping[selectedText] || 'mid';
            
            // Special case for CN
            if (this.value === 'CN' || selectedText.includes('CN')) {
                levelKey = 'cn';
                // Hide dropdown when CN is selected
                dropdown.style.display = 'none';
            } else {
                // Show dropdown for other selections
                dropdown.style.display = '';
            }
            
            currentLevel = levelKey;
            
            // Update URL with current level
            updateURLParameter('level', currentLevel);
            
            filterAndUpdateCards();
        });
    }
    
    // CN button for language toggle - find by looking at header buttons (3rd one)
    let cnButton = null;
    const headerButtons = document.querySelectorAll('header button');
    if (headerButtons.length >= 3) {
        cnButton = headerButtons[2]; // The CN button is the 3rd button in header
    }
    
    if (cnButton) {
        cnButton.addEventListener('click', function(e) {
            console.log('CN Button clicked, currentLanguage:', currentLanguage);
            
            if (currentLanguage === 'en') {
                // Switch to Chinese - show CN dropdown selection
                currentLanguage = 'zh';
                currentLevel = 'cn';
                
                // Hide the dropdown when in CN mode
                if (dropdown) dropdown.style.display = 'none';
                
                // Update button text
                const spanEl = cnButton.querySelector('span.truncate');
                if (spanEl) {
                    spanEl.textContent = 'EN';
                } else {
                    cnButton.textContent = 'EN';
                }
                console.log('Switched to Chinese (CN)');
            } else {
                // Switch back to English
                currentLanguage = 'en';
                currentLevel = 'easy';
                
                // Show dropdown again
                if (dropdown) dropdown.style.display = '';
                
                // Update button text
                const spanEl = cnButton.querySelector('span.truncate');
                if (spanEl) {
                    spanEl.textContent = 'CN';
                } else {
                    cnButton.textContent = 'CN';
                }
                console.log('Switched back to English (EN)');
            }
            
            // Update URL with current level
            updateURLParameter('level', currentLevel);
            
            filterAndUpdateCards();
        });
    } else {
        console.log('CN Button not found');
    }
    
    // Initialize first tab as active
    if (tabLinks.length > 0) {
        for (let link of tabLinks) {
            if (link.textContent.trim() === 'News') {
                link.click();
                break;
            }
        }
    }
    
    // Add Read More button click handler
    document.addEventListener('click', function(e) {
        if (e.target.closest('button[data-article-id]')) {
            const button = e.target.closest('button[data-article-id]');
            const articleId = button.dataset.articleId;
            const level = button.dataset.level;
            
            // Store the current level and redirect to article detail page
            // URL format: article.html?id=ARTICLE_ID&level=LEVEL
            const url = `article.html?id=${articleId}&level=${level}`;
            console.log('Read More clicked:', {articleId, level, url});
            // window.location.href = url; // Uncomment when article detail page is ready
        }
    });
});

function updateURLParameter(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.replaceState({}, document.title, url);
}

function filterAndUpdateCards() {
    const gridDiv = document.querySelector('.grid');
    if (!gridDiv || !levelCards[currentLevel]) return;
    
    // Get all cards from the current level
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = levelCards[currentLevel];
    let cards = Array.from(tempDiv.querySelectorAll('[data-article-id]'));
    
    // Filter by category if not 'all'
    if (currentCategory !== 'all') {
        cards = cards.filter(card => card.dataset.category === currentCategory);
    }
    
    // Replace grid content with filtered cards
    // The HTML from levelCards already has the correct titles/summaries baked in
    const newGridContent = cards.map(card => card.outerHTML).join('\\n');
    gridDiv.innerHTML = newGridContent;
    
    // Update title and summary from data attributes to show full content
    gridDiv.querySelectorAll('[data-article-id]').forEach(card => {
        // Update title
        const titleAttr = `data-title-${currentLevel}`;
        const title = card.getAttribute(titleAttr);
        if (title) {
            const titleEl = card.querySelector('.article-title');
            if (titleEl) titleEl.textContent = title;
        }
        
        // Update summary
        const summaryAttr = `data-summary-${currentLevel}`;
        const summary = card.getAttribute(summaryAttr);
        if (summary) {
            const summaryEl = card.querySelector('.article-summary');
            if (summaryEl) {
                summaryEl.textContent = summary;
                // Remove any max-height or line-clamp restrictions for full display
                summaryEl.style.maxHeight = 'none';
                summaryEl.style.overflow = 'visible';
                summaryEl.classList.remove('line-clamp-3');
            }
        }
    });
}
</script>
    '''
    
    # Inject script before closing body
    output_html = output_html.replace('</body>', f'{script}\n</body>')
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_file = os.path.join(MAIN_DIR, f'index_{timestamp}.html')
    main_index_file = os.path.join(MAIN_DIR, 'index.html')
    generated_index_file = os.path.join(OUTPUT_DIR, 'index.html')
    
    # Write timestamped version (archive)
    print("\n✍️  Writing HTML...")
    try:
        with open(timestamped_file, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f"  ✓ Timestamped archive: {timestamped_file}")
    except Exception as e:
        print(f"❌ Error writing timestamped file: {e}")
        return False
    
    # Check if we should update website/main/index.html (main location)
    should_update_main = True
    if os.path.exists(main_index_file):
        main_mtime = os.path.getmtime(main_index_file)
        timestamped_mtime = os.path.getmtime(timestamped_file)
        if timestamped_mtime <= main_mtime:
            should_update_main = False
            print(f"  ℹ️  Existing website/main/index.html is newer, keeping it")
    
    if should_update_main:
        try:
            with open(main_index_file, 'w', encoding='utf-8') as f:
                f.write(output_html)
            print(f"  ✓ Updated main: {main_index_file}")
        except Exception as e:
            print(f"❌ Error updating main index: {e}")
            return False
    
    # Also update website/generated/index.html for backward compatibility
    try:
        with open(generated_index_file, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f"  ✓ Updated generated: {generated_index_file}")
    except Exception as e:
        print(f"❌ Error writing generated file: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ Website Generation Complete!")
    print("=" * 70)
    print(f"\n📍 Output:")
    print(f"   - Main: {main_index_file}")
    print(f"   - Archive: {timestamped_file}")
    print(f"   - Generated: {generated_index_file}")
    print(f"📊 Statistics:")
    print(f"   - Categories: {len(categories)}")
    print(f"   - Total articles: {total_articles} (randomly selected 6 per category if > 6)")
    print(f"\n📋 Dropdown Levels:")
    print(f"   - Relax → Easy level (beginner friendly)")
    print(f"   - Enjoy → Mid level (intermediate)")
    print(f"   - Research → Hard level (in-depth analysis)")
    print(f"\n🌐 Content Source:")
    print(f"   - Titles/Summaries: From Deepseek response JSON")
    print(f"   - Chinese content: From CN block in response")
    print(f"   - Time/Source/Category: From database")
    print(f"\n⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return True


if __name__ == '__main__':
    success = generate_website()
    sys.exit(0 if success else 1)
