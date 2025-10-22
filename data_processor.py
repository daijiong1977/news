#!/usr/bin/env python3
"""
Data Processor - Deepseek API Integration
Processes collected articles through Deepseek API and populates database tables.
"""

import sqlite3
import json
import os
import pathlib
from datetime import datetime
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_FILE = pathlib.Path("articles.db")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# Load prompts
PROMPTS_FILE = pathlib.Path("prompts_compact.md")

# Create session with connection pooling
session = requests.Session()


def load_prompts():
    """Load all category prompts from prompts.md."""
    prompts = {}
    
    if not PROMPTS_FILE.exists():
        print(f"✗ Prompts file not found: {PROMPTS_FILE}")
        return prompts
    
    with open(PROMPTS_FILE, 'r') as f:
        content = f.read()
    
    # Parse prompts by category
    categories = {
        "default": "## Default Prompt",
        "sports": "## Sports Prompt",
        "tech": "## Technology Prompt",
        "science": "## Science Prompt",
        "politics": "## Political/News Prompt"
    }
    
    for key, marker in categories.items():
        start = content.find(marker)
        if start == -1:
            continue
        
        # Find the prompt code block
        code_start = content.find("```\n", start)
        code_end = content.find("```", code_start + 4)
        
        if code_start != -1 and code_end != -1:
            prompt_text = content[code_start + 4:code_end].strip()
            prompts[key] = prompt_text
    
    return prompts


def get_prompt_for_category(conn, category_id):
    """Get the appropriate prompt for a category."""
    cursor = conn.cursor()
    cursor.execute("SELECT prompt_name FROM categories WHERE category_id = ?", (category_id,))
    result = cursor.fetchone()
    
    if result:
        return result[0]  # prompt_name
    return "default"


