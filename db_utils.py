#!/usr/bin/env python3
"""Database and image handling utilities for articles."""

import sqlite3
import pathlib
import hashlib
import io
import urllib.request
import urllib.error
from typing import Optional, Tuple

DB_FILE = pathlib.Path("articles.db")
CONTENT_DIR = pathlib.Path("content")
IMAGES_DIR = pathlib.Path("images")

MAX_IMAGE_SIZE = 50_000  # 50KB limit per image


def save_article_content(content: str, article_id: int, source: str) -> str:
    """Save article content to disk, return file path."""
    filename = f"{source.lower().replace(' ', '_')}_{article_id}.txt"
    filepath = CONTENT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return str(filepath)


def fetch_image(image_url: str, article_id: int, article_link: Optional[str] = None) -> Optional[Tuple[str, int]]:
    """
    Fetch image from URL, resize if needed, save to disk.
    Returns (filepath, size_in_bytes) or None if failed.
    
    Args:
        image_url: The image URL to fetch
        article_id: The article ID for naming the image file
        article_link: Optional article link to use for constructing absolute URLs
    """
    try:
        # Skip data URLs and invalid URLs
        if not image_url or image_url.startswith("data:"):
            return None
        
        # Make URL absolute if needed
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        elif image_url.startswith("/"):
            # Try to construct absolute URL from article link
            if article_link:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(article_link)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    image_url = base_url + image_url
                except Exception:
                    # If construction fails, skip the image
                    return None
            else:
                # Can't make absolute without base URL
                return None
        
        # Fetch image
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            image_data = response.read()
        
        # Check if within size limit
        if len(image_data) > MAX_IMAGE_SIZE:
            # Try to compress using PIL if available
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(image_data))
                
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = rgb_img
                
                # Resize if too large
                max_dimension = 800
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Save as JPEG with quality adjustment
                output = io.BytesIO()
                quality = 85
                while quality > 50:
                    output.seek(0)
                    output.truncate(0)
                    img.save(output, format="JPEG", quality=quality)
                    if output.tell() <= MAX_IMAGE_SIZE:
                        break
                    quality -= 5
                
                image_data = output.getvalue()
            except Exception:
                # PIL not available or compression failed, skip this image
                return None
        
        # Generate filename
        hash_digest = hashlib.md5(image_url.encode()).hexdigest()[:8]
        ext = ".jpg"
        if b"\x89PNG" in image_data[:10]:
            ext = ".png"
        elif b"GIF" in image_data[:10]:
            ext = ".gif"
        
        filename = f"article_{article_id}_{hash_digest}{ext}"
        filepath = IMAGES_DIR / filename
        
        # Save image
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        return (str(filepath), len(image_data))
    
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        return None


