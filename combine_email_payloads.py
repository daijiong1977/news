#!/usr/bin/env python3
"""
Combine multiple article email payloads into a single structured payload.
Organized by difficulty level: easy, mid, hard, CN
Includes article images with server URLs.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List

# Configuration
SERVER_DOMAIN = "http://localhost:8000"  # Flask API server
IMAGE_BASE_PATH = "/api/images"  # Server endpoint

def get_article_image(article_id):
    """Get image information for an article from database."""
    try:
        conn = sqlite3.connect("articles.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT image_name, local_location 
            FROM article_images 
            WHERE article_id = ?
            LIMIT 1
        """, (article_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            image_name = row['image_name']
            server_image_url = f"{SERVER_DOMAIN}{IMAGE_BASE_PATH}/{image_name}"
            return {
                "image_name": image_name,
                "server_url": server_image_url
            }
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch image for article {article_id}: {e}")
    
    return None

def combine_email_payloads(payload_files: List[str], output_file: str):
    """
    Combine multiple article payloads into a single payload.
    Structure: {levels: {easy: [...], mid: [...], hard: [...], CN: [...]}}
    """
    
    combined = {
        "generated_at": datetime.now().isoformat(),
        "server_domain": SERVER_DOMAIN,
        "image_base_path": IMAGE_BASE_PATH,
        "article_count": len(payload_files),
        "articles": [],
        "levels": {
            "easy": [],
            "mid": [],
            "hard": [],
            "CN": []
        }
    }
    
    # Process each payload file
    for payload_file in payload_files:
        if not Path(payload_file).exists():
            print(f"⚠️  File not found: {payload_file}")
            continue
        
        with open(payload_file) as f:
            payload = json.load(f)
        
        article_id = payload.get("article_id")
        
        # Get image if not already in payload
        image_info = payload.get("image")
        if not image_info and article_id:
            image_info = get_article_image(article_id)
        
        combined["articles"].append({
            "article_id": article_id,
            "image": image_info,
            "levels_available": list(payload.get("levels", {}).keys())
        })
        
        # Organize by level
        for level in ["easy", "mid", "hard", "CN"]:
            if level in payload.get("levels", {}):
                article_content = payload["levels"][level]
                article_content["article_id"] = article_id
                if image_info:
                    article_content["image"] = image_info
                combined["levels"][level].append(article_content)
    
    # Save combined payload
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Combined payload saved: {output_file}")
    print(f"\nPayload structure:")
    print(f"  Server domain: {SERVER_DOMAIN}")
    print(f"  Image base path: {IMAGE_BASE_PATH}")
    print(f"  Total articles: {combined['article_count']}")
    for level in ["easy", "mid", "hard", "CN"]:
        count = len(combined["levels"][level])
        print(f"  {level}: {count} article(s)")
        for article in combined["levels"][level]:
            aid = article.get("article_id")
            title = article.get("title", "")[:50]
            summary_len = len(article.get("summary", ""))
            image_info = article.get("image")
            img_str = f"✓ {image_info['image_name']}" if image_info else "✗ no image"
            print(f"    - Article {aid}: {img_str} | title={len(title)}c, summary={summary_len}c")

if __name__ == "__main__":
    import sys
    
    payload_files = [
        "payloads/email_article_9_payload.json",
        "payloads/email_article_8_payload.json"
    ]
    
    output_file = "payloads/email_combined_payload.json"
    
    combine_email_payloads(payload_files, output_file)
