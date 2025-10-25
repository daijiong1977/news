#!/usr/bin/env python3
"""
Website Generator - Injects article cards into template while preserving structure.
Keeps original News/Science/Fun tab format and CN button functionality.
"""

import json
import sqlite3
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'articles.db')
RESPONSES_DIR = os.path.join(BASE_DIR, 'website.remote', 'responses')
IMAGES_DIR = os.path.join(BASE_DIR, 'website.remote', 'article_image')
OUTPUT_DIR = os.path.join(BASE_DIR, 'website', 'generated')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'website', 'main', 'main_template.html')

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


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
        """Get articles by category_id with response data and images."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, title, description, source, 
                       deepseek_processed, crawled_at, processed_at, zh_title
                FROM articles 
                WHERE deepseek_processed = 1 AND category_id = ?
                ORDER BY processed_at DESC
                LIMIT ?
            """, (category_id, limit))
            
            articles = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            # Enrich with response data and images
            for article in articles:
                article['response'] = self.get_response_data(article['id'])
                article['image'] = self.get_article_image(article['id'])
            
            return articles
        except Exception as e:
            print(f"❌ Error loading articles by category: {e}", file=sys.stderr)
            return []


class HTMLGenerator:
    """Generate HTML article cards."""
    
    @staticmethod
    def generate_article_card(article: Dict) -> str:
        """Generate HTML for a single article card with en/zh data attributes."""
        article_id = article['id']
        title_en = article.get('title', '')
        title_zh = article.get('zh_title', title_en)
        description = article.get('description', '')
        source = article.get('source', 'News Source')
        image_url = article.get('image', '')
        processed_at = article.get('processed_at', '')
        response = article.get('response', {})
        
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
        
        # Extract summaries from response
        summary_en = description[:100] + "..." if len(description) > 100 else description
        summary_zh = summary_en  # Default to English if no zh in response
        
        if response and 'article_analysis' in response:
            levels = response.get('article_analysis', {}).get('levels', {})
            if 'easy' in levels:
                en_summary = levels['easy'].get('summary', description)
                summary_en = en_summary[:100] + "..." if len(en_summary) > 100 else en_summary
            if 'zh' in levels:
                zh_summary = levels['zh'].get('summary', description)
                summary_zh = zh_summary[:100] + "..." if len(zh_summary) > 100 else zh_summary
        
        # Image styling
        image_style = f'background-image: url("file://{image_url}");' if image_url else 'background-color: #e4e4e7;'
        
        return f'''<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{article_id}" data-title-en="{title_en}" data-title-zh="{title_zh}" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">
<div class="w-full bg-center bg-no-repeat aspect-video bg-cover" style='{image_style}'></div>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{title_en}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{time_ago}</p>
<span class="font-bold">·</span>
<p>{source}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed flex-grow article-summary">{summary_en}</p>
<button class="mt-auto flex w-full items-center justify-center rounded-md h-10 px-4 bg-primary/20 text-primary text-sm font-bold leading-normal tracking-wide hover:bg-primary/30 transition-colors">
<span class="truncate">Read More</span>
</button>
</div>
</div>'''


def generate_website():
    """Generate website by injecting article cards into template."""
    print("\n" + "=" * 70)
    print("🌐 GENERATING WEBSITE")
    print("=" * 70 + "\n")
    
    print("📚 Loading articles...")
    loader = ArticleLoader(DB_PATH, RESPONSES_DIR, IMAGES_DIR)
    
    # Get categories with processed articles in correct order
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Query to get categories in order: News (1), Science (2), Fun (3)
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
    
    # Generate article cards HTML for all categories combined
    print("\n🎨 Generating article cards...")
    all_cards = []
    
    # Order: News, Science, Fun (to match template tab order)
    category_order = ['News', 'Science', 'Fun']
    for cat_name in category_order:
        cat_articles = articles_by_category.get(cat_name, [])
        if cat_articles:
            cards = [HTMLGenerator.generate_article_card(article) for article in cat_articles]
            all_cards.extend(cards)
            print(f"  - {cat_name}: {len(cat_articles)} cards")
    
    cards_html = "\n".join(all_cards)
    
    # Replace the grid content in template
    # Find the grid div and replace all its article children
    pattern = r'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">(.*?)</div>\s*</main>'
    replacement = f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4">\n{cards_html}\n</div>\n</main>'
    output_html = re.sub(pattern, replacement, template, flags=re.DOTALL, count=1)
    
    # Add language toggle and tab switching scripts
    tab_and_lang_script = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    let currentLang = 'en';
    let activeTab = 0;
    const tabButtons = document.querySelectorAll('a[href="#"]'); // Tab links
    const cards = Array.from(document.querySelectorAll('[data-article-id]'));
    const categorySize = {
        'News': 4,
        'Science': 3,
        'Fun': 6
    };
    
    // Tab switching
    tabButtons.forEach((btn, index) => {
        if (btn.textContent.includes('News') || btn.textContent.includes('Science') || btn.textContent.includes('Fun')) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                activeTab = index;
                
                // Update tab styling
                tabButtons.forEach((tb, i) => {
                    if (i === index) {
                        tb.classList.add('border-b-primary', 'text-primary');
                        tb.classList.remove('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
                    } else {
                        tb.classList.remove('border-b-primary', 'text-primary');
                        tb.classList.add('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
                    }
                });
                
                // Show/hide cards based on category
                let cardIndex = 0;
                const sizes = Object.values(categorySize);
                let startIdx = 0;
                for (let i = 0; i < index; i++) {
                    startIdx += sizes[i];
                }
                const endIdx = startIdx + sizes[index];
                
                cards.forEach((card, i) => {
                    card.style.display = (i >= startIdx && i < endIdx) ? 'flex' : 'none';
                });
            });
        }
    });
    
    // Initialize first tab
    if (tabButtons.length > 0) {
        tabButtons[0].click();
    }
    
    // Language toggle (CN button)
    let cnButton = null;
    document.querySelectorAll('button').forEach(btn => {
        if (btn.textContent.trim() === 'CN') {
            cnButton = btn;
        }
    });
    
    if (cnButton) {
        cnButton.addEventListener('click', function(e) {
            e.preventDefault();
            currentLang = currentLang === 'en' ? 'zh' : 'en';
            
            // Update all visible article titles and summaries
            cards.forEach(card => {
                if (card.style.display !== 'none') {
                    const titleEl = card.querySelector('.article-title');
                    const summaryEl = card.querySelector('.article-summary');
                    
                    if (titleEl) {
                        titleEl.textContent = currentLang === 'zh' ? card.dataset.titleZh : card.dataset.titleEn;
                    }
                    if (summaryEl) {
                        summaryEl.textContent = currentLang === 'zh' ? card.dataset.summaryZh : card.dataset.summaryEn;
                    }
                }
            });
            
            cnButton.textContent = currentLang === 'zh' ? 'EN' : 'CN';
        });
    }
});
</script>
    '''
    
    # Inject script before closing body
    output_html = output_html.replace('</body>', f'{tab_and_lang_script}\n</body>')
    
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
    print(f"   - Total articles: {total_articles}")
    print(f"   - Tab order: News/Science/Fun")
    print(f"   - Language toggle: EN/CN button")
    print(f"   - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return True


if __name__ == '__main__':
    success = generate_website()
    sys.exit(0 if success else 1)
