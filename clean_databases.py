#!/usr/bin/env python3
"""
Clean all tables in local databases.

This script:
1. Deletes all data from articles.db tables
2. Deletes all data from subscriptions.db tables
3. Keeps the schema intact (tables remain)
4. Optional: Drop and recreate tables for fresh state
"""

import sqlite3
import sys
from pathlib import Path

# Database paths
ARTICLES_DB = Path('/Users/jidai/news/articles.db')
SUBSCRIPTIONS_DB = Path('/Users/jidai/news/subscriptions.db')


def clean_articles_db(drop_tables=False):
    """Clean articles.db - the main database."""
    print("\n" + "="*70)
    print("CLEANING: articles.db")
    print("="*70)
    
    if not ARTICLES_DB.exists():
        print("❌ articles.db not found!")
        return False
    
    try:
        conn = sqlite3.connect(str(ARTICLES_DB))
        cursor = conn.cursor()
        
        if drop_tables:
            print("\n🗑️  Dropping tables (fresh start)...")
            tables = ['article_summaries', 'articles']
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"  ✓ Dropped {table}")
                except Exception as e:
                    print(f"  ⚠️  Error dropping {table}: {e}")
            
            # Recreate tables
            print("\n🔨 Recreating tables...")
            cursor.execute("""
                CREATE TABLE articles (
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
                    processed_at TEXT,
                    category_id INTEGER
                )
            """)
            print("  ✓ Created articles table")
            
            cursor.execute("""
                CREATE TABLE article_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    difficulty TEXT,
                    language TEXT,
                    summary TEXT,
                    generated_at TEXT,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            """)
            print("  ✓ Created article_summaries table")
        else:
            print("\n🧹 Clearing data (keeping schema)...")
            cursor.execute("DELETE FROM article_summaries")
            print(f"  ✓ Cleared article_summaries ({cursor.rowcount} rows deleted)")
            
            cursor.execute("DELETE FROM articles")
            print(f"  ✓ Cleared articles ({cursor.rowcount} rows deleted)")
        
        conn.commit()
        conn.close()
        
        # Verify
        conn = sqlite3.connect(str(ARTICLES_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM article_summaries")
        summary_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\n✅ articles.db cleaned!")
        print(f"   - articles table: {article_count} rows")
        print(f"   - article_summaries table: {summary_count} rows")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning articles.db: {e}")
        return False


def clean_subscriptions_db(drop_tables=False):
    """Clean subscriptions.db - secondary database."""
    print("\n" + "="*70)
    print("CLEANING: subscriptions.db")
    print("="*70)
    
    if not SUBSCRIPTIONS_DB.exists():
        print("⚠️  subscriptions.db not found (optional)")
        return True
    
    try:
        conn = sqlite3.connect(str(SUBSCRIPTIONS_DB))
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        
        if drop_tables:
            print(f"\n🗑️  Dropping {len(tables)} tables...")
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"  ✓ Dropped {table}")
                except Exception as e:
                    print(f"  ⚠️  Error dropping {table}: {e}")
            
            print("\n🔨 Recreating tables...")
            # Recreate all tables with fresh schemas
            cursor.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    website TEXT,
                    description TEXT,
                    color TEXT,
                    emoji TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✓ Created categories table")
            
            cursor.execute("""
                CREATE TABLE article_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    difficulty TEXT,
                    language TEXT,
                    summary TEXT,
                    keywords TEXT,
                    background TEXT,
                    pro_arguments TEXT,
                    con_arguments TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✓ Created article_summaries table")
            
            cursor.execute("""
                CREATE TABLE quiz_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    difficulty TEXT,
                    question_number INTEGER,
                    question_text TEXT,
                    options TEXT,
                    correct_answer INTEGER,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✓ Created quiz_questions table")
            
            cursor.execute("""
                CREATE TABLE articles_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_article_id INTEGER,
                    title TEXT NOT NULL,
                    date TEXT,
                    source TEXT,
                    image_file TEXT,
                    category_id INTEGER,
                    original_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            print("  ✓ Created articles_enhanced table")
            
            cursor.execute("""
                CREATE TABLE subscriptions_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    age_group TEXT,
                    difficulty_level TEXT,
                    interests TEXT,
                    frequency TEXT DEFAULT 'daily',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sent TIMESTAMP,
                    confirmed BOOLEAN DEFAULT 0
                )
            """)
            print("  ✓ Created subscriptions_enhanced table")
            
            cursor.execute("""
                CREATE TABLE email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    age_group TEXT,
                    difficulty_level TEXT,
                    subject TEXT,
                    status TEXT,
                    email_id TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✓ Created email_logs table")
        else:
            print(f"\n🧹 Clearing data from {len(tables)} tables...")
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    count = cursor.rowcount
                    print(f"  ✓ Cleared {table} ({count} rows deleted)")
                except Exception as e:
                    print(f"  ⚠️  Error clearing {table}: {e}")
        
        conn.commit()
        conn.close()
        
        # Verify
        conn = sqlite3.connect(str(SUBSCRIPTIONS_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        
        print(f"\n✅ subscriptions.db cleaned!")
        print(f"   - Tables: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"     • {table}: {count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning subscriptions.db: {e}")
        return False


def show_status():
    """Show current database status."""
    print("\n" + "="*70)
    print("CURRENT DATABASE STATUS")
    print("="*70)
    
    # Check articles.db
    if ARTICLES_DB.exists():
        conn = sqlite3.connect(str(ARTICLES_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM article_summaries")
        summary_count = cursor.fetchone()[0]
        conn.close()
        print(f"\n📦 articles.db")
        print(f"   - articles: {article_count} rows")
        print(f"   - article_summaries: {summary_count} rows")
    else:
        print(f"\n❌ articles.db not found")
    
    # Check subscriptions.db
    if SUBSCRIPTIONS_DB.exists():
        conn = sqlite3.connect(str(SUBSCRIPTIONS_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        print(f"\n📦 subscriptions.db")
        print(f"   - Tables: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"     • {table}: {count} rows")
        conn.close()
    else:
        print(f"\n❌ subscriptions.db not found")


if __name__ == "__main__":
    show_status()
    
    print("\n" + "="*70)
    print("CLEANING OPTIONS")
    print("="*70)
    print("\nUsage:")
    print("  python3 clean_databases.py                    # Clear all data (keep schema)")
    print("  python3 clean_databases.py --drop             # Drop all tables, recreate fresh")
    print("  python3 clean_databases.py --status           # Show current status only")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--status':
            sys.exit(0)
        elif sys.argv[1] == '--drop':
            print("\n⚠️  WARNING: This will DROP and RECREATE all tables!")
            response = input("Are you sure? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Aborted.")
                sys.exit(0)
            
            success = clean_articles_db(drop_tables=True)
            success = clean_subscriptions_db(drop_tables=True) and success
            
            if success:
                print("\n" + "="*70)
                print("✅ ALL DATABASES DROPPED AND RECREATED FRESH!")
                print("="*70)
                show_status()
            else:
                print("\n❌ Some errors occurred during cleaning")
                sys.exit(1)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Default: clear all data but keep schema
        response = input("\nClear all data? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            sys.exit(0)
        
        success = clean_articles_db(drop_tables=False)
        success = clean_subscriptions_db(drop_tables=False) and success
        
        if success:
            print("\n" + "="*70)
            print("✅ ALL DATABASES CLEANED!")
            print("="*70)
            show_status()
        else:
            print("\n❌ Some errors occurred during cleaning")
            sys.exit(1)
