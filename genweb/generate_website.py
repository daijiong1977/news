#!/usr/bin/env python3
"""
Website Generator - Creates index.html with latest articles from each category.
Reads from local database and response JSON files.
"""

import json
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Get base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'articles.db')
RESPONSES_DIR = os.path.join(BASE_DIR, 'website.remote', 'responses')
IMAGES_DIR = os.path.join(BASE_DIR, 'website.remote', 'article_image')
OUTPUT_DIR = os.path.join(BASE_DIR, 'website', 'generated')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'website', 'main', 'main_template.html')

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


class ArticleLoader:
    """Load articles from database and response files."""
    
    def __init__(self, db_path, responses_dir, images_dir):
        self.db_path = db_path
        self.responses_dir = responses_dir
        self.images_dir = images_dir
    
    def get_latest_processed_articles(self, limit: int = 20) -> List[Dict]:
        """Get latest processed articles from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, title, description, source, 
                       deepseek_processed, crawled_at, processed_at
                FROM articles 
                WHERE deepseek_processed = 1
                ORDER BY processed_at DESC
                LIMIT ?
            """, (limit,))
            
            articles = [dict(row) for row in cur.fetchall()]
            conn.close()
            return articles
        except Exception as e:
            print(f"❌ Error loading articles: {e}", file=sys.stderr)
            return []
    
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
            # Look for JPG image
            for img_file in Path(self.images_dir).glob(f'article_{article_id}_*.jpg'):
                return str(img_file)
            return None
        except Exception as e:
            print(f"⚠️  Error finding image for {article_id}: {e}", file=sys.stderr)
            return None
    
    def get_articles_by_category(self, category: str, limit: int = 6) -> List[Dict]:
        """Get articles by source (category)."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, title, description, source, 
                       deepseek_processed, crawled_at, processed_at
                FROM articles 
                WHERE deepseek_processed = 1 AND source = ?
                ORDER BY processed_at DESC
                LIMIT ?
            """, (category, limit))
            
            articles = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            # Enrich with response data and images
            enriched = []
            for article in articles:
                article['response'] = self.get_response_data(article['id'])
                article['image'] = self.get_article_image(article['id'])
                enriched.append(article)
            
            return enriched
        except Exception as e:
            print(f"❌ Error loading articles by source: {e}", file=sys.stderr)
            return []


class HTMLGenerator:
    """Generate HTML from templates."""
    
    @staticmethod
    def generate_article_card(article: Dict) -> str:
        """Generate HTML for an article card."""
        article_id = article['id']
        title = article['title']
        description = article['description']
        image_url = article.get('image', '')
        response = article.get('response', {})
        category = article.get('category', 'News')
        source = article.get('source', 'News Source')
        processed_at = article.get('processed_at', datetime.now().isoformat())
        
        # Format time
        try:
            dt = datetime.fromisoformat(processed_at)
            time_ago = f"{(datetime.now() - dt).seconds // 3600} hours ago" if (datetime.now() - dt).seconds > 3600 else "Just now"
        except:
            time_ago = "Recently"
        
        # Get easy level summary from response
        summary = ""
        if response and 'article_analysis' in response:
            levels = response['article_analysis'].get('levels', {})
            if 'easy' in levels:
                summary = levels['easy'].get('summary', description)[:150] + "..."
        
        if not summary:
            summary = description[:150] + "..." if description else title
        
        # Use image if available
        image_style = f'background-image: url("file://{image_url}");' if image_url else 'background-color: #e4e4e7;'
        
        return f"""
<div class="flex flex-col gap-3 bg-card-light dark:bg-card-dark rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
    <div class="w-full bg-center bg-no-repeat aspect-video bg-cover" style='{image_style}'></div>
    <div class="flex flex-col gap-2 p-4 pt-2">
        <h3 class="text-lg font-bold leading-snug tracking-tight">{title}</h3>
        <div class="flex items-center gap-2 text-xs text-subtle-light dark:text-subtle-dark">
            <p>{time_ago}</p>
            <span class="font-bold">·</span>
            <p>{source}</p>
        </div>
        <p class="text-subtle-light dark:text-subtle-dark text-sm font-normal leading-relaxed flex-grow">{summary}</p>
        <button class="mt-auto flex w-full items-center justify-center rounded-md h-10 px-4 bg-primary/20 text-primary text-sm font-bold leading-normal tracking-wide hover:bg-primary/30 transition-colors">
            <span class="truncate">Read More</span>
        </button>
    </div>
</div>
        """
    
    @staticmethod
    def generate_section(category: str, articles: List[Dict]) -> str:
        """Generate HTML for a category section."""
        if not articles:
            return f"""
<div class="px-4 py-8 text-center">
    <p class="text-subtle-light dark:text-subtle-dark">No articles available for {category}</p>
</div>
            """
        
        cards = "".join([HTMLGenerator.generate_article_card(article) for article in articles])
        
        return f"""
<div class="px-4 py-6">
    <h2 class="text-2xl font-bold mb-4">{category}</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards}
    </div>
</div>
        """


def generate_website():
    """Main website generation function."""
    print("\n" + "=" * 70)
    print("🌐 GENERATING WEBSITE")
    print("=" * 70 + "\n")
    
    # Load articles
    print("📚 Loading articles...")
    loader = ArticleLoader(DB_PATH, RESPONSES_DIR, IMAGES_DIR)
    
    # Get categories (detect from database)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT source FROM articles WHERE deepseek_processed=1 AND source IS NOT NULL ORDER BY source")
    categories = [row[0] for row in cur.fetchall()]
    conn.close()
    
    if not categories:
        print("❌ No categories found with processed articles")
        return False
    
    print(f"  ✓ Found categories: {', '.join(categories)}")
    
    # Generate sections for each category
    print("\n📄 Generating content sections...")
    sections = []
    
    for category in categories:
        print(f"  - Loading {category}...")
        articles = loader.get_articles_by_category(category, limit=6)
        
        if articles:
            section_html = HTMLGenerator.generate_section(category, articles)
            sections.append(section_html)
            print(f"    ✓ {len(articles)} articles loaded")
        else:
            print(f"    ⚠️  No articles found")
    
    # Generate final HTML
    print("\n✍️  Writing HTML...")
    
    # Read template
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False
    
    # Insert sections (replace placeholder if exists, or append before closing tags)
    content_sections = "".join(sections)
    
    # Simple insertion: add before closing </main> tag
    output_html = template.replace("</main>", f"{content_sections}</main>")
    
    # Write output
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
    print(f"   - Total articles displayed: {sum(len(loader.get_articles_by_category(cat, 6)) for cat in categories)}")
    print(f"   - Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return True


if __name__ == '__main__':
    success = generate_website()
    sys.exit(0 if success else 1)
