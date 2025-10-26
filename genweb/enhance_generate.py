#!/usr/bin/env python3
"""
Enhanced Website Generator - Creates separate JSON payloads for dynamic loading.
- Generates a lightweight main HTML with default (Enjoy) level articles
- Creates 4 separate JSON payload files (Relax, Enjoy, Research, CN)
- HTML loads payloads dynamically when user changes difficulty level
- Significantly reduces initial page size (~593KB → ~120KB + dynamic payloads)
- Preserves all article data while deferring rendering

Features:
- Default page loads with Enjoy (mid) level articles
- User switches difficulty → JavaScript loads corresponding JSON
- Each JSON payload contains all article data for that level
- Images lazy-load when cards are rendered
- No page reload needed for level switching
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
PAYLOADS_DIR = os.path.join(MAIN_DIR, 'payloads')

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(MAIN_DIR).mkdir(parents=True, exist_ok=True)
Path(WEBSITE_DIR).mkdir(parents=True, exist_ok=True)
Path(PAYLOADS_DIR).mkdir(parents=True, exist_ok=True)

# Difficulty level mapping
DIFFICULTY_MAPPING = {
    'easy': 'Relax',
    'middle': 'Enjoy',
    'high': 'Research'
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
            'middle': 'middle',
            'high': 'high',
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


class JSONPayloadGenerator:
    """Generate JSON payloads for each difficulty level."""
    
    @staticmethod
    def generate_article_data(article: Dict, level: str = 'easy', category: str = '', for_payload: bool = False) -> Dict:
        """Generate JSON data for a single article.
        
        Args:
            article: Article data from database
            level: Difficulty level
            category: Article category
            for_payload: If True, adjust paths for payload subdirectory
        """
        article_id = article['id']
        source = article.get('source', 'News Source')
        image_url = article.get('image', '')
        
        # Adjust image path for payloads subdirectory (only when for_payload=True)
        # Images are at ../article_image/ from /main/
        # But payloads are in /main/payloads/
        # So from payloads, images are at ../../article_image/
        if for_payload and image_url and image_url.startswith('../'):
            image_url = image_url.replace('../', '../../', 1)  # Convert ../foo to ../../foo
        
        response = article.get('response', {})
        pub_date = article.get('pub_date', '')
        
        # Time formatting
        try:
            if pub_date:
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
        
        # Fallback to original if not found
        if not title_level:
            title_level = article.get('title', '')
        if not summary_level:
            summary_level = article.get('description', '')
        
        return {
            'id': article_id,
            'title': title_level,
            'summary': summary_level,
            'source': source,
            'time_ago': time_ago,
            'image_url': image_url or '',
            'category': category
        }
    
    @staticmethod
    def generate_payloads(articles_by_category: Dict, output_dir: str, timestamp: str = '') -> Dict[str, int]:
        """Generate JSON payload files for each category + difficulty level combination.
        
        Structure: articles_<category>_<level>.json
        Example: articles_news_mid.json, articles_science_easy.json, etc.
        
        Args:
            articles_by_category: Dictionary mapping category names to article lists
            output_dir: Directory to write payload files (versioned by timestamp)
            timestamp: Timestamp string (YYYYMMDD_HHMMSS) for directory versioning
        
        Returns: Dict with payload names and file sizes
        """
        payload_sizes = {}
        
        # Create payloads for each category × difficulty combination
        for cat_name in ['News', 'Science', 'Fun']:
            for level_key in ['easy', 'middle', 'high', 'cn']:
                articles = []
                
                cat_articles = articles_by_category.get(cat_name, [])
                if cat_articles:
                    for article in cat_articles:
                        article_data = JSONPayloadGenerator.generate_article_data(
                            article, level_key, cat_name, for_payload=True
                        )
                        articles.append(article_data)
                
                # Write payload file: articles_<category>_<level>.json
                payload_file = os.path.join(output_dir, f'articles_{cat_name.lower()}_{level_key}.json')
                try:
                    with open(payload_file, 'w', encoding='utf-8') as f:
                        json.dump({'articles': articles}, f, ensure_ascii=False, indent=0)
                    
                    file_size = os.path.getsize(payload_file)
                    payload_sizes[f'{cat_name}_{level_key}'] = file_size
                except Exception as e:
                    print(f"❌ Error writing payload for {cat_name}/{level_key}: {e}")
        
        # Summary
        print("  Payloads created:")
        for cat_name in ['News', 'Science', 'Fun']:
            cat_total = 0
            print(f"  📁 {cat_name}:")
            for level_key in ['easy', 'middle', 'high', 'cn']:
                key = f'{cat_name}_{level_key}'
                size = payload_sizes.get(key, 0)
                cat_total += size
                level_display = DIFFICULTY_MAPPING.get(level_key, level_key)
                print(f"    - {level_display}: {size/1024:.1f}KB")
            print(f"    Total: {cat_total/1024:.1f}KB")
        
        return payload_sizes


class HTMLGenerator:
    """Generate lightweight HTML with embedded JavaScript for dynamic loading."""
    
    @staticmethod
    def generate_article_card_html(article_data: Dict) -> str:
        """Generate HTML template for a single article card.
        
        This is a template that JavaScript will use to render cards.
        """
        article_id = article_data['id']
        
        image_style = ''
        if article_data['image_url']:
            image_style = f"background-image: url('{article_data['image_url']}');"
        else:
            image_style = 'background-color: #e4e4e7;'
        
        return f'''<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{article_id}">
<a href="../article_page/article.html?id={{{{id}}}}&level={{{{level}}}}" class="w-full bg-center bg-no-repeat aspect-video bg-cover cursor-pointer hover:opacity-90 transition-opacity" style='{image_style}'></a>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{{title}}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{{time_ago}}</p>
<span class="font-bold">·</span>
<p>{{source}}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed article-summary" style="overflow-wrap: break-word; word-break: break-word;">{{summary}}</p>
<div class="flex justify-end mt-2">
<a href="../article_page/article.html?id={{{{id}}}}&level={{{{level}}}}" class="text-primary hover:text-primary/80 font-semibold text-sm transition-colors">
Activities →
</a>
</div>
</div>
</div>'''


def generate_website_enhanced():
    """Generate enhanced website with timestamped payloads."""
    print("=" * 70)
    print("🚀 ENHANCED WEBSITE GENERATOR (with Timestamped Payloads)")
    print("=" * 70)
    
    # Generate timestamp at the start
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"\n⏰ Generation timestamp: {timestamp}")
    
    loader = ArticleLoader(DB_PATH, RESPONSES_DIR, IMAGES_DIR)
    
    # Get categories with processed articles
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
    
    # Generate JSON payloads in versioned directory
    print("\n📦 Generating JSON payloads...")
    versioned_payloads_dir = os.path.join(MAIN_DIR, f'payloads_{timestamp}')
    Path(versioned_payloads_dir).mkdir(parents=True, exist_ok=True)
    payload_sizes = JSONPayloadGenerator.generate_payloads(articles_by_category, versioned_payloads_dir, timestamp)
    total_payload_size = sum(payload_sizes.values())
    print(f"  Total payload size: {total_payload_size/1024:.1f}KB")
    print(f"  Directory: payloads_{timestamp}/")
    
    # Read template
    print("\n📖 Reading template...")
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False
    
    # Generate default cards (News + Enjoy/middle level)
    print("\n🎨 Generating default article cards (News / Enjoy level)...")
    default_level = 'middle'
    default_category = 'News'
    all_default_cards = []
    
    # Only include News category for default view
    cat_articles = articles_by_category.get(default_category, [])
    if cat_articles:
        for article in cat_articles:
            article_data = JSONPayloadGenerator.generate_article_data(
                article, default_level, default_category
            )
            all_default_cards.append(article_data)
    
    # Generate HTML cards for default level
    # Embed the default cards directly
    default_cards_html = ""
    for data in all_default_cards:
        card_html = f'''<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{data['id']}">
<a href="../article_page/article.html?id={data['id']}&level=middle" class="w-full bg-center bg-no-repeat aspect-video bg-cover cursor-pointer hover:opacity-90 transition-opacity" style="{'background-image: url(\'' + data['image_url'] + '\');' if data['image_url'] else 'background-color: #e4e4e7;'}"></a>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{data['title']}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{data['time_ago']}</p>
<span class="font-bold">·</span>
<p>{data['source']}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed article-summary" style="overflow-wrap: break-word; word-break: break-word;">{data['summary']}</p>
<div class="flex justify-end mt-2">
<a href="../article_page/article.html?id={data['id']}&level=middle" class="text-primary hover:text-primary/80 font-semibold text-sm transition-colors">
Activities →
</a>
</div>
</div>
</div>'''
        default_cards_html += card_html + "\n"
    
    # Add JavaScript for dynamic loading with category + difficulty support
    print("\n⚙️  Injecting dynamic loading script...")
    payload_base_path = f'./payloads_{timestamp}/'
    dynamic_js = '''<script>
// Dynamic article loading by category and difficulty level
const PAYLOAD_BASE = '{PAYLOAD_BASE}';

// Template for regular levels (with Activities link)
const CARD_TEMPLATE = `<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{{id}}">
<a href="../article_page/article.html?id={{id}}&level={{levelKey}}" class="w-full bg-center bg-no-repeat aspect-video bg-cover cursor-pointer hover:opacity-90 transition-opacity" style="{{imageStyle}}"></a>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{{title}}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{{time_ago}}</p>
<span class="font-bold">·</span>
<p>{{source}}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed article-summary" style="overflow-wrap: break-word; word-break: break-word;">{{summary}}</p>
<div class="flex justify-end mt-2">
<a href="../article_page/article.html?id={{id}}&level={{levelKey}}" class="text-primary hover:text-primary/80 font-semibold text-sm transition-colors">
Activities →
</a>
</div>
</div>
</div>`;

// Template for CN level (no Activities link, no clickable image)
const CARD_TEMPLATE_CN = `<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1" data-article-id="{{id}}">
<div class="w-full bg-center bg-no-repeat aspect-video bg-cover" style="{{imageStyle}}"></div>
<div class="flex flex-col gap-2 p-4 pt-2">
<h3 class="text-lg font-bold leading-snug tracking-tight article-title">{{title}}</h3>
<div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
<p>{{time_ago}}</p>
<span class="font-bold">·</span>
<p>{{source}}</p>
</div>
<p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed article-summary" style="overflow-wrap: break-word; word-break: break-word;">{{summary}}</p>
</div>
</div>`;

const levelMap = {
  'Relax': 'easy',
  'Enjoy': 'middle',
  'Research': 'high',
  'CN': 'cn'
};

// Track current selections
let currentCategory = 'News';
let currentLevel = 'Enjoy';
let isChineseMode = localStorage.getItem('language') === 'cn';

async function loadArticles(category, level) {
  // Always read current language mode from localStorage
  const isChineseMode = localStorage.getItem('language') === 'cn';
  
  // If in Chinese mode, override level to 'cn'
  let finalLevel = isChineseMode ? 'CN' : level;
  const levelKey = levelMap[finalLevel] || 'middle';
  const categoryLower = category.toLowerCase();
  
  console.log(`Loading articles: ${category} / ${finalLevel} (${levelKey})`);
  console.log(`Chinese mode: ${isChineseMode}`);
  
  try {
    const payloadFile = `${PAYLOAD_BASE}articles_${categoryLower}_${levelKey}.json`;
    console.log(`Fetching: ${payloadFile}`);
    
    const response = await fetch(payloadFile);
    if (!response.ok) throw new Error(`HTTP ${response.status} loading ${payloadFile}`);
    
    const data = await response.json();
    const articles = data.articles || [];
    
    // Render articles
    const grid = document.querySelector('.grid');
    if (!grid) {
      console.error('Grid element not found');
      return;
    }
    
    grid.innerHTML = '';
    articles.forEach(article => {
      const imageStyle = article.image_url 
        ? `background-image: url('${article.image_url}');` 
        : 'background-color: #e4e4e7;';
      
      // Use CN template if level is 'cn', otherwise use regular template
      const template = (levelKey === 'cn') ? CARD_TEMPLATE_CN : CARD_TEMPLATE;
      
      const html = template
        .replace(/{{id}}/g, article.id)
        .replace(/{{levelKey}}/g, levelKey)
        .replace('{{imageStyle}}', imageStyle)
        .replace('{{title}}', escapeHtml(article.title))
        .replace('{{time_ago}}', article.time_ago)
        .replace('{{source}}', article.source)
        .replace('{{summary}}', escapeHtml(article.summary));
      
      grid.innerHTML += html;
    });
    
    console.log(`✓ Loaded ${articles.length} articles for ${category}/${finalLevel}`);
  } catch (error) {
    console.error(`Error loading articles: ${error.message}`);
    const grid = document.querySelector('.grid');
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: red;">Error loading articles. Check browser console.</div>`;
    }
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Hook into category tabs and difficulty dropdown
document.addEventListener('DOMContentLoaded', function() {
  // Category tabs
  const tabs = document.querySelectorAll('a[href="#"]');
  tabs.forEach((tab, index) => {
    const categories = ['News', 'Science', 'Fun'];
    if (index < 3) {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Update active tab styling
        tabs.forEach((t, i) => {
          if (i < 3) {
            if (i === index) {
              t.classList.add('border-b-primary', 'text-primary');
              t.classList.remove('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
            } else {
              t.classList.remove('border-b-primary', 'text-primary');
              t.classList.add('border-b-transparent', 'text-subtle-light', 'dark:text-subtle-dark');
            }
          }
        });
        
        currentCategory = categories[index];
        loadArticles(currentCategory, currentLevel);
      });
    }
  });
  
  // Difficulty dropdown
  const select = document.querySelector('select');
  if (select) {
    select.addEventListener('change', function() {
      currentLevel = this.value;
      loadArticles(currentCategory, currentLevel);
    });
  }
  
  // CN Language Toggle Button
  const cnButton = document.getElementById('cn-toggle');
  if (cnButton) {
    function updateCNButtonStyle() {
      const isChinese = localStorage.getItem('language') === 'cn';
      const label = document.getElementById('cn-button-label');
      const select = document.querySelector('select');
      
      if (isChinese) {
        // In Chinese mode: button shows "EN" (to switch to English)
        cnButton.classList.remove('bg-card-light', 'dark:bg-card-dark', 'text-text-light', 'dark:text-text-dark');
        cnButton.classList.add('bg-primary', 'text-white');
        if (label) label.textContent = 'EN';
        // Hide difficulty dropdown in CN mode
        if (select) select.style.display = 'none';
      } else {
        // In English mode: button shows "CN" (to switch to Chinese)
        cnButton.classList.remove('bg-primary', 'text-white');
        cnButton.classList.add('bg-card-light', 'dark:bg-card-dark', 'text-text-light', 'dark:text-text-dark');
        if (label) label.textContent = 'CN';
        // Show difficulty dropdown in English mode
        if (select) select.style.display = '';
      }
    }
    
    // Initialize CN button style
    updateCNButtonStyle();
    // Ensure articles reflect current language on initial load
    loadArticles(currentCategory, currentLevel);
    
    // CN button click handler
    cnButton.addEventListener('click', function(e) {
      e.preventDefault();
      const currentMode = localStorage.getItem('language');
      const newMode = currentMode === 'cn' ? 'en' : 'cn';
      localStorage.setItem('language', newMode);
      console.log(`CN mode toggled to: ${newMode}`);
      updateCNButtonStyle();
      isChineseMode = (newMode === 'cn');
      loadArticles(currentCategory, currentLevel);
    });
  }
  
  // Listen for CN mode changes (external changes to localStorage)
  const observer = setInterval(function() {
    const newCNMode = localStorage.getItem('language') === 'cn';
    if (newCNMode !== isChineseMode) {
      isChineseMode = newCNMode;
      console.log(`CN mode changed to: ${isChineseMode}`);
      loadArticles(currentCategory, currentLevel);
    }
  }, 100);
});
</script>'''.replace("const PAYLOAD_BASE = '{PAYLOAD_BASE}';", f"const PAYLOAD_BASE = '{payload_base_path}';")
    
    # Replace the grid content in template
    pattern = r'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">[\s\S]*?<!-- Article cards go here -->[\s\S]*?</div>\s*</main>'
    replacement = f'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">\n{default_cards_html}</div>\n</main>'
    output_html = re.sub(pattern, replacement, template, flags=re.DOTALL, count=1)
    
    # Inject the dynamic loading script before closing body tag
    output_html = output_html.replace('</body>', dynamic_js + '\n</body>')
    
    # Write main HTML file
    print("\n💾 Writing enhanced HTML...")
    
    # Main index.html
    output_path = os.path.join(MAIN_DIR, 'index.html')
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        main_size = os.path.getsize(output_path)
        print(f"  ✓ Main HTML: {output_path}")
        print(f"    Size: {main_size/1024:.1f}KB")
    except Exception as e:
        print(f"❌ Error writing main HTML: {e}")
        return False
    
    # Timestamped backup
    timestamped_path = os.path.join(MAIN_DIR, f'index_{timestamp}.html')
    try:
        with open(timestamped_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f"  ✓ Timestamped backup: {timestamped_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not write timestamped backup: {e}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 GENERATION SUMMARY")
    print("=" * 70)
    print(f"\n📦 Payload Files ({PAYLOADS_DIR}/)")
    print(f"  - articles_easy.json (Relax):    {payload_sizes.get('easy', 0)/1024:.1f}KB")
    print(f"  - articles_mid.json (Enjoy):     {payload_sizes.get('mid', 0)/1024:.1f}KB")
    print(f"  - articles_hard.json (Research): {payload_sizes.get('hard', 0)/1024:.1f}KB")
    print(f"  - articles_cn.json (CN):         {payload_sizes.get('cn', 0)/1024:.1f}KB")
    print(f"  Total payloads: {total_payload_size/1024:.1f}KB")
    
    print(f"\n📄 Main HTML ({MAIN_DIR}/)")
    print(f"  - index.html: {main_size/1024:.1f}KB (includes default Enjoy level)")
    print(f"  - Reduction: ~{(593 - main_size/1024):.1f}KB saved vs monolithic ({((593-main_size/1024)/593*100):.0f}% smaller)")
    
    print(f"\n📈 Content Statistics")
    print(f"  - Total articles: {total_articles}")
    print(f"  - Articles per level: ~{total_articles}")
    print(f"  - Default level on load: Enjoy (mid)")
    print(f"  - Dynamic loading: Enabled via dropdown")
    
    print(f"\n✅ GENERATION COMPLETE")
    print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = generate_website_enhanced()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
