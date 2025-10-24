#!/usr/bin/env python3
"""
Generate email payload from Deepseek response JSON.
Extract title, summary, and image from each level (easy, mid, hard, CN).
Includes server domain paths for images.
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Configuration
DB_PATH = "/Users/jidai/news/articles.db"
SERVER_DOMAIN = "http://localhost:8000"  # Flask API server
IMAGE_BASE_PATH = "/api/images"  # Server endpoint for images

def get_article_image(article_id):
    """Get image information for an article from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT image_name, local_location, new_url 
            FROM article_images 
            WHERE article_id = ?
            LIMIT 1
        """, (article_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            image_name = row['image_name']
            local_location = row['local_location']
            # Build server URL
            server_image_url = f"{SERVER_DOMAIN}{IMAGE_BASE_PATH}/{image_name}"
            return {
                "image_name": image_name,
                "local_path": local_location,
                "server_url": server_image_url
            }
    except Exception as e:
        print(f"⚠️  Error fetching image for article {article_id}: {e}")
    
    return None

def extract_email_payload(response_file, article_id=None):
    """Extract title, summary, and image from each level to create email payload."""
    
    with open(response_file) as f:
        response = json.load(f)
    
    levels = response['article_analysis']['levels']
    
    payload = {
        "article_id": article_id,
        "generated_at": datetime.now().isoformat(),
        "image": None,
        "levels": {}
    }
    
    # Extract from each level
    for level in ['easy', 'mid', 'hard', 'CN']:
        if level in levels:
            payload["levels"][level] = {
                "title": levels[level].get("title", ""),
                "summary": levels[level].get("summary", "")
            }
    
    # Try to extract article_id from filename if not provided
    if not article_id:
        filename = Path(response_file).name
        if 'article_' in filename:
            parts = filename.split('_')
            if len(parts) > 2:
                try:
                    article_id = int(parts[2])
                    payload["article_id"] = article_id
                except:
                    pass
    
    # Get image for the article
    if article_id:
        image_info = get_article_image(article_id)
        if image_info:
            payload["image"] = image_info
    
    return payload

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_email_payload.py <response_json_file> [output_file]")
        sys.exit(1)
    
    response_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else response_file.replace('.json', '_email_payload.json')
    
    if not Path(response_file).exists():
        print(f"✗ File not found: {response_file}")
        sys.exit(1)
    
    try:
        payload = extract_email_payload(response_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Email payload generated: {output_file}")
        print(f"\nPayload structure:")
        print(f"  article_id: {payload['article_id']}")
        if payload.get('image'):
            print(f"  image: {payload['image']['image_name']}")
            print(f"    └─ server_url: {payload['image']['server_url']}")
        else:
            print(f"  image: None")
        print(f"  levels: {list(payload['levels'].keys())}")
        for level in payload['levels']:
            title_len = len(payload['levels'][level]['title'])
            summary_len = len(payload['levels'][level]['summary'])
            print(f"    {level}: title={title_len}c, summary={summary_len}c")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
