#!/usr/bin/env python3
"""
Data Collector - RSS Feed Crawler
Collects articles from various RSS feeds stored in the database and stores them in articles table.
Maps sources to categories automatically from feeds table.
"""

import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
import pathlib
from html.parser import HTMLParser
import time

DB_FILE = pathlib.Path("articles.db")


class ParagraphExtractor(HTMLParser):
    """Extract paragraphs from HTML."""
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
            if text and len(text) > 10:  # Skip very short text
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
    
    def get_paragraphs(self):
        return self.paragraphs


def fetch_article_content(url):
    """Fetch full article content from URL and extract text."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Extract paragraphs
        parser = ParagraphExtractor()
        parser.feed(response.text)
        paragraphs = parser.get_paragraphs()
        
        if paragraphs:
            content = "\n\n".join(paragraphs[:15])  # Take first 15 paragraphs
            return content[:5000]  # Limit to 5000 chars
        else:
            return ""
    except Exception as e:
        return ""


def get_feeds_from_db(conn):
    """Query all enabled feeds from database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.feed_id, f.feed_name, f.feed_url, f.category_id, c.category_name
        FROM feeds f
        JOIN categories c ON f.category_id = c.category_id
        WHERE f.enable = 1
        ORDER BY f.feed_name
    """)
    return cursor.fetchall()


def is_video_article(title, description, url):
    """Check if article is a video/show/segment (should be skipped).
    Only skip if it's clearly about watching/viewing video content."""
    # Only skip if explicitly marked as video content to watch
    video_keywords = [
        'watch:', 'video:', 'segment -',
        'pbs newshour episode', 'full episode',
        'video episode'
    ]
    
    combined = f"{title} {description} {url}".lower()
    
    for keyword in video_keywords:
        if keyword in combined:
            return True
    
    return False


def article_exists(conn, url):
    """Check if article already exists by URL."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
    return cursor.fetchone() is not None


def insert_article(conn, title, source, url, description, content, pub_date, category_id):
    """Insert article into database."""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO articles 
            (title, source, url, description, content, pub_date, crawled_at, category_id, deepseek_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            title[:500] if title else "",
            source[:100] if source else "",
            url[:500] if url else "",
            description[:1000] if description else "",
            content[:5000] if content else "",
            pub_date[:50] if pub_date else datetime.now().isoformat(),
            datetime.now().isoformat(),
            category_id
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"  ✗ Duplicate URL or constraint error: {e}")
        return None


def parse_rss_feed(feed_url, source_name, category_id, max_articles=1):
    """Parse RSS feed and extract articles."""
    articles = []
    
    try:
        print(f"\n  Fetching {source_name} feed...")
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # Handle different RSS formats
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//entry')  # Atom format
        
        for item in items[:max_articles]:
            # Extract fields (handle both RSS and Atom formats)
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else ""
            
            # Link/URL
            link_elem = item.find('link')
            url = ""
            if link_elem is not None:
                if link_elem.text:  # RSS format
                    url = link_elem.text
                else:  # Atom format
                    href = link_elem.get('href')
                    url = href if href else ""
            
            # Description/Summary
            desc_elem = item.find('description')
            if desc_elem is None:
                desc_elem = item.find('summary')
            description = desc_elem.text if desc_elem is not None else ""
            
            # Content (often in description or content:encoded)
            content = description
            content_encoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            if content_encoded is not None and content_encoded.text:
                content = content_encoded.text
            
            # Publication date
            pub_date_elem = item.find('pubDate')
            if pub_date_elem is None:
                pub_date_elem = item.find('published')
            pub_date = pub_date_elem.text if pub_date_elem is not None else datetime.now().isoformat()
            
            if title and url:
                # Fetch full article content from URL
                full_content = fetch_article_content(url)
                if not full_content:
                    full_content = content  # Fall back to RSS content
                
                articles.append({
                    'title': title,
                    'source': source_name,
                    'url': url,
                    'description': description[:500] if description else "",
                    'content': full_content[:5000] if full_content else "",
                    'pub_date': pub_date,
                    'category_id': category_id
                })
                
                # Be respectful - add delay between requests
                time.sleep(0.3)
        
        print(f"  ✓ Found {len(articles)} article(s)")
        return articles
        
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch feed: {e}")
        return []
    except ET.ParseError as e:
        print(f"  ✗ Failed to parse XML: {e}")
        return []


def collect_articles(num_per_source=1):
    """Collect articles from RSS feeds stored in database."""
    
    if not DB_FILE.exists():
        print(f"✗ Database not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(DB_FILE)
    
    print("\n" + "="*70)
    print("COLLECTING ARTICLES FROM RSS FEEDS")
    print("="*70)
    print(f"Target: {num_per_source} article(s) per source")
    
    # Get feeds from database
    feeds = get_feeds_from_db(conn)
    
    if not feeds:
        print("✗ No active feeds found in database")
        conn.close()
        return False
    
    print(f"Found {len(feeds)} active feed(s)")
    
    collected = 0
    duplicates = 0
    
    for feed_id, feed_name, feed_url, category_id, category_name in feeds:
        print(f"\n[{feed_name}]")
        
        # Fetch RSS feed
        articles = parse_rss_feed(feed_url, feed_name, category_id, num_per_source)
        
        # Insert articles
        for article in articles:
            # Skip video articles
            if is_video_article(article['title'], article['description'], article['url']):
                print(f"  ⊘ Skipped (VIDEO): {article['title'][:60]}...")
                continue
            
            if article_exists(conn, article['url']):
                print(f"  ⊘ Duplicate: {article['title'][:60]}...")
                duplicates += 1
            else:
                article_id = insert_article(
                    conn,
                    article['title'],
                    article['source'],
                    article['url'],
                    article['description'],
                    article['content'],
                    article['pub_date'],
                    article['category_id']
                )
                if article_id:
                    print(f"  ✓ Inserted (ID {article_id}): {article['title'][:60]}...")
                    collected += 1
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"✓ Collection complete: {collected} new articles, {duplicates} duplicates")
    print("="*70)
    
    return collected > 0


def main():
    """Main function."""
    print("\n" + "="*70)
    print("DATA COLLECTOR - RSS Feed Aggregator")
    print("="*70)
    
    collect_articles(num_per_source=5)
    
    # Show what was collected
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0")
    unprocessed = cursor.fetchone()[0]
    cursor.execute("SELECT id, title, source, category_id FROM articles WHERE deepseek_processed = 0")
    articles = cursor.fetchall()
    conn.close()
    
    print(f"\nReady for processing: {unprocessed} unprocessed article(s)")
    for article_id, title, source, category_id in articles:
        print(f"  - ID {article_id}: {title[:60]}... (Source: {source}, Category ID: {category_id})")
    
    print("\nNext: Run data_processor.py to process these articles through Deepseek")


if __name__ == "__main__":
    main()
