#!/usr/bin/env python3
"""Migrate database to add summary column."""

import sqlite3
import pathlib

DB_FILE = pathlib.Path("articles.db")

def migrate_add_summary():
    """Add summary column if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if summary column exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'summary' not in columns:
            cursor.execute("""
                ALTER TABLE articles ADD COLUMN summary TEXT
            """)
            print("✓ Added 'summary' column to articles table")
        else:
            print("✓ 'summary' column already exists")
        
        conn.commit()
    except Exception as e:
        print(f"✗ Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_summary()