def call_deepseek_api(prompt_with_article, retry_count=3):
    """Call Deepseek API to process article with retry logic."""
    
    if not DEEPSEEK_API_KEY:
        print("✗ DEEPSEEK_API_KEY not set")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt_with_article
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                print(f"    Retry attempt {attempt}...")
            else:
                print("    Calling Deepseek API...")
            
            # Use tuple (connect_timeout, read_timeout) - the key difference!
            response = requests.post(
                DEEPSEEK_API_URL, 
                json=payload, 
                headers=headers, 
                timeout=(30, 300)  # connect_timeout=30s, read_timeout=300s
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                print(f"    ✗ Unexpected API response format")
                return None
                
        except requests.exceptions.Timeout:
            if attempt < retry_count - 1:
                wait_time = 20 * (attempt + 1)
                print(f"    ✗ Timeout")
                print(f"    Waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
            else:
                print(f"    ✗ Timeout after {retry_count} attempts")
                return None
        except requests.RequestException as e:
            if attempt < retry_count - 1:
                wait_time = 20 * (attempt + 1)
                print(f"    ✗ API error: {str(e)[:50]}")
                print(f"    Waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
            else:
                print(f"    ✗ API error after {retry_count} attempts: {str(e)[:100]}")
                return None
    
    return None


def parse_json_response(response_text):
    """Extract JSON from Deepseek response."""
    
    # Try to find JSON block in response
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start == -1 or json_end == 0:
        print("    ✗ No JSON found in response")
        return None
    
    json_str = response_text[json_start:json_end]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parsing error: {e}")
        return None


def insert_summaries(conn, article_id, data):
    """Insert article summaries."""
    cursor = conn.cursor()
    
    summaries = [
        ("easy", "en", data.get("summary_easy", "")),
        ("mid", "en", data.get("summary_mid", "")),
        ("hard", "en", data.get("summary_hard", "")),
        ("hard", "zh", data.get("summary_zh_hard", ""))
    ]
    
    count = 0
    for difficulty, language, summary_text in summaries:
        if not summary_text:
            continue
        
        # Get difficulty_id
        cursor.execute("SELECT difficulty_id FROM difficulty_levels WHERE difficulty = ?", (difficulty,))
        diff_result = cursor.fetchone()
        if not diff_result:
            continue
        difficulty_id = diff_result[0]
        
        # Get language_id
        cursor.execute("SELECT language_id FROM languages WHERE language = ?", (language,))
        lang_result = cursor.fetchone()
        if not lang_result:
            continue
        language_id = lang_result[0]
        
        try:
            cursor.execute("""
                INSERT INTO article_summaries 
                (article_id, difficulty_id, language_id, summary, generated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (article_id, difficulty_id, language_id, summary_text, datetime.now().isoformat()))
            count += 1
        except sqlite3.Error as e:
            print(f"      ✗ Error inserting summary: {e}")
    
    conn.commit()
    return count


def insert_keywords(conn, article_id, data):
    """Insert keywords."""
    cursor = conn.cursor()
    count = 0
    
    keyword_sets = [
        (1, data.get("key_words_easy", [])),
        (2, data.get("key_words_mid", [])),
        (3, data.get("key_words_hard", []))
    ]
    
    for difficulty_id, keywords in keyword_sets:
        for keyword_data in keywords:
            word = keyword_data.get("word", "")
            if not word:
                continue
            
            frequency = keyword_data.get("frequency", 1)
            explanation = ""
            
            if difficulty_id == 1:
                explanation = keyword_data.get("easy_explanation", "")
            elif difficulty_id == 2:
                explanation = keyword_data.get("medium_explanation", "")
            else:
                explanation = keyword_data.get("hard_explanation", "")
            
            try:
                cursor.execute("""
                    INSERT INTO keywords 
                    (article_id, difficulty_id, word, frequency, explanation, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (article_id, difficulty_id, word, frequency, explanation, datetime.now().isoformat()))
                count += 1
            except sqlite3.Error as e:
                print(f"      ✗ Error inserting keyword: {e}")
    
    conn.commit()
    return count


def insert_questions_and_choices(conn, article_id, data):
    """Insert questions and their choices."""
    cursor = conn.cursor()
    q_count = 0
    c_count = 0
    
    question_sets = [
        (1, data.get("multiple_choice_questions_easy", [])),
        (2, data.get("multiple_choice_questions_mid", [])),
        (3, data.get("multiple_choice_questions_hard", []))
    ]
    
    for difficulty_id, questions in question_sets:
        for q_data in questions:
            question_text = q_data.get("question", "")
            if not question_text:
                continue
            
            try:
                cursor.execute("""
                    INSERT INTO questions 
                    (article_id, difficulty_id, question, created_at)
                    VALUES (?, ?, ?, ?)
                """, (article_id, difficulty_id, question_text, datetime.now().isoformat()))
                question_id = cursor.lastrowid
                q_count += 1
                
                # Insert choices
                options = q_data.get("options", [])
                correct_answer = q_data.get("correct_answer", "")
                explanation = q_data.get("explanation", "")
                
                for idx, option_text in enumerate(options):
                    option_letter = chr(65 + idx)  # A, B, C, D
                    is_correct = (option_letter == correct_answer)
                    
                    cursor.execute("""
                        INSERT INTO choices 
                        (question_id, choice_text, is_correct, explanation, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (question_id, option_text, is_correct, explanation if is_correct else "", datetime.now().isoformat()))
                    c_count += 1
                    
            except sqlite3.Error as e:
                print(f"      ✗ Error inserting question: {e}")
    
    conn.commit()
    return q_count, c_count


def insert_background_reading(conn, article_id, data):
    """Insert background reading."""
    cursor = conn.cursor()
    count = 0
    
    readings = [
        (1, data.get("background_reading_easy", "")),
        (2, data.get("background_reading_mid", "")),
        (3, data.get("background_reading_hard", ""))
    ]
    
    for difficulty_id, reading_text in readings:
        if not reading_text:
            continue
        
        try:
            cursor.execute("""
                INSERT INTO background_read 
                (article_id, difficulty_id, background_text, created_at)
                VALUES (?, ?, ?, ?)
            """, (article_id, difficulty_id, reading_text, datetime.now().isoformat()))
            count += 1
        except sqlite3.Error as e:
            print(f"      ✗ Error inserting background reading: {e}")
    
    conn.commit()
    return count


def insert_analysis(conn, article_id, data):
    """Insert article analysis."""
    cursor = conn.cursor()
    count = 0
    
    analyses = [
        (2, data.get("article_analysis_mid", {}).get("analysis_en", "")),
        (3, data.get("article_analysis_hard", {}).get("analysis_en", ""))
    ]
    
    for difficulty_id, analysis_text in analyses:
        if not analysis_text:
            continue
        
        try:
            cursor.execute("""
                INSERT INTO article_analysis 
                (article_id, difficulty_id, analysis_en, created_at)
                VALUES (?, ?, ?, ?)
            """, (article_id, difficulty_id, analysis_text, datetime.now().isoformat()))
            count += 1
        except sqlite3.Error as e:
            print(f"      ✗ Error inserting analysis: {e}")
    
    conn.commit()
    return count


def insert_perspectives(conn, article_id, data):
    """Insert perspectives (comments)."""
    cursor = conn.cursor()
    count = 0
    
    perspectives = [
        (1, data.get("perspectives_easy", {})),
        (2, data.get("perspectives_mid", {})),
        (3, data.get("perspectives_hard", {}))
    ]
    
    for difficulty_id, persp_data in perspectives:
        # Insert perspective_1
        p1_title = persp_data.get("perspective_1", {}).get("title", "")
        p1_arg = persp_data.get("perspective_1", {}).get("argument") or persp_data.get("perspective_1", {}).get("arguments", [])
        p1_attitude = persp_data.get("perspective_1", {}).get("attitude", "neutral")
        
        if p1_title:
            p1_content = f"{p1_title}: {p1_arg if isinstance(p1_arg, str) else ' '.join(p1_arg)}"
            try:
                cursor.execute("""
                    INSERT INTO comments 
                    (article_id, difficulty_id, attitude, com_content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, difficulty_id, p1_attitude, p1_content, datetime.now().isoformat()))
                count += 1
            except sqlite3.Error as e:
                print(f"      ✗ Error inserting perspective: {e}")
        
        # Insert perspective_2
        p2_title = persp_data.get("perspective_2", {}).get("title", "")
        p2_arg = persp_data.get("perspective_2", {}).get("argument") or persp_data.get("perspective_2", {}).get("arguments", [])
        p2_attitude = persp_data.get("perspective_2", {}).get("attitude", "neutral")
        
        if p2_title:
            p2_content = f"{p2_title}: {p2_arg if isinstance(p2_arg, str) else ' '.join(p2_arg)}"
            try:
                cursor.execute("""
                    INSERT INTO comments 
                    (article_id, difficulty_id, attitude, com_content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, difficulty_id, p2_attitude, p2_content, datetime.now().isoformat()))
                count += 1
            except sqlite3.Error as e:
                print(f"      ✗ Error inserting perspective: {e}")
        
        # Insert synthesis
        synth_text = persp_data.get("synthesis", {}).get("text", "")
        if synth_text:
            try:
                cursor.execute("""
                    INSERT INTO comments 
                    (article_id, difficulty_id, attitude, com_content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, difficulty_id, "neutral", f"Synthesis: {synth_text}", datetime.now().isoformat()))
                count += 1
            except sqlite3.Error as e:
                print(f"      ✗ Error inserting synthesis: {e}")
    
    conn.commit()
    return count


def process_article(conn, article_id, prompts):
    """Process a single article through Deepseek."""
    
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, category_id FROM articles WHERE id = ?", (article_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"✗ Article {article_id} not found")
        return False
    
    title, content, category_id = result
    
    print(f"\n  Article ID {article_id}: {title[:60]}...")
    
    # Get appropriate prompt
    prompt_name = get_prompt_for_category(conn, category_id)
    prompt_template = prompts.get(prompt_name, prompts.get("default", ""))
    
    if not prompt_template:
        print(f"    ✗ No prompt found for category: {prompt_name}")
        return False
    
    # Limit content to 1500 characters to prevent API timeout while preserving key info
    limited_content = content[:1500] if len(content) > 1500 else content
    
    # Build articles_json placeholder
    articles_json = f"""
Title: {title}
Content: {limited_content}
"""
    
    # Replace placeholders in prompt
    full_prompt = prompt_template.replace("{articles_json}", articles_json).replace("{num_articles}", "1")
    
    # Call Deepseek API
    response = call_deepseek_api(full_prompt)
    if not response:
        print("    ✗ Failed to get Deepseek response")
        return False
    
    # Parse JSON response
    data = parse_json_response(response)
    if not data:
        print("    ✗ Failed to parse Deepseek response")
        return False
    
    print("    ✓ Received and parsed response")
    
    # Insert data into all tables
    summary_rows = insert_summaries(conn, article_id, data)
    keyword_rows = insert_keywords(conn, article_id, data)
    question_rows, choice_rows = insert_questions_and_choices(conn, article_id, data)
    background_rows = insert_background_reading(conn, article_id, data)
    analysis_rows = insert_analysis(conn, article_id, data)
    perspective_rows = insert_perspectives(conn, article_id, data)
    
    print(f"    ✓ Inserted: {summary_rows} summaries, {keyword_rows} keywords, " +
          f"{question_rows} questions, {choice_rows} choices, {background_rows} background, " +
          f"{analysis_rows} analysis, {perspective_rows} perspectives")
    
    # Update article as processed and clear in_progress
    cursor.execute("UPDATE articles SET deepseek_processed = 1, processed_at = ?, deepseek_in_progress = 0 WHERE id = ?",
                   (datetime.now().isoformat(), article_id))
    conn.commit()
    
    return True


def main():
    """Main function."""
    
    if not DEEPSEEK_API_KEY:
        print("✗ DEEPSEEK_API_KEY environment variable not set")
        print("   Run: export DEEPSEEK_API_KEY='your-key'")
        return
    
    if not DB_FILE.exists():
        print(f"✗ Database not found: {DB_FILE}")
        return
    
    # Load prompts
    prompts = load_prompts()
    if not prompts:
        print("✗ Failed to load prompts")
        return
    
    print("\n" + "="*70)
    print("DATA PROCESSOR - Deepseek Integration")
    print("="*70)
    print(f"API Key: {DEEPSEEK_API_KEY[:10]}...")
    print(f"Prompts loaded: {len(prompts)} categories")
    
    conn = sqlite3.connect(DB_FILE)
    
    # Find unprocessed articles
    cursor = conn.cursor()
    # Select unprocessed articles but exclude those that have failed >=3 or are in progress
    cursor.execute("SELECT id FROM articles WHERE deepseek_processed = 0 AND deepseek_failed < 3 AND (deepseek_in_progress = 0 OR deepseek_in_progress IS NULL) ORDER BY id")
    unprocessed_ids = [row[0] for row in cursor.fetchall()]
    
    print(f"\nUnprocessed articles: {len(unprocessed_ids)}")
    for aid in unprocessed_ids:
        print(f"  - ID {aid}")
    
    # Process articles
    success_count = 0
    for article_id in unprocessed_ids:
        # Try to claim the article atomically
        try:
            cur = conn.cursor()
            cur.execute("UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND deepseek_processed = 0 AND deepseek_failed < 3 AND (deepseek_in_progress = 0 OR deepseek_in_progress IS NULL)", (article_id,))
            if cur.rowcount != 1:
                # someone else claimed it
                continue
            conn.commit()

            ok = process_article(conn, article_id, prompts)
            if ok:
                success_count += 1
                # mark processed and clear in_progress
                try:
                    cur.execute("UPDATE articles SET deepseek_processed = 1, processed_at = ?, deepseek_in_progress = 0 WHERE id = ?", (datetime.now().isoformat(), article_id))
                    conn.commit()
                except Exception:
                    conn.rollback()
            else:
                # increment failed and possibly delete
                try:
                    cur.execute("UPDATE articles SET deepseek_failed = deepseek_failed + 1, deepseek_last_error = ? WHERE id = ?", ("processing_failed", article_id))
                    conn.commit()
                    cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                    val = cur.fetchone()
                    failed_count = val[0] if val else 0
                    if failed_count and failed_count > 3:
                        cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                        conn.commit()
                except Exception:
                    conn.rollback()
            # ensure in_progress cleared if still present
            try:
                cur.execute("UPDATE articles SET deepseek_in_progress = 0 WHERE id = ?", (article_id,))
                conn.commit()
            except Exception:
                conn.rollback()
        except Exception:
            conn.rollback()
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"✓ Processing complete: {success_count}/{len(unprocessed_ids)} articles processed")
    print("="*70)


if __name__ == "__main__":
    main()
