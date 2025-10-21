#!/usr/bin/env python3
"""
Migrate summaries from deepseek_feedback table to article_summaries table
Creates entries for all difficulty and language combinations
"""

import sqlite3
import pathlib

DB_FILE = pathlib.Path("articles.db")

def migrate_summaries():
    """Migrate deepseek_feedback summaries to article_summaries table"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all deepseek_feedback records
    cursor.execute("""
        SELECT article_id, summary_en, summary_zh 
        FROM deepseek_feedback 
        WHERE summary_en IS NOT NULL OR summary_zh IS NOT NULL
    """)
    
    feedback_records = cursor.fetchall()
    print(f"Found {len(feedback_records)} deepseek_feedback records")
    
    # Get all difficulty and language combinations
    cursor.execute("SELECT difficulty_id FROM difficulty_levels ORDER BY difficulty_id")
    difficulties = cursor.fetchall()
    
    cursor.execute("SELECT language_id FROM languages ORDER BY language_id")
    languages = cursor.fetchall()
    
    print(f"Difficulty levels: {len(difficulties)}")
    print(f"Languages: {len(languages)}")
    
    count = 0
    # For each article with feedback
    for feedback in feedback_records:
        article_id = feedback['article_id']
        summary_en = feedback['summary_en']
        summary_zh = feedback['summary_zh']
        
        # Create entry for each difficulty/language combination
        for diff in difficulties:
            difficulty_id = diff['difficulty_id']
            
            # English summary
            if summary_en:
                cursor.execute("""
                    INSERT OR REPLACE INTO article_summaries 
                    (article_id, difficulty_id, language_id, summary, generated_at)
                    VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (article_id, difficulty_id, summary_en))
                count += 1
            
            # Chinese summary
            if summary_zh:
                cursor.execute("""
                    INSERT OR REPLACE INTO article_summaries 
                    (article_id, difficulty_id, language_id, summary, generated_at)
                    VALUES (?, ?, 2, ?, CURRENT_TIMESTAMP)
                """, (article_id, difficulty_id, summary_zh))
                count += 1
        
        print(f"✓ Article {article_id}: Created {len(difficulties) * 2} summary entries")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration complete! Created {count} summary entries")

if __name__ == '__main__':
    migrate_summaries()
