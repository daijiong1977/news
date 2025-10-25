#!/usr/bin/env python3
"""
Local status checker for the news pipeline.
Shows: total articles, processed, remaining, and file counts.
Works with local database and website directory.
"""

import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Detect if running locally or on server
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Try local paths first, fall back to server paths
if os.path.exists(os.path.join(BASE_DIR, 'articles.db')):
    DB_PATH = os.path.join(BASE_DIR, 'articles.db')
    RESPONSES_DIR = os.path.join(BASE_DIR, 'website.remote', 'responses')
    IMAGES_DIR = os.path.join(BASE_DIR, 'website.remote', 'article_image')
else:
    # Server paths
    DB_PATH = '/var/www/news/articles.db'
    RESPONSES_DIR = '/var/www/news/website/responses'
    IMAGES_DIR = '/var/www/news/website/article_image'


def get_db_stats():
    """Get article statistics from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Total articles
        cur.execute('SELECT COUNT(*) FROM articles')
        total = cur.fetchone()[0]
        
        # Processed articles
        cur.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1')
        processed = cur.fetchone()[0]
        
        # Remaining articles
        cur.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=0')
        remaining = cur.fetchone()[0]
        
        conn.close()
        return {
            'total': total,
            'processed': processed,
            'remaining': remaining
        }
    except Exception as e:
        print(f"❌ Error reading database: {e}", file=sys.stderr)
        return None


def count_files(directory, pattern):
    """Count files matching pattern in directory."""
    try:
        if not os.path.exists(directory):
            return 0
        
        path = Path(directory)
        count = 0
        
        if pattern == '*':
            count = len(list(path.glob('*')))
        else:
            count = len(list(path.glob(pattern)))
        
        return count
    except Exception as e:
        print(f"❌ Error counting files in {directory}: {e}", file=sys.stderr)
        return 0


def get_file_stats():
    """Get file statistics."""
    # Count regular JPGs (full-size images)
    jpg_count = count_files(IMAGES_DIR, '*.jpg')
    # Count mobile WebP (small images)
    webp_count = count_files(IMAGES_DIR, '*.webp')
    
    return {
        'response_json': count_files(RESPONSES_DIR, 'article_*_response.json'),
        'image_full': jpg_count,  # Full-size JPG images
        'image_mobile': webp_count,  # Mobile WebP images
        'raw_response': count_files(RESPONSES_DIR, 'raw_response_article_*.txt')
    }


def print_status():
    """Print comprehensive status report."""
    print("\n" + "="*70)
    print("📊 NEWS PIPELINE STATUS CHECK")
    print("="*70)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Location: {DB_PATH}\n")
    
    # Database stats
    print("📦 DATABASE STATISTICS:")
    print("-" * 70)
    db_stats = get_db_stats()
    
    if db_stats:
        total = db_stats['total']
        processed = db_stats['processed']
        remaining = db_stats['remaining']
        
        percent = (processed / total * 100) if total > 0 else 0
        
        print(f"  Total Articles:    {total}")
        print(f"  ✅ Processed:       {processed} ({percent:.1f}%)")
        print(f"  ⏳ Remaining:       {remaining} ({100-percent:.1f}%)")
    else:
        print("  ❌ Could not read database")
        return
    
    # File stats
    print("\n📁 FILE STATISTICS:")
    print("-" * 70)
    file_stats = get_file_stats()
    
    print(f"  Response JSON:     {file_stats['response_json']} files")
    print(f"  Image Full-Size:   {file_stats['image_full']} JPG files")
    print(f"  Image Mobile:      {file_stats['image_mobile']} WebP files")
    print(f"  Raw Response:      {file_stats['raw_response']} files (parse errors)")
    
    # Summary
    print("\n📈 SUMMARY:")
    print("-" * 70)
    
    if file_stats['raw_response'] > 0:
        print(f"  ⚠️  {file_stats['raw_response']} articles have JSON parse errors")
        print(f"     See {RESPONSES_DIR}/raw_response_*.txt")
    else:
        print("  ✅ No JSON parse errors detected")
    
    if file_stats['response_json'] == processed:
        print(f"  ✅ All {processed} processed articles have response files")
    else:
        print(f"  ⚠️  Response files ({file_stats['response_json']}) != Processed DB ({processed})")
    
    if file_stats['image_full'] > 0:
        print(f"  ✅ {file_stats['image_full']} full-size images, {file_stats['image_mobile']} mobile versions")
    else:
        print(f"  ℹ️  No images downloaded yet (expected after data collection phase)")
    
    # Progress bar
    if total > 0:
        bar_length = 50
        filled = int(bar_length * processed / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n  Progress: [{bar}] {percent:.1f}%\n")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    print_status()
