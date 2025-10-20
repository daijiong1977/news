#!/usr/bin/env python3
"""
Full pipeline for news crawling, Deepseek processing, and page generation.

Process:
1. Crawl articles from 4 RSS sources
2. Store articles in database with basic info
3. Process each article through Deepseek API (1 by 1)
4. Generate HTML pages for different reading levels
5. Create summary pages

Usage:
    python3 run_full_pipeline.py [--test] [--limit N]
    
Options:
    --test      Test mode with smaller batches
    --limit N   Limit articles to N per source
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import sqlite3
import datetime as dt
from typing import Optional, Any

# Import from existing modules
try:
    from db_utils import save_article_content, fetch_image
except ImportError as e:
    print(f"Error: Missing required module: {e}", file=sys.stderr)
    sys.exit(1)

import requests

# Configuration
SOURCES = {
    "pbs": {
        "url": "https://www.pbs.org/newshour/feeds/rss/headlines",
        "name": "PBS NewsHour",
        "max_articles": 5,
    },
    "swimming": {
        "url": "https://www.swimmingworldmagazine.com/news/feed/",
        "name": "Swimming World Magazine",
        "max_articles": 5,
    },
    "techradar": {
        "url": "https://www.techradar.com/rss",
        "name": "TechRadar",
        "max_articles": 5,
    },
    "sciencedaily": {
        "url": "https://www.sciencedaily.com/rss/top.xml",
        "name": "Science Daily",
        "max_articles": 5,
    },
}

DB_FILE = pathlib.Path("articles.db")
OUTPUT_DIR = pathlib.Path("output")
CONTENT_DIR = pathlib.Path("content")
IMAGES_DIR = pathlib.Path("images")

# Try to import deepseek key from environment
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-3fa37d1185514b7fbcd4c1ab8b7643db")


def init_database() -> sqlite3.Connection:
    """Initialize or connect to database."""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            pub_date TEXT,
            image_url TEXT,
            image_local TEXT,
            content TEXT,
            crawled_at TEXT,
            deepseek_processed BOOLEAN DEFAULT 0,
            processed_at TEXT
        )
    """)
    
    # Create summaries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty TEXT,
            language TEXT,
            summary TEXT,
            generated_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    """)
    
    conn.commit()
    return conn


def fetch_rss_feed(url: str, max_articles: int = 5) -> list[dict[str, str]]:
    """Fetch RSS feed and return list of articles."""
    import urllib.request
    import xml.etree.ElementTree as ET
    import email.utils
    
    print(f"  Fetching RSS feed: {url}", file=sys.stderr)
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        articles = []
        
        for item in root.findall(".//item"):
            if len(articles) >= max_articles:
                break
            
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            
            # Try to find image
            image_url = None
            media_content = item.find("{http://search.yahoo.com/mrss/}content")
            if media_content is not None:
                image_url = media_content.get("url")
            
            if not image_url:
                media_thumbnail = item.find("{http://search.yahoo.com/mrss/}thumbnail")
                if media_thumbnail is not None:
                    image_url = media_thumbnail.get("url")
            
            if title and link:
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pub_date": pub_date,
                    "image_url": image_url or "",
                })
        
        print(f"    Found {len(articles)} articles", file=sys.stderr)
        return articles
    
    except Exception as e:
        print(f"  Error fetching feed: {e}", file=sys.stderr)
        return []


def fetch_article_content(url: str) -> str:
    """Fetch full article content from URL."""
    import urllib.request
    from html.parser import HTMLParser
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html_data = response.read().decode('utf-8', errors='ignore')
        
        # Simple content extraction - get all text from <p> tags
        class ParagraphExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.paragraphs = []
                self.current_p = []
                self.in_p = False
                self.in_script = False
                self.in_style = False
            
            def handle_starttag(self, tag, attrs):
                if tag == 'p':
                    self.in_p = True
                elif tag == 'script':
                    self.in_script = True
                elif tag == 'style':
                    self.in_style = True
            
            def handle_endtag(self, tag):
                if tag == 'p' and self.in_p:
                    text = ''.join(self.current_p).strip()
                    if text:
                        self.paragraphs.append(text)
                    self.current_p = []
                    self.in_p = False
                elif tag == 'script':
                    self.in_script = False
                elif tag == 'style':
                    self.in_style = False
            
            def handle_data(self, data):
                if self.in_p and not self.in_script and not self.in_style:
                    self.current_p.append(data)
        
        parser = ParagraphExtractor()
        parser.feed(html_data)
        content = "\n\n".join(parser.paragraphs[:10])  # Take first 10 paragraphs
        
        return content if content else "Content extraction failed"
    
    except Exception as e:
        print(f"  Error fetching article content: {e}", file=sys.stderr)
        return ""


def crawl_sources(conn: sqlite3.Connection, test_mode: bool = False, limit: Optional[int] = None) -> int:
    """Crawl all configured RSS sources and store in database."""
    print("\n" + "="*80, file=sys.stderr)
    print("STEP 1: CRAWLING RSS SOURCES", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    cursor = conn.cursor()
    total_articles = 0
    
    for source_key, source_config in SOURCES.items():
        print(f"\nSource: {source_config['name']}", file=sys.stderr)
        
        max_articles = limit if limit else source_config["max_articles"]
        if test_mode:
            max_articles = 2
        
        articles = fetch_rss_feed(source_config["url"], max_articles)
        
        for article in articles:
            try:
                # Check if article with same title already exists
                cursor.execute("SELECT id FROM articles WHERE title = ?", (article["title"],))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"  ⊘ Skipped (duplicate): {article['title'][:60]}...", file=sys.stderr)
                    continue
                
                # Insert article
                cursor.execute("""
                    INSERT INTO articles 
                    (title, source, url, description, pub_date, image_url, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    article["title"],
                    source_config["name"],
                    article["link"],
                    article["description"],
                    article["pub_date"],
                    article["image_url"],
                    dt.datetime.now().isoformat(),
                ))
                conn.commit()
                total_articles += 1
                print(f"  ✓ Added: {article['title'][:60]}...", file=sys.stderr)
                
                # Small delay between requests
                time.sleep(0.2)
            
            except Exception as e:
                print(f"  ✗ Error adding article: {e}", file=sys.stderr)
    
    print(f"\n✓ Crawled {total_articles} new articles", file=sys.stderr)
    return total_articles


