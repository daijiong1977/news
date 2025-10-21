#!/usr/bin/env python3
"""
Clean up database and prepare for fresh data population
This script:
1. Clears all processed data (deepseek_feedback, article_summaries, keywords, etc.)
2. Keeps article basic data intact
3. Resets deepseek_processed flag
4. Prepares database for fresh processing
"""

import sqlite3
import pathlib

DB_FILE = pathlib.Path("articles.db")

def cleanup_database():
    """Clean up processed data from database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🧹 Database Cleanup Starting...")
    print("=" * 60)
    
    tables_to_clear = [
        ('deepseek_feedback', 'deepseek feedback records'),
        ('article_summaries', 'article summaries'),
        ('keywords', 'keywords'),
        ('questions', 'quiz questions'),
        ('background_read', 'background reading'),
        ('comments', 'comments'),
        ('choices', 'question choices'),
    ]
    
    for table, description in tables_to_clear:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute(f"DELETE FROM {table}")
            print(f"✓ Cleared {table:25} ({count} records)")
        except Exception as e:
            print(f"⚠️  {table:25} - {str(e)}")
    
    # Reset deepseek_processed flag
    cursor.execute("UPDATE articles SET deepseek_processed = 0, processed_at = NULL")
    print(f"✓ Reset deepseek_processed flag for all articles")
    
    # Verify articles are intact
    cursor.execute("SELECT COUNT(*) FROM articles")
    article_count = cursor.fetchone()[0]
    print(f"✓ Articles preserved: {article_count} articles")
    
    # Verify images are intact
    cursor.execute("SELECT COUNT(*) FROM article_images")
    image_count = cursor.fetchone()[0]
    print(f"✓ Images preserved: {image_count} images")
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("✅ Database cleanup complete!")
    print("\n📋 Next steps:")
    print("   1. Run: python3 process_single_article.py <article_id>")
    print("   2. Then: python3 populate_all_summary_tables.py")
    print("   3. Restart: db_server")

if __name__ == '__main__':
    cleanup_database()
