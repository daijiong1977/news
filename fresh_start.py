#!/usr/bin/env python3
"""
Fresh start: Delete all articles/images and re-crawl from scratch
"""

import sqlite3
import os
import shutil
from pathlib import Path

def delete_articles_and_images():
    """Delete all articles and images, keep only schema"""
    
    print("🗑️  Deleting all articles and images...")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    
    # Delete all processed data
    tables_to_clear = [
        'article_summaries',
        'keywords',
        'questions',
        'background_read',
        'article_images',
        'comments',
        'choices'
    ]
    
    for table in tables_to_clear:
        try:
            c.execute(f'DELETE FROM {table}')
            count = c.rowcount
            print(f"✓ Cleared {table:25s} ({count} records)")
        except Exception as e:
            print(f"✗ Error clearing {table}: {e}")
    
    # Delete articles
    c.execute('DELETE FROM articles')
    print(f"✓ Cleared articles           (all articles deleted)")
    
    # Reset sequences/autoincrement
    c.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
    
    conn.commit()
    conn.close()
    
    # Delete images directory
    if os.path.exists('images'):
        shutil.rmtree('images')
        print(f"✓ Deleted images directory")
    
    # Create fresh images directory
    os.makedirs('images', exist_ok=True)
    print(f"✓ Created fresh images directory")
    
    print("=" * 60)
    print("✅ Database and images cleared!\n")

def main():
    print("\n🚀 FRESH START PROCEDURE")
    print("=" * 60)
    print("This will:")
    print("  1. Delete ALL articles from database")
    print("  2. Delete ALL images")
    print("  3. Reset all processed data")
    print("=" * 60)
    
    response = input("\n⚠️  Are you sure? (type 'YES' to confirm): ").strip().upper()
    
    if response == 'YES':
        delete_articles_and_images()
        print("📋 Next steps:")
        print("   1. Run: python3 data_collector.py  (to crawl articles)")
        print("   2. Run: python3 download_article_images.py  (to get images)")
        print("   3. Process articles with Deepseek")
    else:
        print("❌ Cancelled")

if __name__ == '__main__':
    main()
