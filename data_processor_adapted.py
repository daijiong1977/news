#!/usr/bin/env python3
"""
Data Processor - Adapted from working deepseek_processor.py
Uses batch processing approach that worked perfectly with 20 articles
"""

import sqlite3
import json
import pathlib
import requests
from typing import Optional
import time
import os
import argparse
from datetime import datetime

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY:
    raise RuntimeError('DEEPSEEK_API_KEY is not set in the environment.')

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DB_FILE = pathlib.Path("articles.db")


def get_unprocessed_articles(limit: int = 5) -> list[dict]:
    """Get unprocessed articles from NEW schema (pub_date instead of date_iso)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Updated query for new schema
    # Select candidate ids with precondition and attempt to claim them atomically
    cursor.execute("""
        SELECT id FROM articles 
        WHERE deepseek_processed = 0 AND deepseek_failed < 3 AND (deepseek_in_progress = 0 OR deepseek_in_progress IS NULL)
        ORDER BY pub_date DESC
        LIMIT ?
    """, (limit,))

    candidate_ids = [row['id'] for row in cursor.fetchall()]

    articles = []
    for aid in candidate_ids:
        try:
            # Try to claim the article for processing
            c = conn.cursor()
            c.execute("UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND deepseek_processed = 0 AND deepseek_failed < 3 AND (deepseek_in_progress = 0 OR deepseek_in_progress IS NULL)", (aid,))
            if c.rowcount != 1:
                continue
            conn.commit()
            article = get_article_content(aid)
            if article:
                articles.append(article)
        except Exception:
            conn.rollback()

    conn.close()
    return articles


def get_article_content(article_id: int) -> Optional[dict]:
    """Get article content from NEW schema."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    conn.close()
    
    if not article:
        return None
    
    return {
        "id": article['id'],
        "title": article['title'],
        "source": article['source'],
        "link": article['url'],
        "content": article['content'],
        "date": article['pub_date']
    }


def create_deepseek_prompt(articles: list[dict]) -> str:
    """Create detailed prompt for multiple articles (batch mode)."""
    
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    
    prompt = f"""You are an expert editorial analyst and educator. Process the following {len(articles)} articles with comprehensive analysis.

For EACH article, provide a JSON response with the following structure:

{{
    "article_id": <id>,
    "summary_en": "<500-700 word summary in English>",
    "summary_zh": "<Chinese translation of the English summary, 500-700 words>",
    "key_words": [
        {{
            "word": "<keyword>",
            "frequency": <count>,
            "explanation": "<50-100 word explanation of this key term in context>",
            "easy_explanation": "<simple 30-50 word explanation suitable for beginners>",
            "medium_explanation": "<intermediate 50-80 word explanation with moderate detail>",
            "hard_explanation": "<advanced 80-120 word explanation with technical depth and nuances>"
        }},
        ... (top 10 keywords: ONLY include words with frequency >= 3. Skip any words that appear only 1-2 times. Include important technical terms, named entities, and significant concepts.)
    ],
    "background_reading": "<200-300 word background on the topic, explaining historical context or domain knowledge needed to understand the article>",
    "multiple_choice_questions": [
        {{
            "question": "<question text>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>",
            "type": "<what_questions/how_questions/why_questions>",
            "word_type": "<what/how/why>"
        }},
        ... (10 questions total: 3-4 "what" questions, 3-4 "how" questions, 3-4 "why" questions)
    ],
    "discussion_both_sides": {{
        "perspective_1": {{
            "title": "<perspective name>",
            "arguments": ["<1-2 arguments supporting this view>"]
        }},
        "perspective_2": {{
            "title": "<alternative perspective>",
            "arguments": ["<1-2 arguments supporting this view>"]
        }},
        "synthesis": "<200 word synthesis discussing the tension between perspectives>"
    }}
}}

IMPORTANT INSTRUCTIONS:
1. Ensure summaries are EXACTLY 500-700 words (not less, not more)
2. Chinese translation should be natural and idiomatic, not literal
3. **CRITICAL FOR KEYWORDS: ONLY include words that appear 3 or more times in the article. Completely skip/exclude any words with frequency 1 or 2. If a word appears only once or twice, do NOT include it in the list.**
4. Keywords should be genuinely important/frequent (technical terms, named entities, significant concepts that are repeated)
5. FOR EACH KEYWORD, provide THREE separate explanations tailored to different learning levels:
   - easy_explanation: Simple language for beginners, avoid jargon, 30-50 words
   - medium_explanation: Intermediate level with some technical terms, 50-80 words
   - hard_explanation: Advanced technical explanation with nuances and depth, 80-120 words
6. Background reading should help someone with no prior knowledge understand the topic
7. Generate 10 multiple choice questions per article (NOT 5):
   - 3-4 "what" questions (word_type: "what") - questions about facts and definitions
   - 3-4 "how" questions (word_type: "how") - questions about processes and mechanisms
   - 3-4 "why" questions (word_type: "why") - questions about reasons and implications
8. Each question should be academic level with 4 clear options
9. Only ONE correct answer per question
10. Perspectives should represent genuinely different viewpoints on the topic/technology/issue
11. Return ONLY valid JSON, one object per article
12. If articles are in array, return array of JSON objects, one per article

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive analysis for all {len(articles)} articles. Return ONLY the JSON response."""
    
    return prompt