def extract_image_url(html_content: str) -> Optional[str]:
    """Extract the most likely article image URL from HTML content.
    
    Prioritizes:
    1. Open Graph (og:image) meta tag - the official article image
    2. Images from picture tags (responsive images) - usually real content
    3. Images with recent dates - likely actual article photos
    4. Images with descriptive alt text - likely not logos
    5. Larger images - more likely to be article photos than tiny logos
    """
    import re
    from datetime import datetime
    
    current_year = str(datetime.now().year)
    
    # Strategy 0: Look for Open Graph image (most reliable)
    og_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html_content, re.IGNORECASE)
    if og_match:
        og_image = og_match.group(1)
        if og_image and not any(skip in og_image.lower() for skip in ['placeholder', 'logo', 'icon', 'sponsor', 'avatar', 'flag']):
            return og_image
    
    # Strategy 1: Look for images in <picture> tags (modern responsive images)
    picture_imgs = re.findall(
        r'<picture[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"',
        html_content,
        re.IGNORECASE | re.DOTALL
    )
    if picture_imgs:
        scored_images = []
        for src, alt in picture_imgs:
            score = 0
            
            # Skip obvious non-article images
            if any(skip in src.lower() for skip in ['logo', 'icon', 'sponsor', 'avatar', 'flag']):
                continue
            
            # Bonus: Has descriptive alt text
            if alt and len(alt) > 15:
                score += 50
            
            # Bonus: Common content CDNs
            if any(cdn in src.lower() for cdn in ['cdn', 'cloudfront', 'mos.cms', 'futurecdn']):
                score += 40
            
            if score > 0:
                scored_images.append((score, src))
        
        if scored_images:
            scored_images.sort(reverse=True)
            return scored_images[0][1]
    
    # Strategy 2: Find all img tags with src and alt attributes
    imgs = re.findall(
        r'<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"',
        html_content,
        re.IGNORECASE
    )
    
    if not imgs:
        return None
    
    # Score each image
    scored_images = []
    for src, alt in imgs:
        score = 0
        
        # Skip obvious non-article images
        if any(skip in src.lower() for skip in ['placeholder', 'logo', 'icon', 'sponsor', 'avatar', 'flag']):
            continue
        if 'static/assets/images' in src:
            continue
        
        # Bonus: Recent date (current year or previous year)
        if current_year in src or str(int(current_year) - 1) in src:
            score += 100
        
        # Bonus: Has descriptive alt text (not just category names)
        if alt and len(alt) > 15:
            score += 50
        elif alt:
            score += 10
        
        # Bonus: Has dimension hints suggesting real image (not tiny logo)
        if any(d in src for d in ['1500', '1200', '1024', '800', '600', '400']):
            score += 30
        
        # Bonus: Common news/content CDNs
        if any(cdn in src.lower() for cdn in ['cloudfront', 'cdn', 'mos.cms', 'futurecdn', 'tinifycdn']):
            score += 20
        
        if score > 0:
            scored_images.append((score, src))
    
    if scored_images:
        # Return highest scored image
        scored_images.sort(reverse=True)
        return scored_images[0][1]
    
    # Fallback: return first non-skipped image
    for src, alt in imgs:
        if not any(skip in src.lower() for skip in ['placeholder', 'logo', 'icon', 'sponsor', 'avatar']):
            return src
    
    # Last resort: return first image
    return imgs[0][0] if imgs else None


def insert_article(
    title: str,
    date_iso: str,
    source: str,
    link: str,
    content: str,
    snippet: str,
    image_url: Optional[str] = None,
    summary: Optional[str] = None,
) -> Optional[int]:
    """
    Insert article into database, save content and image.
    Returns article_id or None if duplicate link exists.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if link already exists
        cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
        if cursor.fetchone():
            conn.close()
            return None
        
        # Save content to disk
        # Generate a temp ID for filename
        cursor.execute("SELECT MAX(id) FROM articles")
        max_id = cursor.fetchone()[0] or 0
        temp_id = max_id + 1
        
        content_file = save_article_content(content, temp_id, source)
        
        # Fetch and save image if URL provided
        image_file = None
        image_size = None
        if image_url:
            result = fetch_image(image_url, temp_id, article_link=link)
            if result:
                image_file, image_size = result
        
        # Use snippet as summary if not provided
        if not summary:
            summary = snippet
        
        # Insert into database
        cursor.execute("""
            INSERT INTO articles 
            (title, date_iso, source, link, content_file, image_file, image_size, snippet, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, date_iso, source, link, content_file, image_file, image_size, snippet, summary))
        
        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return article_id
    
    except Exception as e:
        conn.close()
        print(f"Error inserting article: {e}")
        return None


def get_recent_articles(limit: int = 20, source: Optional[str] = None) -> list[dict]:
    """Get recent articles from database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if source:
        cursor.execute("""
            SELECT * FROM articles 
            WHERE source = ? 
            ORDER BY date_iso DESC 
            LIMIT ?
        """, (source, limit))
    else:
        cursor.execute("""
            SELECT * FROM articles 
            ORDER BY date_iso DESC 
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_articles_by_source(limit_per_source: int = 3) -> dict[str, list[dict]]:
    """Get recent articles grouped by source."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get distinct sources
    cursor.execute("SELECT DISTINCT source FROM articles ORDER BY source")
    sources = [row[0] for row in cursor.fetchall()]
    
    result = {}
    for source in sources:
        cursor.execute("""
            SELECT * FROM articles 
            WHERE source = ? 
            ORDER BY date_iso DESC 
            LIMIT ?
        """, (source, limit_per_source))
        
        result[source] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return result


def delete_old_articles(days: int = 7) -> int:
    """Delete articles older than N days."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM articles 
        WHERE created_at < datetime('now', '-' || ? || ' days')
    """, (days,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted
