#!/usr/bin/env python3
"""
Insert data from a saved response JSON file into the database.
Use this AFTER verifying the response structure is correct.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

if len(sys.argv) < 2:
    print("Usage: python3 insert_from_response.py <response_json_file>")
    print("\nExample:")
    print("  python3 insert_from_response.py response_article_1_20251020_123456.json")
    sys.exit(1)

# Configuration
DB_PATH = '/Users/jidai/news/articles.db'
response_file = sys.argv[1]

# Map difficulty text to difficulty_id
DIFFICULTY_MAP = {
    'easy': 1,
    'mid': 2,
    'hard': 3
}

# Map language text to language_id
LANGUAGE_MAP = {
    'en': 1,
    'zh': 2
}

def extract_zh_title_from_response(response_data, article_id):
    """Try to extract or generate Chinese title from response"""
    
    # Check if zh_title exists in article_analysis
    if 'article_analysis' in response_data:
        aa = response_data['article_analysis']
        if 'zh_title' in aa and aa['zh_title']:
            return aa['zh_title']
    
    # If zh_title not found, try to generate from zh_hard
    try:
        if 'article_analysis' in response_data:
            aa = response_data['article_analysis']
            if 'levels' in aa and 'hard' in aa['levels']:
                hard = aa['levels']['hard']
                if 'zh_hard' in hard and hard['zh_hard']:
                    # Extract first sentence (often contains the topic)
                    zh_text = hard['zh_hard']
                    # Find first sentence end (。or ，)
                    for sep in ['。', '，']:
                        if sep in zh_text:
                            first_part = zh_text[:zh_text.index(sep) + 1]
                            if len(first_part) < 100:  # Only if reasonably short
                                return first_part
                    # If no separator, take first 50 chars
                    if len(zh_text) > 50:
                        return zh_text[:50] + '...'
    except:
        pass
    
    return None

def update_zh_title_in_db(article_id, zh_title):
    """Update article with Chinese title"""
    if not zh_title:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE articles 
            SET zh_title = ?
            WHERE id = ?
        """, (zh_title, article_id))
        conn.commit()
        return True
    finally:
        conn.close()

