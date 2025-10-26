#!/usr/bin/env python3
"""
Main Payload Generator - Creates JSON payloads for dynamic article loading.
- Reads articles from database and response files
- Generates 12 JSON payload files (3 categories × 4 difficulty levels)
- Creates timestamped payload directory with symlink to latest
- Does NOT regenerate HTML (use enhance_generate.py for that)

Usage:
    python3 genweb/mainpayload_generate.py

Output:
    - website/main/payloads_YYYYMMDD_HHMMSS/ (timestamped directory)
    - website/main/payloads_latest -> payloads_YYYYMMDD_HHMMSS/ (symlink)
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
RESPONSES_DIR = os.path.join(BASE_DIR, 'website', 'article_response')
IMAGES_DIR = os.path.join(BASE_DIR, 'website', 'article_image')
MAIN_DIR = os.path.join(BASE_DIR, 'website', 'main')

Path(MAIN_DIR).mkdir(parents=True, exist_ok=True)

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
    
    def get_articles_by_category(self, category_id: int, limit: int = 6, max_per_source: int = 4) -> List[Dict]:
        """Get latest N articles with balanced source representation.
        
        Args:
            category_id: Category ID to fetch
            limit: Total articles to return (default 6)
            max_per_source: Max articles from a single source (default 4)
            
        Strategy: Get articles sorted by pub_date DESC, but ensure no source exceeds max_per_source.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get ALL processed articles in this category, sorted by pub_date DESC
            cur.execute("""
                SELECT id, title, description, source, 
                       deepseek_processed, crawled_at, processed_at, zh_title, pub_date
                FROM articles 
                WHERE deepseek_processed = 1 AND category_id = ?
                ORDER BY pub_date DESC
            """, (category_id,))
            
            all_articles = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            # Helper function to parse RFC dates
            def parse_pub_date(article):
                try:
                    pub_date_str = article.get('pub_date', '')
                    # Parse RFC date string to datetime
                    dt = parsedate_to_datetime(pub_date_str)
                    return dt
                except:
                    return datetime.min  # If parsing fails, treat as oldest
            
            # Ensure sorted by pub_date DESC
            all_articles.sort(key=parse_pub_date, reverse=True)
            
            # Apply max-per-source limit: take top articles but cap each source at max_per_source
            selected_articles = []
            source_count = {}
            
            for article in all_articles:
                source = article['source']
                source_count[source] = source_count.get(source, 0)
                
                # Only add if this source hasn't hit the max
                if source_count[source] < max_per_source:
                    selected_articles.append(article)
                    source_count[source] += 1
                    
                    # Stop once we have enough articles
                    if len(selected_articles) >= limit:
                        break
            
            all_articles = selected_articles
            
            # Enrich with response data and images
            for article in all_articles:
                article['response'] = self.get_response_data(article['id'])
                article['image'] = self.get_article_image(article['id'])
            
            return all_articles
        except Exception as e:
            print(f"❌ Error loading articles by category: {e}", file=sys.stderr)
            return []
    
    def extract_content(self, response_data: Optional[Dict], level: str) -> tuple:
        """Extract title and summary for a given difficulty level."""
        if not response_data or 'article_analysis' not in response_data:
            return None, None
        
        # Map our level names to the actual keys in the response
        level_map = {
            'easy': 'easy',
            'middle': 'middle',
            'high': 'high',
            'cn': 'zh'
        }
        
        response_level = level_map.get(level, level)
        levels = response_data.get('article_analysis', {}).get('levels', {})
        
        if response_level in levels:
            content = levels[response_level]
            title = content.get('title', '')
            summary = content.get('summary', '')
            return title, summary
        
        return None, None


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
        Example: articles_news_middle.json, articles_science_easy.json, etc.
        
        Args:
            articles_by_category: Dictionary mapping category names to article lists
            output_dir: Directory to write payload files (versioned by timestamp)
            timestamp: Timestamp string (YYYYMMDD_HHMMSS) for directory versioning
        
        Returns: Dict with payload names and file sizes
        """
        payload_sizes = {}
        
        # Create payloads for each category × difficulty combination
        for cat_name in ['News', 'Science', 'Fun']:
            print(f"\n  📄 {cat_name} category:")
            cat_articles = articles_by_category.get(cat_name, [])
            
            # Print all articles in this category
            if cat_articles:
                print(f"    Articles in payload ({len(cat_articles)} total):")
                for article in cat_articles:
                    print(f"      - [{article['id']}] {article['title'][:60]}")
            
            for level_key in ['easy', 'middle', 'high', 'cn']:
                articles = []
                
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


def update_archive_dates(main_dir: str, current_payload_dir: str):
    """Update archive_available_dates.json based on existing payload directories.
    
    Args:
        main_dir: Path to website/main/
        current_payload_dir: Path to the current payload directory being generated
    """
    # Pattern: payloads_YYYYMMDD_HHMMSS
    pattern = re.compile(r'^payloads_(\d{8})_(\d{6})$')
    
    dates_dict = {}  # {date: [list of timestamps]}
    
    for item in Path(main_dir).iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                date = match.group(1)
                timestamp = match.group(2)
                
                if date not in dates_dict:
                    dates_dict[date] = []
                dates_dict[date].append(timestamp)
    
    # Sort timestamps for each date to get the latest
    dates_data = []
    for date in sorted(dates_dict.keys()):
        timestamps = sorted(dates_dict[date], reverse=True)
        latest_timestamp = timestamps[0]
        
        dates_data.append({
            'date': date,
            'latest_timestamp': latest_timestamp,
            'directory': f'payloads_{date}_{latest_timestamp}',
            'count': len(timestamps)
        })
    
    # Create output structure
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_dates': len(dates_data),
        'dates': [d['date'] for d in dates_data],
        'details': dates_data
    }
    
    # Write to CURRENT payload directory (not main_dir)
    output_file = os.path.join(current_payload_dir, 'archive_available_dates.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Archive index created in payload directory: {len(dates_data)} dates available")


def generate_payloads_only():
    """Generate only JSON payloads without touching HTML."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("=" * 70)
    print("🚀 MAIN PAYLOAD GENERATOR")
    print("=" * 70)
    print()
    print(f"⏰ Generation timestamp: {timestamp}")
    
    # Load articles from database
    loader = ArticleLoader(DB_PATH, RESPONSES_DIR, IMAGES_DIR)
    
    # Get categories with articles
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT c.category_id, c.category_name
        FROM categories c
        JOIN articles a ON c.category_id = a.category_id
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
    
    # Create/update symlink to latest payloads
    payloads_latest = os.path.join(MAIN_DIR, 'payloads_latest')
    if os.path.islink(payloads_latest) or os.path.exists(payloads_latest):
        os.remove(payloads_latest)
    os.symlink(f'payloads_{timestamp}', payloads_latest)
    print(f"  Symlink: payloads_latest -> payloads_{timestamp}/")
    
    # Update archive available dates
    print("\n📅 Updating archive dates...")
    update_archive_dates(MAIN_DIR, versioned_payloads_dir)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 GENERATION SUMMARY")
    print("=" * 70)
    print()
    print(f"\n📦 Payload Files ({MAIN_DIR}/)")
    print(f"  - 13 JSON files (12 payloads + 1 archive index)")
    print(f"  - Total size: {total_payload_size/1024:.1f}KB")
    print(f"  - Directory: payloads_{timestamp}/")
    print(f"  - Symlink: payloads_latest -> payloads_{timestamp}/")
    
    print(f"\n📈 Content Statistics")
    print(f"  - Total articles: {total_articles}")
    print(f"  - Categories: {len(categories)}")
    print(f"  - Levels per category: 4 (Relax/Enjoy/Research/CN)")
    
    print(f"\n✅ PAYLOAD GENERATION COMPLETE")
    print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")
    
    print("💡 Note: HTML was NOT regenerated. Use enhance_generate.py if template changes are needed.")
    
    return True


if __name__ == '__main__':
    try:
        success = generate_payloads_only()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
