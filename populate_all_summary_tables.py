#!/usr/bin/env python3
"""
Populate all article summary tables from deepseek_feedback
Maps deepseek_feedback data to:
- article_summaries (summary by difficulty and language)
- keywords (key_words parsed)
- questions (multiple_choice_questions parsed)
- background_read (background_reading)
"""

import sqlite3
import json
import pathlib

DB_FILE = pathlib.Path("articles.db")

def populate_from_deepseek():
    """Populate all tables from deepseek_feedback data"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if deepseek_feedback table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='deepseek_feedback'
    """)
    
    if not cursor.fetchone():
        print("❌ deepseek_feedback table not found!")
        conn.close()
        return
    
    # Get all deepseek_feedback records
    cursor.execute("""
        SELECT * FROM deepseek_feedback 
        WHERE summary_en IS NOT NULL OR summary_zh IS NOT NULL
    """)
    
    feedback_records = cursor.fetchall()
    print(f"📊 Found {len(feedback_records)} deepseek_feedback records\n")
    
    # Get difficulty and language IDs
    cursor.execute("SELECT difficulty_id, difficulty FROM difficulty_levels ORDER BY difficulty_id")
    difficulties = {row['difficulty_id']: row['difficulty'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT language_id, language FROM languages ORDER BY language_id")
    languages = {row['language_id']: row['language'] for row in cursor.fetchall()}
    
    print(f"📋 Schema Info:")
    print(f"   Difficulties: {difficulties}")
    print(f"   Languages: {languages}\n")
    
    total_summaries = 0
    total_keywords = 0
    total_questions = 0
    total_background = 0
    
    # Process each feedback record
    for feedback in feedback_records:
        article_id = feedback['article_id']
        print(f"📄 Article {article_id}:")
        
        # ===== SUMMARIES =====
        # For each difficulty level, create summary entries
        for diff_id, diff_name in difficulties.items():
            # English summary
            if feedback['summary_en']:
                cursor.execute("""
                    INSERT OR REPLACE INTO article_summaries 
                    (article_id, difficulty_id, language_id, summary, generated_at)
                    VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (article_id, diff_id, feedback['summary_en']))
                total_summaries += 1
            
            # Chinese summary
            if feedback['summary_zh']:
                cursor.execute("""
                    INSERT OR REPLACE INTO article_summaries 
                    (article_id, difficulty_id, language_id, summary, generated_at)
                    VALUES (?, ?, 2, ?, CURRENT_TIMESTAMP)
                """, (article_id, diff_id, feedback['summary_zh']))
                total_summaries += 1
        
        print(f"   ✓ Summaries: {len(difficulties) * 2} entries")
        
        # ===== KEYWORDS =====
        if feedback['key_words']:
            try:
                keywords_list = json.loads(feedback['key_words'])
                for diff_id in difficulties.keys():
                    for kw in keywords_list:
                        cursor.execute("""
                            INSERT OR REPLACE INTO keywords 
                            (article_id, difficulty_id, word, explanation)
                            VALUES (?, ?, ?, ?)
                        """, (
                            article_id,
                            diff_id,
                            kw.get('word', ''),
                            kw.get('explanation', '')
                        ))
                        total_keywords += 1
                print(f"   ✓ Keywords: {len(keywords_list) * len(difficulties)} entries")
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Failed to parse keywords: {e}")
        
        # ===== QUESTIONS =====
        if feedback['multiple_choice_questions']:
            try:
                questions_list = json.loads(feedback['multiple_choice_questions'])
                for diff_id in difficulties.keys():
                    for q in questions_list:
                        cursor.execute("""
                            INSERT OR REPLACE INTO questions 
                            (article_id, difficulty_id, question_text, created_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            article_id,
                            diff_id,
                            q.get('question', '')
                        ))
                        total_questions += 1
                print(f"   ✓ Questions: {len(questions_list) * len(difficulties)} entries")
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Failed to parse questions: {e}")
        
        # ===== BACKGROUND READING =====
        if feedback['background_reading']:
            for diff_id in difficulties.keys():
                cursor.execute("""
                    INSERT OR REPLACE INTO background_read 
                    (article_id, difficulty_id, background_text, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (article_id, diff_id, feedback['background_reading']))
                total_background += 1
            print(f"   ✓ Background: {len(difficulties)} entries")
        
        print()
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 60)
    print(f"📊 Summary Statistics:")
    print(f"   Summaries:  {total_summaries} entries")
    print(f"   Keywords:   {total_keywords} entries")
    print(f"   Questions:  {total_questions} entries")
    print(f"   Background: {total_background} entries")
    print(f"   TOTAL:      {total_summaries + total_keywords + total_questions + total_background} entries")

if __name__ == '__main__':
    populate_from_deepseek()
