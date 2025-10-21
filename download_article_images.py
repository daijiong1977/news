#!/usr/bin/env python3
"""
Download article images from article URLs
Extracts images from HTML content and saves them locally
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

# Environment detection
if os.path.exists('/var/www/news/articles.db'):
    # EC2 Server
    DB_PATH = '/var/www/news/articles.db'
    IMAGES_DIR = Path('/var/www/news/article_images')
else:
    # Local Mac
    DB_PATH = '/Users/jidai/news/articles.db'
    IMAGES_DIR = Path('/Users/jidai/news/article_images')

IMAGES_DIR.mkdir(exist_ok=True)

def download_article_image(article_id, article_url, title):
    """Download image from article URL"""
    try:
        # Fetch the article page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(article_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Parse HTML to find images
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the main article image
        img_tag = None
        
        # Try meta og:image first (most common)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            img_tag = {'src': img_url, 'url': img_url}
        
        # Try to find first substantial image in article content
        if not img_tag:
            # Look for images in article body/content divs
            article_content = soup.find('article') or soup.find('div', class_='article-content') or soup.find('div', class_='entry-content')
            
            if article_content:
                for img in article_content.find_all('img'):
                    src = img.get('src', '')
                    if src and ('cdn' in src.lower() or 'arstechnica' in src or 'jpg' in src.lower() or 'png' in src.lower()):
                        img_url = urljoin(article_url, src)
                        img_tag = {'src': img_url, 'url': img_url}
                        break
            
            # If still not found, check all images on page
            if not img_tag:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    # Skip logos, icons, and ads
                    if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'ad-']):
                        if any(pattern in src.lower() for pattern in ['cdn', 'uploads', 'wp-content', 'jpg', 'png']):
                            img_url = urljoin(article_url, src)
                            img_tag = {'src': img_url, 'url': img_url}
                            break
        
        if not img_tag:
            return None, "No image found"
        
        image_url = img_tag.get('url') or img_tag.get('src')
        
        # Download the image
        img_response = requests.get(image_url, timeout=10, headers=headers)
        img_response.raise_for_status()
        
        # Determine file extension
        content_type = img_response.headers.get('content-type', 'image/jpeg')
        ext = '.jpg'
        if 'png' in content_type:
            ext = '.png'
        elif 'webp' in content_type:
            ext = '.webp'
        
        # Save image
        filename = f"article_{article_id}{ext}"
        filepath = IMAGES_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        return {
            'filename': filename,
            'filepath': str(filepath),
            'url': image_url,
            'size': len(img_response.content)
        }, "Success"
        
    except Exception as e:
        return None, str(e)

def main():
    """Download images for all articles"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get articles that don't have images yet
    cursor.execute("""
        SELECT id, url, title FROM articles 
        WHERE image_id IS NULL
        ORDER BY pub_date DESC
        LIMIT 10
    """)
    
    articles = cursor.fetchall()
    print(f"📸 Downloading images for {len(articles)} articles...\n")
    
    for i, article in enumerate(articles, 1):
        article_id = article['id']
        url = article['url']
        title = article['title'][:50]
        
        print(f"{i}. Article {article_id}: {title}...")
        
        if not url:
            print("   ✗ No URL")
            continue
        
        result, message = download_article_image(article_id, url, article['title'])
        
        if result:
            # Insert into article_images table
            cursor.execute("""
                INSERT INTO article_images 
                (article_id, image_name, original_url, local_location, new_url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                article_id,
                result['filename'],
                result['url'],
                result['filepath'],
                f"/images/{result['filename']}"  # URL path for serving
            ))
            
            # Update article's image_id
            cursor.execute("SELECT image_id FROM article_images WHERE article_id = ? ORDER BY image_id DESC LIMIT 1", 
                          (article_id,))
            image_id_row = cursor.fetchone()
            if image_id_row:
                cursor.execute("UPDATE articles SET image_id = ? WHERE id = ?", 
                             (image_id_row[0], article_id))
            
            conn.commit()
            print(f"   ✓ Downloaded {result['size']} bytes")
        else:
            print(f"   ✗ Failed: {message}")
    
    conn.close()
    print(f"\n✅ Images saved to: {IMAGES_DIR}")

if __name__ == '__main__':
    main()
