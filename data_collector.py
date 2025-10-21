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


def clean_paragraphs(paragraphs):
    """Clean and filter paragraphs - remove bylines, feedback prompts, etc."""
    import html
    import re
    
    TRIM_PREFIXES = (
        "Read More:",
        "READ MORE:",
        "Watch:",
        "WATCH:",
        "Notice:",
        "NOTICE:",
    )
    TRIM_CONTAINS = (
        "Support trusted journalism",
        "Support Provided By:",
        "Subscribe to Here's the Deal",
    )
    ASCII_REPLACEMENTS = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    
    # Common byline patterns to detect (names that appear in PBS articles)
    BYLINE_NAMES = {
        'Nick Schifrin', 'Sonia Kopelev', 'Geoff Bennett', 'Amna Nawaz',
        'Stephanie Kotuby', 'Alexa Gold', 'Jonah Anderson', 'Ismael M. Belkoura',
        'Amalia Hout-Marchand', 'Leonardo Pini', 'Athan Yanos',
    }
    
    cleaned = []
    for raw in paragraphs:
        # Unescape HTML entities
        text = html.unescape(raw.strip())
        for src, dst in ASCII_REPLACEMENTS.items():
            text = text.replace(src, dst)
        text = text.replace("\r", "")
        
        if not text:
            continue
        
        # Check for byline patterns: repeated names or name:
        # Pattern 1: "Name Name" (duplicated name)
        stripped = text.strip()
        parts = stripped.split()
        if len(parts) == 2 and parts[0] == parts[1]:
            # Likely "Nick Schifrin Nick Schifrin" - skip it
            continue
        
        # Pattern 2: Direct byline name match
        if stripped in BYLINE_NAMES:
            continue
        
        # Pattern 3: Name with colon (e.g., "Nick Schifrin:")
        if len(parts) <= 3 and stripped.endswith(':'):
            name_part = stripped[:-1].strip()
            if name_part in BYLINE_NAMES:
                continue
        
        # Skip all-caps short text (like bylines)
        upper_count = sum(1 for ch in text if ch.isupper())
        lower_count = sum(1 for ch in text if ch.islower())
        if upper_count and not lower_count and len(text.split()) <= 6:
            continue
        
        # Skip short capitalized phrases (2-3 words, all caps) - generic byline pattern
        if len(parts) <= 3 and all(w[0].isupper() for w in parts if len(w) > 0):
            # If very short and all proper case, likely a byline
            if len(parts) <= 2 and len(text) < 40:
                continue
        
        # Skip feedback prompts
        if text.lower() == "leave your feedback":
            continue
        
        # Skip prefixes
        if any(text.startswith(prefix) for prefix in TRIM_PREFIXES):
            continue
        
        # Skip certain phrases
        if any(needle in text for needle in TRIM_CONTAINS):
            continue
        
        # Skip if less than 30 chars (too short to be real content)
        if len(text) < 30:
            continue
        
        # Skip duplicates
        if cleaned and text == cleaned[-1]:
            continue
        
        cleaned.append(text)
    
    return cleaned


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
        raw_paragraphs = parser.get_paragraphs()
        
        # Clean whitespace from all paragraphs first
        import re
        cleaned_raw = []
        for p in raw_paragraphs:
            # Normalize whitespace
            clean_p = re.sub(r'\s+', ' ', p.strip())
            if clean_p:
                cleaned_raw.append(clean_p)
        
        # Find the start of actual content by looking for substantial paragraphs
        # Skip the first few paragraphs which are usually bylines/presenter names
        content_start = 0
        for i, p in enumerate(cleaned_raw):
            # Skip very short paragraphs (< 50 chars) - these are usually bylines
            if len(p) > 50:
                content_start = i
                break
        
        # Use paragraphs starting from content_start
        filtered_paragraphs = cleaned_raw[content_start:]
        
        # Clean and filter paragraphs
        paragraphs = clean_paragraphs(filtered_paragraphs)
        
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


def is_transcript_article(content):
    """Check if article is a transcript-style piece (mixed speaker names and dialogue).
    These are hard to clean and should be skipped for now."""
    if not content:
        return False
    
    # Transcript-style indicators: speaker names mixed throughout content
    # Common PBS and news transcript patterns
    transcript_indicators = [
        'has the details.',
        'reports:',
        'says:',
        'tells ',
        'NewsHour:',
        'the details.',
    ]
    
    content_lower = content.lower()
    
    # Check if content has transcript markers
    indicator_count = sum(1 for indicator in transcript_indicators if indicator in content_lower)
    
    # If multiple transcript indicators found, it's likely a transcript
    if indicator_count >= 2:
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
            
            # Skip transcript-style articles (PBS news interviews/reports with mixed speakers)
            if is_transcript_article(article['content']):
                print(f"  ⊘ Skipped (TRANSCRIPT): {article['title'][:60]}...")
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
