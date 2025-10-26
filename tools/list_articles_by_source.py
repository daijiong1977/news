#!/usr/bin/env python3
"""List latest 3 articles for each source from database."""

import sqlite3
import sys

def main():
    db_path = 'articles.db'
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all unique sources
        cursor.execute("SELECT DISTINCT source FROM articles ORDER BY source")
        sources = [row['source'] for row in cursor.fetchall()]
        
        print("\nLatest 3 articles per source:")
        print("=" * 90)
        
        for source in sources:
            print(f"\nSource: {source}")
            print("-" * 90)
            
            cursor.execute("""
                SELECT id, title, pubdate 
                FROM articles 
                WHERE source = ? 
                ORDER BY pubdate DESC 
                LIMIT 3
            """, (source,))
            
            rows = cursor.fetchall()
            for i, row in enumerate(rows, 1):
                title = row['title'][:65] + '...' if len(row['title']) > 65 else row['title']
                pubdate = row['pubdate'][:10] if row['pubdate'] else 'N/A'
                print(f"  {i}. [ID: {row['id']}] {title}")
                print(f"     Date: {pubdate}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