def insert_data_into_db(article_id, response_data):
    """Parse response and insert into database
    
    Expected format:
    {
      "article_analysis": {
        "title": "...",
        "levels": {
          "easy": { "summary", "keywords", "questions", "background_reading", "perspectives" },
          "mid": { "summary", "keywords", "questions", "background_reading", "analysis", "perspectives" },
          "hard": { "summary", "keywords", "questions", "background_reading", "analysis", "zh_hard", "perspectives" }
        }
      }
    }
    """
    
    print("\n" + "="*70)
    print("INSERTING DATA INTO DATABASE")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Expect article_analysis with nested levels
        if 'article_analysis' not in response_data:
            print("ERROR: Response missing 'article_analysis' key")
            print(f"Available keys: {list(response_data.keys())}")
            return False
        
        aa = response_data['article_analysis']
        
        # Update article with zh_title if provided
        if 'zh_title' in aa and aa['zh_title']:
            cursor.execute("""
                UPDATE articles 
                SET zh_title = ?
                WHERE id = ?
            """, (aa['zh_title'], article_id))
            print(f"✓ Updated article zh_title")
        
        if 'levels' not in aa:
            print("ERROR: Response missing 'levels' key in article_analysis")
            print(f"Available keys: {list(aa.keys())}")
            return False
        
        levels = aa['levels']
        insert_count = 0
        
        # Process each difficulty level (easy, mid, hard)
        for level_name in ['easy', 'mid', 'hard']:
            if level_name not in levels:
                print(f"WARNING: Missing level {level_name}")
                continue
            
            level_data = levels[level_name]
            difficulty_id = DIFFICULTY_MAP.get(level_name)
            
            print(f"\n--- Processing {level_name.upper()} level (difficulty_id={difficulty_id}) ---")
            
            # 1. Insert Summaries (English and Chinese if hard)
            if 'summary' in level_data and level_data['summary']:
                # English summary
                cursor.execute("""
                    INSERT INTO article_summaries (article_id, difficulty_id, language_id, summary, generated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, difficulty_id, LANGUAGE_MAP['en'], level_data['summary'], datetime.now().isoformat()))
                insert_count += 1
                print(f"  ✓ Inserted {level_name} English summary")
                
                # Chinese summary (hard level only) - if API provides zh_hard or zh_summary
                if level_name == 'hard':
                    zh_text = level_data.get('zh_hard') or level_data.get('zh_summary') or level_data.get('zh_hard_summary')
                    if zh_text:
                        cursor.execute("""
                            INSERT INTO article_summaries (article_id, difficulty_id, language_id, summary, generated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (article_id, difficulty_id, LANGUAGE_MAP['zh'], zh_text, datetime.now().isoformat()))
                        insert_count += 1
                        print(f"  ✓ Inserted {level_name} Chinese summary")
            
            # 2. Insert Keywords
            if 'keywords' in level_data and isinstance(level_data['keywords'], list):
                for kw in level_data['keywords']:
                    term = kw.get('term') or kw.get('word') or kw.get('keyword') or ''
                    explanation = kw.get('explanation') or ''
                    if term:
                        cursor.execute("""
                            INSERT INTO keywords (article_id, difficulty_id, word, explanation)
                            VALUES (?, ?, ?, ?)
                        """, (article_id, difficulty_id, term, explanation))
                        insert_count += 1
                print(f"  ✓ Inserted {len(level_data['keywords'])} keywords")
            
            # 3. Insert Questions and Choices
            if 'questions' in level_data and isinstance(level_data['questions'], list):
                for q in level_data['questions']:
                    question_text = q.get('question') or q.get('question_text') or ''
                    if question_text:
                        cursor.execute("""
                            INSERT INTO questions (article_id, difficulty_id, question_text, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (article_id, difficulty_id, question_text, datetime.now().isoformat()))
                        insert_count += 1
                        
                        question_id = cursor.lastrowid
                        
                        # Insert choices for this question
                        options = q.get('options') or []
                        correct_answer = q.get('correct_answer') or ''
                        
                        for option in options:
                            is_correct = 1 if option == correct_answer else 0
                            cursor.execute("""
                                INSERT INTO choices (question_id, choice_text, is_correct, created_at)
                                VALUES (?, ?, ?, ?)
                            """, (question_id, option, is_correct, datetime.now().isoformat()))
                            insert_count += 1
                
                print(f"  ✓ Inserted {len(level_data['questions'])} questions with choices")
            
            # 4. Insert Background Reading
            if 'background_reading' in level_data and level_data['background_reading']:
                bg_text = level_data['background_reading']
                cursor.execute("""
                    INSERT INTO background_read (article_id, difficulty_id, background_text, created_at)
                    VALUES (?, ?, ?, ?)
                """, (article_id, difficulty_id, bg_text, datetime.now().isoformat()))
                insert_count += 1
                print(f"  ✓ Inserted background reading")
            
            # 5. Insert Article Analysis (mid and hard only)
            if level_name in ['mid', 'hard'] and 'analysis' in level_data and level_data['analysis']:
                cursor.execute("""
                    INSERT INTO article_analysis (article_id, difficulty_id, analysis_en, created_at)
                    VALUES (?, ?, ?, ?)
                """, (article_id, difficulty_id, level_data['analysis'], datetime.now().isoformat()))
                insert_count += 1
                print(f"  ✓ Inserted analysis")
            else:
                if level_name in ['mid', 'hard']:
                    print(f"  ⚠ No analysis provided by API for {level_name} level")
            
            # 6. Insert Comments (perspectives)
            # Perspectives can be either a list or dict format
            if 'perspectives' in level_data:
                perspectives = level_data['perspectives']
                perspective_count = 0
                
                if isinstance(perspectives, list):
                    # List format: [perspective1, perspective2, synthesis]
                    for idx, p in enumerate(perspectives):
                        if isinstance(p, dict):
                            attitude = p.get('attitude', 'neutral')
                            content = p.get('perspective') or p.get('content') or ''
                            if content:
                                who = f'perspective_{idx+1}' if idx < len(perspectives) - 1 else 'synthesis'
                                cursor.execute("""
                                    INSERT INTO comments (article_id, difficulty_id, attitude, com_content, who_comment, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (article_id, difficulty_id, attitude, content, who, datetime.now().isoformat()))
                                insert_count += 1
                                perspective_count += 1
                
                elif isinstance(perspectives, dict):
                    # Dict format: {perspective_1, perspective_2, synthesis}
                    # Perspective 1
                    if 'perspective_1' in perspectives and perspectives['perspective_1']:
                        p1 = perspectives['perspective_1']
                        attitude = p1.get('attitude', 'neutral')
                        content = p1.get('content') or p1.get('perspective') or ''
                        if content:
                            cursor.execute("""
                                INSERT INTO comments (article_id, difficulty_id, attitude, com_content, who_comment, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (article_id, difficulty_id, attitude, content, 'perspective_1', datetime.now().isoformat()))
                            insert_count += 1
                            perspective_count += 1
                    
                    # Perspective 2
                    if 'perspective_2' in perspectives and perspectives['perspective_2']:
                        p2 = perspectives['perspective_2']
                        attitude = p2.get('attitude', 'neutral')
                        content = p2.get('content') or p2.get('perspective') or ''
                        if content:
                            cursor.execute("""
                                INSERT INTO comments (article_id, difficulty_id, attitude, com_content, who_comment, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (article_id, difficulty_id, attitude, content, 'perspective_2', datetime.now().isoformat()))
                            insert_count += 1
                            perspective_count += 1
                    
                    # Synthesis
                    if 'synthesis' in perspectives and perspectives['synthesis']:
                        syn = perspectives['synthesis']
                        content = syn.get('content') or syn.get('synthesis') or ''
                        if content:
                            cursor.execute("""
                                INSERT INTO comments (article_id, difficulty_id, attitude, com_content, who_comment, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (article_id, difficulty_id, 'neutral', content, 'synthesis', datetime.now().isoformat()))
                            insert_count += 1
                            perspective_count += 1
                
                if perspective_count > 0:
                    print(f"  ✓ Inserted {perspective_count} perspectives/comments")
                else:
                    print(f"  ⚠ No perspectives provided by API for {level_name} level")
        
        # Update article as processed
        cursor.execute("""
            UPDATE articles 
            SET deepseek_processed = 1, processed_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), article_id))
        insert_count += 1
        
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"✓ SUCCESS: Inserted {insert_count} records for article {article_id}")
        print(f"{'='*70}")
        return True
        
    except Exception as e:
        print(f"ERROR inserting data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("INSERT FROM RESPONSE - AFTER VERIFICATION")
    print("="*70)
    
    # Load response file
    if not os.path.exists(response_file):
        print(f"ERROR: File not found: {response_file}")
        sys.exit(1)
    
    print(f"Loading response from: {response_file}")
    
    try:
        with open(response_file) as f:
            response_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in file: {e}")
        sys.exit(1)
    
    # Extract article_id from response or filename
    article_id = None
    
    # Try to get from response
    if 'article_id' in response_data:
        article_id = response_data['article_id']
    
    # Try to get from filename
    if not article_id:
        import re
        match = re.search(r'response_article_(\d+)', response_file)
        if match:
            article_id = int(match.group(1))
    
    if not article_id:
        print("ERROR: Could not determine article_id from response or filename")
        sys.exit(1)
    
    print(f"Article ID: {article_id}")
    
    # Verify article exists and is not already processed
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deepseek_processed FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"ERROR: Article {article_id} not found in database")
        sys.exit(1)
    
    if row[0] == 1:
        print(f"ERROR: Article {article_id} is already processed")
        sys.exit(1)
    
    print(f"✓ Article exists and is ready for processing")
    
    # Try to extract/generate Chinese title
    zh_title = extract_zh_title_from_response(response_data, article_id)
    if zh_title:
        print(f"✓ Chinese title found: {zh_title[:60]}...")
    else:
        print(f"⚠ No Chinese title found in response")
    
    # Insert data
    success = insert_data_into_db(article_id, response_data)
    
    if success:
        # Try to update Chinese title
        if zh_title:
            if update_zh_title_in_db(article_id, zh_title):
                print(f"✓ Updated Chinese title for article {article_id}")
        
        print(f"\n✓ Article {article_id} fully processed and inserted!")
    else:
        print(f"\n✗ Failed to insert data for article {article_id}")
        sys.exit(1)

if __name__ == '__main__':
    main()
