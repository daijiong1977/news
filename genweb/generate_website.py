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
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'articles.db')
RESPONSES_DIR = os.path.join(BASE_DIR, 'website', 'responses')
IMAGES_DIR = os.path.join(BASE_DIR, 'website', 'article_image')
OUTPUT_DIR = os.path.join(BASE_DIR, 'website', 'generated')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'website', 'main', 'main_template.html')

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

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
        """Get image path for an article."""
        try:
            for img_file in Path(self.images_dir).glob(f'article_{article_id}_*.jpg'):
                return str(img_file)
            return None
        except Exception as e:
            print(f"⚠️  Error finding image for {article_id}: {e}", file=sys.stderr)
            return None
    
    def get_articles_by_category(self, category_id: int, limit: int = 6) -> List[Dict]:
        """Get articles by category_id, randomly pick 6 if more than 6 available."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get all processed articles in category
            cur.execute("""
                SELECT id, title, description, source, 
                       deepseek_processed, crawled_at, processed_at, zh_title
                FROM articles 
                WHERE deepseek_processed = 1 AND category_id = ?
                ORDER BY processed_at DESC
            """, (category_id,))
            
            all_articles = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            # Randomly pick 6 if more than 6
            if len(all_articles) > limit:
                articles = random.sample(all_articles, limit)
                # Re-sort by processed_at after random selection
                articles.sort(key=lambda x: x['processed_at'], reverse=True)
            else:
                articles = all_articles
            
            # Enrich with response data and images
            for article in articles:
                article['response'] = self.get_response_data(article['id'])
                article['image'] = self.get_article_image(article['id'])
            
            return articles
        except Exception as e:
            print(f"❌ Error loading articles by category: {e}", file=sys.stderr)
            return []
    
    def extract_content(self, response: Dict, level: str = 'easy') -> tuple:
        """Extract title and summary from response based on difficulty level.
        
        Returns: (title, summary)
        """
        if not response or 'article_analysis' not in response:
            return '', ''
        
        levels = response.get('article_analysis', {}).get('levels', {})
        
        if level in levels:
            content = levels[level]
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
        cn_data = levels.get('cn', {})
        
        title_zh = cn_data.get('title', '')
        summary_zh = cn_data.get('summary', '')
        
        return title_zh, summary_zh


class HTMLGenerator:
    """Generate HTML article cards with difficulty levels."""
    
    @staticmethod
    def generate_article_card(article: Dict, level: str = 'easy') -> str:
        """Generate HTML for a single article card with difficulty level content."""
        article_id = article['id']
        source = article.get('source', 'News Source')
        image_url = article.get('image', '')
        response = article.get('response', {})
        processed_at = article.get('processed_at', '')
        
        # Time formatting
        try:
            if processed_at:
                dt = datetime.fromisoformat(processed_at)
                hours_ago = (datetime.now() - dt).total_seconds() // 3600
                time_ago = f"{int(hours_ago)} hours ago" if hours_ago > 0 else "Just now"
            else:
                time_ago = "Recently"
        except:
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
        
        # Shorten summaries
        summary_short = (summary_level[:100] + "...") if len(summary_level) > 100 else summary_level
        summary_cn_short = (summary_cn[:100] + "...") if len(summary_cn) > 100 else summary_cn
        
        # Image styling
        image_style = f'background-image: url("file://{image_url}");' if image_url else 'background-color: #e4e4e7;'
        
        return f'''<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{article_id}" data-level="{level}" data-title-en="{title_level}" data-title-zh="{title_cn}" data-summary-en="{summary_short}" data-summary-zh="{summary_cn_short}">
<div class="w-full bg-center bg-no-repeat aspect-video bg-cover" style='{image_style}'></div>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{title_level}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{time_ago}</p>
<span class="font-bold">·</span>
<p>{source}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed flex-grow article-summary">{summary_short}</p>
<button class="mt-auto flex w-full items-center justify-center rounded-md h-10 px-4 bg-primary/20 text-primary text-sm font-bold leading-normal tracking-wide hover:bg-primary/30 transition-colors">
<span class="truncate">Read More</span>
</button>
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
        articles = loader.get_articles_by_category(cat_id, limit=6)
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
                cards = [HTMLGenerator.generate_article_card(article, level_key) for article in cat_articles]
                all_cards.extend(cards)
        
        cards_by_level[level_key] = "\n".join(all_cards)
        level_display = DIFFICULTY_MAPPING.get(level_key, level_key)
        print(f"  - {level_display} ({level_key}): {len(all_cards)} cards")
    
    # Start with 'easy' (Relax) as default
    default_cards = cards_by_level['easy']
    
    # Replace the grid content in template
    pattern = r'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">(.*?)</div>\s*</main>'
    replacement = f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">\n{default_cards}\n</div>\n</main>'
    output_html = re.sub(pattern, replacement, template, flags=re.DOTALL, count=1)
    
    # Add comprehensive script for difficulty level switching and language toggle
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

let currentLanguage = 'en';
let currentLevel = 'easy';

document.addEventListener('DOMContentLoaded', function() {
    // Difficulty level dropdown handler
    const dropdown = document.querySelector('select');
    if (dropdown) {
        dropdown.addEventListener('change', function() {
            const selectedText = this.options[this.selectedIndex].text;
            let levelKey = levelMapping[selectedText] || 'easy';
            
            // Special case for CN
            if (this.value === 'CN' || selectedText.includes('CN')) {
                levelKey = 'cn';
            }
            
            currentLevel = levelKey;
            updateCards();
        });
    }
    
    // CN button for language toggle
    let cnButton = null;
    document.querySelectorAll('button').forEach(btn => {
        if (btn.textContent.trim() === 'CN') {
            cnButton = btn;
        }
    });
    
    if (cnButton) {
        cnButton.addEventListener('click', function(e) {
            e.preventDefault();
            currentLanguage = currentLanguage === 'en' ? 'zh' : 'en';
            updateCards();
            cnButton.textContent = currentLanguage === 'zh' ? 'EN' : 'CN';
        });
    }
});

function updateCards() {
    const gridDiv = document.querySelector('.grid');
    if (!gridDiv || !levelCards[currentLevel]) return;
    
    // Parse and update cards
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = levelCards[currentLevel];
    
    const cards = tempDiv.querySelectorAll('[data-article-id]');
    
    // Update visible content based on current language
    cards.forEach(card => {
        const titleEl = card.querySelector('.article-title');
        const summaryEl = card.querySelector('.article-summary');
        
        if (titleEl) {
            const titleEn = card.dataset.titleEn;
            const titleZh = card.dataset.titleZh;
            titleEl.textContent = currentLanguage === 'zh' ? (titleZh || titleEn) : titleEn;
        }
        
        if (summaryEl) {
            const summaryEn = card.dataset.summaryEn;
            const summaryZh = card.dataset.summaryZh;
            summaryEl.textContent = currentLanguage === 'zh' ? (summaryZh || summaryEn) : summaryEn;
        }
    });
    
    // Replace grid content
    const newGridContent = tempDiv.innerHTML;
    gridDiv.innerHTML = newGridContent;
}
</script>
    '''
    
    # Inject script before closing body
    output_html = output_html.replace('</body>', f'{script}\n</body>')
    
    # Write output
    print("\n✍️  Writing HTML...")
    output_file = os.path.join(OUTPUT_DIR, 'index.html')
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f"  ✓ Written to: {output_file}")
    except Exception as e:
        print(f"❌ Error writing HTML: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ Website Generation Complete!")
    print("=" * 70)
    print(f"\n📍 Output: {output_file}")
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