def send_to_deepseek(prompt: str, batch_num: int) -> Optional[str]:
    """Send prompt to DeepSeek API with working timeout format."""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 6000
    }
    
    print(f"\n📤 Sending batch {batch_num} to DeepSeek API...")
    print(f"   Timeout: (30s connect, 300s read)...")
    
    try:
        # CRITICAL: Use tuple (connect_timeout, read_timeout) - this was the key fix!
        response = requests.post(
            DEEPSEEK_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=(30, 300)  # 30s connect, 300s read
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            
            print(f"✓ Received response from DeepSeek (batch {batch_num})")
            return content
        else:
            print(f"✗ Unexpected response format")
            return None
            
    except requests.exceptions.Timeout as e:
        print(f"✗ Timeout: {e}")
        return None
    except requests.RequestException as e:
        print(f"✗ API Error: {e}")
        return None


def insert_into_new_schema(article_id: int, data: dict):
    """Insert parsed data into NEW schema tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Insert summaries
        summaries = data.get("summaries", {})
        for lang in ["en", "zh"]:
            for level in ["easy", "mid", "hard"]:
                key = f"summary_{level}"
                if key in summaries:
                    cursor.execute("""
                        INSERT OR REPLACE INTO article_summaries
                        (article_id, difficulty_id, language_id, summary)
                        VALUES (?, ?, ?, ?)
                    """, (
                        article_id,
                        {"easy": 1, "mid": 2, "hard": 3}[level],
                        {"en": 1, "zh": 2}[lang],
                        summaries[key]
                    ))
        
        # Insert keywords
        for difficulty_id, level in [(1, "easy"), (2, "mid"), (3, "hard")]:
            keywords = data.get(f"keywords_{level}", [])
            for kw in keywords:
                cursor.execute("""
                    INSERT INTO keywords
                    (article_id, difficulty_id, word, frequency, explanation, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    difficulty_id,
                    kw.get("word", ""),
                    kw.get("frequency", 1),
                    kw.get("explanation", ""),
                    datetime.now().isoformat()
                ))
        
        # Insert questions and choices
        for difficulty_id, level in [(1, "easy"), (2, "mid"), (3, "hard")]:
            questions = data.get(f"questions_{level}", [])
            for q in questions:
                cursor.execute("""
                    INSERT INTO questions
                    (article_id, difficulty_id, question, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    article_id,
                    difficulty_id,
                    q.get("question", ""),
                    datetime.now().isoformat()
                ))
                q_id = cursor.lastrowid
                
                for idx, option in enumerate(q.get("options", [])):
                    is_correct = chr(65 + idx) == q.get("correct_answer", "")
                    cursor.execute("""
                        INSERT INTO choices
                        (question_id, choice_text, is_correct, explanation, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        q_id,
                        option,
                        is_correct,
                        q.get("explanation", "") if is_correct else "",
                        datetime.now().isoformat()
                    ))
        
        # Insert background reading
        for difficulty_id, level in [(1, "easy"), (2, "mid"), (3, "hard")]:
            bg = data.get(f"background_{level}", "")
            if bg:
                cursor.execute("""
                    INSERT INTO background_read
                    (article_id, difficulty_id, background_text, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    article_id,
                    difficulty_id,
                    bg,
                    datetime.now().isoformat()
                ))
        
        # Insert analysis (mid/hard only)
        for difficulty_id, level in [(2, "mid"), (3, "hard")]:
            analysis = data.get(f"analysis_{level}", "")
            if analysis:
                cursor.execute("""
                    INSERT INTO article_analysis
                    (article_id, difficulty_id, analysis_en, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    article_id,
                    difficulty_id,
                    analysis,
                    datetime.now().isoformat()
                ))
        
        # Insert perspectives (comments)
        for difficulty_id, level in [(1, "easy"), (2, "mid"), (3, "hard")]:
            persp = data.get(f"perspectives_{level}", {})
            for p_key in ["perspective_1", "perspective_2"]:
                if p_key in persp:
                    p_data = persp[p_key]
                    cursor.execute("""
                        INSERT INTO comments
                        (article_id, difficulty_id, attitude, com_content, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        article_id,
                        difficulty_id,
                        p_data.get("attitude", "neutral"),
                        f"{p_data.get('title', '')}: {p_data.get('argument', '')}",
                        datetime.now().isoformat()
                    ))
            
            # Synthesis
            if "synthesis" in persp:
                cursor.execute("""
                    INSERT INTO comments
                    (article_id, difficulty_id, attitude, com_content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    difficulty_id,
                    "neutral",
                    f"Synthesis: {persp['synthesis'].get('text', '')}",
                    datetime.now().isoformat()
                ))
        
        # Mark as processed and clear in_progress
        cursor.execute("""
            UPDATE articles SET deepseek_processed = 1, processed_at = ?, deepseek_in_progress = 0 WHERE id = ?
        """, (datetime.now().isoformat(), article_id))
        
        conn.commit()
        print(f"  ✓ Stored data for article {article_id}")
        
    except Exception as e:
        print(f"  ✗ Error storing data for article {article_id}: {e}")
        conn.rollback()
        try:
            cursor.execute("UPDATE articles SET deepseek_failed = deepseek_failed + 1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?", (str(e), article_id))
            conn.commit()
            cursor.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
            val = cursor.fetchone()
            failed_count = val[0] if val else 0
            if failed_count and failed_count > 3:
                cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                conn.commit()
        except Exception:
            conn.rollback()
    finally:
        conn.close()


