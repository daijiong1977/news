#!/usr/bin/env python3
"""
Migration: Add category_id column to articles table.

This script adds a category_id column to link articles to categories.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path('/Users/jidai/news/articles.db')


def migrate_add_category_id():
    """Add category_id column to articles table."""
    print("\n" + "="*70)
    print("MIGRATION: Add category_id to articles table")
    print("="*70)
    
    if not DB_PATH.exists():
        print("❌ articles.db not found!")
        return False
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category_id' in columns:
            print("\n⚠️  category_id column already exists!")
            print("✅ Migration skipped (no changes needed)")
            conn.close()
            return True
        
        # Add the column
        print("\n🔨 Adding category_id column...")
        cursor.execute("""
            ALTER TABLE articles 
            ADD COLUMN category_id INTEGER
        """)
        print("  ✓ Column added")
        
        conn.commit()
        conn.close()
        
        # Verify
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        conn.close()
        
        print(f"\n✅ Migration complete!")
        print(f"   Articles table now has {len(columns)} columns:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            if col_name == 'category_id':
                print(f"   ✨ {col_name}: {col_type} (NEW)")
            else:
                print(f"   • {col_name}: {col_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False


def show_schema():
    """Display current schema."""
    print("\n" + "="*70)
    print("CURRENT ARTICLES TABLE SCHEMA")
    print("="*70)
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        
        print("\nColumn | Type | Nullable | PK")
        print("--------|------|----------|----")
        for col in columns:
            col_id, col_name, col_type, not_null, default, primary = col
            nullable = "NO" if not_null else "YES"
            pk = "✓" if primary else " "
            print(f"{col_name:15} | {col_type:10} | {nullable:8} | {pk}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    show_schema()
    
    print("\n" + "="*70)
    print("MIGRATION DETAILS")
    print("="*70)
    print("""
This migration adds a category_id column to the articles table.

Purpose:
  - Link each article to a category
  - Enable category-based filtering on homepage
  - Support category assignment per article

Column Details:
  - Name: category_id
  - Type: INTEGER
  - Nullable: YES (can be NULL for uncategorized articles)
  - Default: NULL

Relationship:
  articles.category_id → categories table

Usage After Migration:
  UPDATE articles SET category_id = 1 WHERE source = 'PBS'
  SELECT * FROM articles WHERE category_id = 2
""")
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    
    if response == 'yes':
        if migrate_add_category_id():
            print("\n✅ Migration successful!")
        else:
            print("\n❌ Migration failed!")
            exit(1)
    else:
        print("Migration cancelled.")