def fetch_article_details(conn: sqlite3.Connection, test_mode: bool = False) -> int:
    """Fetch full content for crawled articles."""
    print("\n" + "="*80, file=sys.stderr)
    print("STEP 2: FETCHING ARTICLE CONTENT", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    cursor = conn.cursor()
    
    # Get articles without content
    cursor.execute("""
        SELECT id, url, title FROM articles WHERE content IS NULL LIMIT ?
    """, (10 if test_mode else 100,))
    
    articles = cursor.fetchall()
    print(f"Fetching content for {len(articles)} articles...", file=sys.stderr)
    
    processed = 0
    for article_id, url, title in articles:
        print(f"  Fetching: {title[:60]}...", file=sys.stderr)
        
        content = fetch_article_content(url)
        
        if content:
            cursor.execute("""
                UPDATE articles SET content = ? WHERE id = ?
            """, (content, article_id))
            conn.commit()
            processed += 1
        
        time.sleep(0.3)  # Be respectful
    
    print(f"✓ Fetched content for {processed} articles", file=sys.stderr)
    return processed


def process_with_deepseek(conn: sqlite3.Connection, test_mode: bool = False) -> int:
    """Process articles through Deepseek API."""
    print("\n" + "="*80, file=sys.stderr)
    print("STEP 3: PROCESSING WITH DEEPSEEK API", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    if not DEEPSEEK_API_KEY:
        print("⚠ Warning: DEEPSEEK_API_KEY not set, skipping Deepseek processing", file=sys.stderr)
        return 0
    
    cursor = conn.cursor()
    
    # Get all articles with content to check which ones need processing
    cursor.execute("""
        SELECT id, title, content, deepseek_processed FROM articles 
        WHERE content IS NOT NULL 
        ORDER BY processed_at DESC
    """)
    
    all_articles = cursor.fetchall()
    to_process = [a for a in all_articles if a[3] == 0]  # Filter for unprocessed
    already_processed = len(all_articles) - len(to_process)
    
    print(f"Total articles with content: {len(all_articles)}", file=sys.stderr)
    print(f"Already analyzed: {already_processed}", file=sys.stderr)
    print(f"Processing {len(to_process)} articles through Deepseek...", file=sys.stderr)
    
    # Show already processed articles
    if already_processed > 0:
        for article_id, title, _, _ in all_articles:
            if any(a[3] == 1 for a in all_articles if a[0] == article_id):
                print(f"  ⊘ Skipped (already analyzed): {title[:60]}...", file=sys.stderr)
    
    processed = 0
    for article_id, title, content, _ in to_process:
        print(f"  Processing: {title[:60]}...", file=sys.stderr)
        
        try:
            # Create prompt for Deepseek
            prompt = f"""Analyze this article and provide summaries for three reading levels:

ARTICLE TITLE: {title}

ARTICLE CONTENT:
{content}

Please provide:
1. ELEMENTARY (ages 8-11): Simple summary using easy words
2. MIDDLE (ages 12-14): Medium-complexity summary
3. HIGH (ages 15+): Advanced summary with context

Format your response as JSON:
{{
    "summaries": {{
        "elementary": "...",
        "middle": "...",
        "high": "..."
    }},
    "language": "en"
}}"""
            
            # Call Deepseek API
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                response_text = result_data["choices"][0]["message"]["content"]
                
                # Parse JSON response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    if "summaries" in result:
                        # Store summaries
                        for difficulty, summary in result["summaries"].items():
                            cursor.execute("""
                                INSERT INTO article_summaries 
                                (article_id, difficulty, language, summary, generated_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                article_id,
                                difficulty,
                                result.get("language", "en"),
                                summary,
                                dt.datetime.now().isoformat(),
                            ))
                        
                        # Mark as processed
                        cursor.execute("""
                            UPDATE articles SET deepseek_processed = 1, processed_at = ? 
                            WHERE id = ?
                        """, (dt.datetime.now().isoformat(), article_id))
                        
                        conn.commit()
                        processed += 1
                        print(f"    ✓ Generated summaries: {', '.join(result['summaries'].keys())}", file=sys.stderr)
                else:
                    print(f"    ✗ Could not parse JSON response", file=sys.stderr)
            else:
                print(f"    ✗ Deepseek API error: {response.status_code}", file=sys.stderr)
            
            # Rate limiting
            time.sleep(2)
        
        except Exception as e:
            print(f"    ✗ Error processing: {e}", file=sys.stderr)
    
    print(f"✓ Processed {processed} articles with Deepseek", file=sys.stderr)
    return processed


def generate_pages(conn: sqlite3.Connection, test_mode: bool = False) -> int:
    """Generate HTML pages for articles."""
    print("\n" + "="*80, file=sys.stderr)
    print("STEP 4: GENERATING HTML PAGES", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    cursor = conn.cursor()
    
    # Get processed articles
    cursor.execute("""
        SELECT DISTINCT a.id, a.title, a.url, a.source, a.content
        FROM articles a
        WHERE a.deepseek_processed = 1
        LIMIT ?
    """, (10 if test_mode else 50,))
    
    articles = cursor.fetchall()
    print(f"Generating HTML pages for {len(articles)} articles...", file=sys.stderr)
    
    generated = 0
    for article_id, title, url, source, content in articles:
        # Get summaries
        cursor.execute("""
            SELECT difficulty, summary FROM article_summaries WHERE article_id = ?
        """, (article_id,))
        
        summaries = {row[0]: row[1] for row in cursor.fetchall()}
        
        try:
            # Generate HTML page
            output_file = OUTPUT_DIR / f"article_{article_id}.html"
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #1a73e8;
            margin-bottom: 10px;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        .summary-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid #1a73e8;
            border-radius: 4px;
        }}
        .summary-section h3 {{
            margin-top: 0;
            color: #1a73e8;
        }}
        .difficulty-badge {{
            display: inline-block;
            padding: 5px 10px;
            margin: 5px 5px 5px 0;
            background: #e8f0fe;
            color: #1a73e8;
            border-radius: 3px;
            font-size: 0.85em;
        }}
        .original-content {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 4px;
        }}
        .source-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #1a73e8;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
        .source-link:hover {{
            background: #1557b0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">
        <strong>Source:</strong> {source}<br>
        <strong>URL:</strong> <a href="{url}" target="_blank">{url[:60]}...</a>
    </div>
    
    <div class="summary-section">
        <h3>Summaries by Reading Level</h3>
"""
            
            for difficulty in ["elementary", "middle", "high"]:
                if difficulty in summaries:
                    html_content += f"""
        <div class="summary-section" style="margin: 15px 0;">
            <div class="difficulty-badge">{difficulty.upper()}</div>
            <p>{summaries[difficulty]}</p>
        </div>
"""
            
            html_content += f"""
    </div>
    
    <div class="original-content">
        <h3>Original Article Content</h3>
        <p>{content}</p>
    </div>
    
    <a href="{url}" target="_blank" class="source-link">Read Full Article →</a>
</body>
</html>
"""
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            generated += 1
            print(f"  ✓ Generated: {output_file}", file=sys.stderr)
        
        except Exception as e:
            print(f"  ✗ Error generating page: {e}", file=sys.stderr)
    
    print(f"✓ Generated {generated} HTML pages to {OUTPUT_DIR}", file=sys.stderr)
    return generated


def generate_index_page(conn: sqlite3.Connection) -> None:
    """Generate index page with links to all articles."""
    print(f"\nGenerating index page...", file=sys.stderr)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, source FROM articles WHERE deepseek_processed = 1
        ORDER BY processed_at DESC
    """)
    
    articles = cursor.fetchall()
    
    # Build HTML without format strings
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "    <title>News Articles Index</title>",
        "    <style>",
        "        body {",
        "            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
        "            max-width: 900px;",
        "            margin: 0 auto;",
        "            padding: 20px;",
        "            line-height: 1.6;",
        "            color: #333;",
        "        }",
        "        h1 {",
        "            color: #1a73e8;",
        "            border-bottom: 2px solid #1a73e8;",
        "            padding-bottom: 10px;",
        "        }",
        "        .article-list {",
        "            list-style: none;",
        "            padding: 0;",
        "        }",
        "        .article-item {",
        "            padding: 15px;",
        "            margin: 10px 0;",
        "            border: 1px solid #ddd;",
        "            border-radius: 4px;",
        "            background: #fafafa;",
        "            transition: all 0.3s;",
        "        }",
        "        .article-item:hover {",
        "            background: #f0f0f0;",
        "            border-color: #1a73e8;",
        "        }",
        "        .article-link {",
        "            color: #1a73e8;",
        "            text-decoration: none;",
        "            font-size: 1.1em;",
        "            font-weight: 500;",
        "        }",
        "        .article-link:hover {",
        "            text-decoration: underline;",
        "        }",
        "        .article-source {",
        "            color: #666;",
        "            font-size: 0.85em;",
        "            margin-top: 5px;",
        "        }",
        "        .stats {",
        "            background: #e8f0fe;",
        "            padding: 15px;",
        "            border-radius: 4px;",
        "            margin-bottom: 20px;",
        "        }",
        "    </style>",
        "</head>",
        "<body>",
        "    <h1>📰 News Articles Generated</h1>",
        "    <div class=\"stats\">",
        f"        <strong>Total Articles:</strong> {len(articles)}",
        "    </div>",
        "    <ul class=\"article-list\">",
    ]
    
    for article_id, title, source in articles:
        html_lines.append("        <li class=\"article-item\">")
        html_lines.append(f"            <a href=\"article_{article_id}.html\" class=\"article-link\">{title}</a>")
        html_lines.append(f"            <div class=\"article-source\">Source: {source}</div>")
        html_lines.append("        </li>")
    
    html_lines.extend([
        "    </ul>",
        "</body>",
        "</html>",
    ])
    
    html_content = "\n".join(html_lines)
    
    index_file = OUTPUT_DIR / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✓ Generated index page: {index_file}", file=sys.stderr)


def generate_articles_data(conn: sqlite3.Connection) -> None:
    """Generate articles_data.json for the main interface."""
    print(f"\nGenerating articles_data.json...", file=sys.stderr)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.title,
            a.pub_date as date,
            a.source,
            a.content,
            GROUP_CONCAT(CASE WHEN s.difficulty = 'elementary' THEN s.summary END) as summary_elementary,
            GROUP_CONCAT(CASE WHEN s.difficulty = 'middle' THEN s.summary END) as summary_middle,
            GROUP_CONCAT(CASE WHEN s.difficulty = 'high' THEN s.summary END) as summary_high
        FROM articles a
        LEFT JOIN article_summaries s ON a.id = s.article_id
        WHERE a.deepseek_processed = 1
        GROUP BY a.id
        ORDER BY a.processed_at DESC
    """)
    
    articles = cursor.fetchall()
    
    # Build articles data with language support and all difficulty levels
    articles_data = []
    for row in articles:
        article_id, title, date, source, content, summary_elem, summary_mid, summary_high = row
        
        # Extract keywords from title (simplified)
        title_words = [w for w in title.split() if len(w) > 4]
        keywords_list = title_words[:5] if title_words else ["News", "Article"]
        
        articles_data.append({
            "id": article_id,
            "title": title,
            "date": date or dt.datetime.now().strftime("%Y-%m-%d"),
            "source": source,
            "image": f"https://picsum.photos/400/300?random={article_id}",  # Real image from placeholder service
            "summary_easy": summary_elem or "",
            "summary_medium": summary_mid or "",
            "summary_hard": summary_high or "",
            "summary_en": summary_elem or summary_mid or summary_high or "",
            "summary_zh": summary_mid or summary_elem or "",
            "keywords": keywords_list
        })
    
    # Write JSON file
    data_file = OUTPUT_DIR / "articles_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated articles_data.json: {data_file} ({len(articles_data)} articles)", file=sys.stderr)


def main() -> None:
    """Run the full pipeline."""
    parser = argparse.ArgumentParser(
        description="Full news pipeline: crawl → process → generate pages"
    )
    parser.add_argument("--test", action="store_true", help="Test mode (smaller batches)")
    parser.add_argument("--limit", type=int, help="Limit articles per source")
    parser.add_argument("--skip-crawl", action="store_true", help="Skip crawling step")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip content fetching")
    parser.add_argument("--skip-deepseek", action="store_true", help="Skip Deepseek processing")
    parser.add_argument("--skip-pages", action="store_true", help="Skip page generation")
    
    args = parser.parse_args()
    
    # Ensure required directories
    CONTENT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Initialize database
    conn = init_database()
    
    print("\n" + "="*80, file=sys.stderr)
    print("NEWS PIPELINE - FULL END-TO-END PROCESS", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Test Mode: {args.test}", file=sys.stderr)
    print(f"Database: {DB_FILE}", file=sys.stderr)
    print(f"Output Directory: {OUTPUT_DIR}", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    try:
        # Step 1: Crawl RSS sources
        if not args.skip_crawl:
            crawl_sources(conn, test_mode=args.test, limit=args.limit)
        
        # Step 2: Fetch article content
        if not args.skip_fetch:
            fetch_article_details(conn, test_mode=args.test)
        
        # Step 3: Process with Deepseek
        if not args.skip_deepseek:
            process_with_deepseek(conn, test_mode=args.test)
        
        # Step 4: Generate pages
        if not args.skip_pages:
            generate_pages(conn, test_mode=args.test)
            generate_index_page(conn)
            generate_articles_data(conn)
        
        print("\n" + "="*80, file=sys.stderr)
        print("✓ PIPELINE COMPLETE", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(f"Open output/index.html to view generated pages", file=sys.stderr)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