def process_articles_in_batches(batch_size: int = 5, max_batches: Optional[int] = None):
    """Process unprocessed articles in batches (the working approach!)."""

    batch_num = 1
    while True:
        if max_batches and batch_num > max_batches:
            break

        # Get next batch
        articles = get_unprocessed_articles(limit=batch_size)

        if not articles:
            print("\n✓ All articles have been processed!")
            break

        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}: Processing {len(articles)} articles")
        print(f"{'='*70}")

        for article in articles:
            print(f"  - Article {article['id']}: {article['title'][:50]}")

        # Create and send prompt
        prompt = create_deepseek_prompt(articles)
        response_text = send_to_deepseek(prompt, batch_num=batch_num)

        if response_text:
            # Save response for inspection
            response_file = f"deepseek_batch_{batch_num}.json"
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"✓ Response saved to {response_file}")

            # Parse response
            try:
                data = json.loads(response_text)
                if isinstance(data, list):
                    feedbacks = data
                else:
                    feedbacks = [data]

                # Store each article's data
                for fb in feedbacks:
                    if 'id' in fb:
                        insert_into_new_schema(fb['id'], fb)
                    elif 'article_id' in fb:
                        insert_into_new_schema(fb['article_id'], fb)

                print(f"✓ Batch {batch_num} complete")

            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse response: {e}")

        batch_num += 1


def main():
    parser = argparse.ArgumentParser(description='Process articles with DeepSeek')
    parser.add_argument('--batch-size', type=int, default=5, help='Articles per batch')
    parser.add_argument('--max-batches', type=int, default=None, help='Max batches to process')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("DATA PROCESSOR - Batch Mode (Working Approach)")
    print("="*70)
    print(f"API Key: {DEEPSEEK_API_KEY[:10]}...")
    print(f"Batch size: {args.batch_size}")
    print()
    
    process_articles_in_batches(batch_size=args.batch_size, max_batches=args.max_batches)


if __name__ == "__main__":
    main()
