#!/usr/bin/env python3
"""Initialize SQLite database for news articles."""

import sqlite3
import pathlib

DB_FILE = pathlib.Path("articles.db")
CONTENT_DIR = pathlib.Path("content")
IMAGES_DIR = pathlib.Path("images")

def init_database():
    """Create database and tables if they don't exist."""
    # Create directories
    CONTENT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    # Create/connect to database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date_iso TEXT NOT NULL,
            source TEXT NOT NULL,
            link TEXT NOT NULL UNIQUE,
            content_file TEXT,
            image_file TEXT,
            image_size INTEGER,
            snippet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index on date for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date_iso ON articles(date_iso DESC)
    """)
    
    # Create index on source for filtering
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_source ON articles(source)
    """)
    
    # Create index on link to ensure uniqueness
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_link ON articles(link)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database initialized: {DB_FILE}")
    print(f"✓ Created directories: {CONTENT_DIR}, {IMAGES_DIR}")

if __name__ == "__main__":
    init_database()
