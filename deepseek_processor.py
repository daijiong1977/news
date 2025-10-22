#!/usr/bin/env python3
"""Process articles with DeepSeek API for enhanced analysis."""

import sqlite3
import json
import pathlib
import requests
from typing import Optional
import time

import os

# DeepSeek API key is read from environment for security. Set DEEPSEEK_API_KEY in your shell.
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY:
    # Fail early with clear instruction when running interactively
    raise RuntimeError('DEEPSEEK_API_KEY is not set in the environment. Please export it before running this script.')
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DB_FILE = pathlib.Path("articles.db")
CONTENT_DIR = pathlib.Path("content")


def init_deepseek_tables():
    """Initialize database tables for DeepSeek feedback."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Add column to track DeepSeek processing status
    try:
        cursor.execute("""
            ALTER TABLE articles 
            ADD COLUMN deepseek_processed INTEGER DEFAULT 0
        """)
        print("✓ Added deepseek_processed column to articles table")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # deepseek_feedback table deprecated — runtime storage uses normalized tables
    
    # Create dedicated quiz questions table for game development
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question_type TEXT,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            UNIQUE(article_id, question_number)
        )
    """)
    
    # Create indexes for game queries
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quiz_article 
            ON quiz_questions(article_id)
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quiz_type 
            ON quiz_questions(question_type)
        """)
    except:
        pass
    
    conn.commit()
    conn.close()
    print("✓ DeepSeek tables initialized")
    print("✓ Quiz questions table created (perfect for game development)")


def store_quiz_questions(article_id: int, questions_data: list[dict]):
    """Store quiz questions in separate table for easy game development."""
    if not questions_data:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Best-effort: write into normalized questions/choices tables.
        # Ensure question_number column exists in questions (migration script will add it if needed).
        cursor.execute("PRAGMA table_info(questions)")
        qcols = [r[1] for r in cursor.fetchall()]

        # Delete existing normalized questions for this article (we'll re-insert fresh)
        try:
            cursor.execute("DELETE FROM choices WHERE question_id IN (SELECT question_id FROM questions WHERE article_id = ?)", (article_id,))
            cursor.execute("DELETE FROM questions WHERE article_id = ?", (article_id,))
        except Exception:
            pass

        for idx, q in enumerate(questions_data, 1):
            qtext = q.get('question', '')
            opts = q.get('options', ['', '', '', ''])
            correct = q.get('correct_answer', '')
            explanation = q.get('explanation', None)
            created_at = None

            # Insert into questions. Include question_number if column exists.
            if 'question_number' in qcols:
                cursor.execute('INSERT INTO questions (article_id, difficulty_id, question_text, created_at, question_number) VALUES (?, NULL, ?, ?, ?)', (article_id, qtext, created_at, idx))
            else:
                cursor.execute('INSERT INTO questions (article_id, difficulty_id, question_text, created_at) VALUES (?, NULL, ?, ?)', (article_id, qtext, created_at))

            question_id = cursor.lastrowid

            # Insert choices
            letters = ['A', 'B', 'C', 'D']
            for opt_text, letter in zip(opts, letters):
                if not opt_text:
                    continue
                is_correct = 1 if (correct and str(correct).strip().upper().startswith(letter)) else 0
                cur_expl = explanation if is_correct else None
                cursor.execute('INSERT INTO choices (question_id, choice_text, is_correct, explanation, created_at) VALUES (?, ?, ?, ?, ?)', (question_id, opt_text, is_correct, cur_expl, created_at))

        conn.commit()

    except Exception as e:
        # If normalized insert fails, log and re-raise — we no longer write to legacy quiz_questions
        print(f"ERROR storing quiz questions for article {article_id}: {e}")
        conn.rollback()
        raise

    conn.commit()

def get_unprocessed_articles(limit: int = 5) -> list[dict]:
    """Get articles that haven't been processed by DeepSeek yet."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM articles_enhanced 
        WHERE deepseek_processed = 0
        ORDER BY date_iso DESC
        LIMIT ?
    """, (limit,))
    
    article_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    articles = []
    for article_id in article_ids:
        article = get_article_content(article_id)
        if article:
            articles.append(article)
    
    return articles


def create_deepseek_prompt(articles: list[dict]) -> str:
    """Create a comprehensive prompt for DeepSeek to process articles."""
    
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    
    prompt = f"""You are an expert editorial analyst and educator. Process the following {len(articles)} articles with comprehensive analysis.

For EACH article, provide a JSON response with the following structure:

{{
    "article_id": <id>,
    "rewritten_title": "<rewrite the title to be more engaging and clear, 8-12 words>",
    "rewritten_title_zh": "<Chinese translation of the rewritten title>",
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
1. **TITLE REWRITING (NEW)**: 
   - Rewrite the title to be more engaging, clear, and informative (8-12 words)
   - The rewritten title should capture the essence of the article better than the original
   - Translate the rewritten title to Chinese naturally
2. Ensure summaries are EXACTLY 500-700 words (not less, not more)
3. Chinese translation should be natural and idiomatic, not literal
4. **CRITICAL FOR KEYWORDS: ONLY include words that appear 3 or more times in the article. Completely skip/exclude any words with frequency 1 or 2. If a word appears only once or twice, do NOT include it in the list.**
5. Keywords should be genuinely important/frequent (technical terms, named entities, significant concepts that are repeated)
6. FOR EACH KEYWORD, provide THREE separate explanations tailored to different learning levels:
   - easy_explanation: Simple language for beginners, avoid jargon, 30-50 words
   - medium_explanation: Intermediate level with some technical terms, 50-80 words
   - hard_explanation: Advanced technical explanation with nuances and depth, 80-120 words
7. Background reading should help someone with no prior knowledge understand the topic
8. Generate 10 multiple choice questions per article (NOT 5):
   - 3-4 "what" questions (word_type: "what") - questions about facts and definitions
   - 3-4 "how" questions (word_type: "how") - questions about processes and mechanisms
   - 3-4 "why" questions (word_type: "why") - questions about reasons and implications
9. Each question should be academic level with 4 clear options
10. Only ONE correct answer per question
11. Perspectives should represent genuinely different viewpoints on the topic/technology/issue
12. Return ONLY valid JSON, one object per article
13. If articles are in array, return array of JSON objects, one per article

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive analysis for all {len(articles)} articles. Return ONLY the JSON response."""
    
    return prompt


def send_to_deepseek(prompt: str, batch_num: int = 1) -> Optional[str]:
    """Send prompt to DeepSeek API and get response."""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert editorial analyst, educator, and content processor. Return responses only in valid JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 6000
    }
    
    print(f"\n📤 Sending batch {batch_num} to DeepSeek API...")
    print(f"   Payload size: {len(json.dumps(payload)) / 1024:.1f} KB")
    print(f"   Max tokens: 6000 (reduced from 8000 for faster response)...")
    print(f"   Timeout: 300 seconds (for complex analysis)...")
    
    try:
        # Use tuple (connect_timeout, read_timeout)
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=(30, 300))
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Strip markdown code fences if present
            if content.startswith("```"):
                # Remove leading ```json or ``` or similar
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            
            print(f"✓ Received response from DeepSeek (batch {batch_num})")
            return content
        else:
            print(f"✗ Unexpected response format from DeepSeek")
            print(f"  Response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")
        return None


def process_articles_in_batches(batch_size: int = 5, max_batches: Optional[int] = None):
    """Process unprocessed articles in batches."""
    
    init_deepseek_tables()
    
    batch_num = 1
    while True:
        if max_batches and batch_num > max_batches:
            break
            
        # Get next batch of articles
        articles = get_unprocessed_articles(limit=batch_size)
        
        if not articles:
            print("\n✓ All articles have been processed!")
            break
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}: Processing {len(articles)} articles")
        print(f"{'='*70}")
        
        for article in articles:
            print(f"  - Article {article['id']}: {article['title'][:50]}")
        
        # Create prompt
        prompt = create_deepseek_prompt(articles)
        
        # Send to DeepSeek
        response_text = send_to_deepseek(prompt, batch_num=batch_num)
        
        if response_text:
            # Save response to file for inspection
            response_file = f"deepseek_batch_{batch_num}.json"
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"✓ Response saved to {response_file}")
            
            # Parse and store in database
            try:
                # Try to parse as single JSON object
                try:
                    feedback = json.loads(response_text)
                    if isinstance(feedback, list):
                        feedbacks = feedback
                    else:
                        feedbacks = [feedback]
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_matches = re.findall(r'\{[^{}]*\}', response_text, re.DOTALL)
                    if json_matches:
                        feedbacks = [json.loads(match) for match in json_matches]
                    else:
                        print(f"✗ Could not parse response as JSON")
                        feedbacks = []
                
                # Insert processed data into normalized tables using the verified inserter
                try:
                    from insert_from_response import insert_data_into_db
                except Exception as e:
                    insert_data_into_db = None
                    print(f"  ⚠ Could not import insert_from_response inserter: {e}")

                stored_count = 0
                for fb in feedbacks:
                    if 'article_id' not in fb:
                        continue
                    article_id = fb.get('article_id')

                    # Update rewritten titles in articles table if present
                    try:
                        if fb.get('rewritten_title'):
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE articles 
                                SET title = ?, zh_title = ?
                                WHERE id = ?
                            """, (
                                fb.get('rewritten_title', ''),
                                fb.get('rewritten_title_zh', ''),
                                article_id
                            ))
                            conn.commit()
                            conn.close()
                            print(f"  ✓ Updated title for article {article_id}")
                    except Exception as e:
                        print(f"  ✗ Failed to update title for article {article_id}: {e}")

                    # Use the dedicated inserter to populate summaries, keywords, questions, etc.
                    if insert_data_into_db:
                        try:
                            ok = insert_data_into_db(article_id, fb)
                            if ok:
                                stored_count += 1
                                print(f"  ✓ Inserted processed data for article {article_id}")
                            else:
                                print(f"  ✗ Inserter returned False for article {article_id}")
                                # treat as failure: increment failed counter
                                conn = sqlite3.connect(DB_FILE)
                                cur = conn.cursor()
                                cur.execute("UPDATE articles SET deepseek_failed = deepseek_failed + 1 WHERE id = ?", (article_id,))
                                conn.commit()
                                # check threshold and delete if exceeded
                                cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                                val = cur.fetchone()
                                try:
                                    failed_count = val[0] if val else 0
                                except Exception:
                                    failed_count = 0
                                if failed_count and failed_count > 3:
                                    print(f"  ⚠ deepseek_failed > 3 for article {article_id}; deleting article")
                                    cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                                    conn.commit()
                                conn.close()
                        except Exception as e:
                            print(f"  ✗ Error inserting processed data for article {article_id}: {e}")
                            # increment failed counter
                            try:
                                conn = sqlite3.connect(DB_FILE)
                                cur = conn.cursor()
                                cur.execute("UPDATE articles SET deepseek_failed = deepseek_failed + 1, deepseek_last_error = ? WHERE id = ?", (str(e)[:1000], article_id))
                                conn.commit()
                                cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                                val = cur.fetchone()
                                failed_count = val[0] if val else 0
                                if failed_count and failed_count > 3:
                                    print(f"  ⚠ deepseek_failed > 3 for article {article_id}; deleting article")
                                    cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                                    conn.commit()
                                conn.close()
                            except Exception:
                                pass
                    else:
                        print(f"  ✗ No inserter available; skipping insert for article {article_id}")

                    # Store quiz questions separately (for game development)
                    if fb.get('multiple_choice_questions'):
                        store_quiz_questions(article_id, fb.get('multiple_choice_questions'))

                print(f"✓ Processed and inserted data for {stored_count}/{len(articles)} articles")
                
            except Exception as e:
                print(f"✗ Error processing response: {e}")
        else:
            print(f"✗ Failed to get response from DeepSeek, skipping batch {batch_num}")
        
        # Rate limiting
        print(f"⏳ Waiting 3 seconds before next batch...")
        time.sleep(3)
        batch_num += 1


def query_feedback(article_id: int) -> Optional[dict]:
    """Query DeepSeek feedback for a specific article.

    Deprecated: use normalized tables (article_summaries, keywords, questions, background_read, comments) instead.
    """
    return None


def get_quiz_questions(article_id: int) -> list[dict]:
    """Get all quiz questions for an article (for game development)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Try normalized tables first
    try:
        cursor.execute('SELECT question_id, question_text, question_number FROM questions WHERE article_id = ? ORDER BY question_number NULLS LAST, question_id', (article_id,))
        qrows = cursor.fetchall()
        if qrows:
            out = []
            for qr in qrows:
                qid = qr['question_id'] if 'question_id' in qr.keys() else qr[0]
                qnum = qr['question_number'] if 'question_number' in qr.keys() else (qr['question_number'] if 'question_number' in qr.keys() else None)
                qtext = qr['question_text'] if 'question_text' in qr.keys() else qr[1]

                cursor.execute('SELECT choice_text, is_correct, explanation FROM choices WHERE question_id = ? ORDER BY choice_id', (qid,))
                opts = cursor.fetchall()
                options = [o['choice_text'] if 'choice_text' in o.keys() else o[0] for o in opts]
                correct = None
                expl = None
                for o in opts:
                    is_corr = o['is_correct'] if 'is_correct' in o.keys() else o[1]
                    if is_corr:
                        correct = o['choice_text'] if 'choice_text' in o.keys() else o[0]
                        expl = o['explanation'] if 'explanation' in o.keys() else o[2]

                # Convert correct choice text to letter if possible
                correct_letter = None
                if correct and options:
                    try:
                        idx = options.index(correct)
                        correct_letter = ['A', 'B', 'C', 'D'][idx]
                    except Exception:
                        correct_letter = str(correct).strip()

                out.append({
                    'id': qid,
                    'question_number': qnum,
                    'type': None,
                    'question': qtext,
                    'options': options,
                    'correct_answer': correct_letter,
                    'explanation': expl
                })

            conn.close()
            return out

    except Exception:
        # if normalized read fails, fall back to legacy table
        pass

    # Fallback to legacy quiz_questions table
    try:
        cursor.execute("""
            SELECT id, question_number, question_type, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation
            FROM quiz_questions
            WHERE article_id = ?
            ORDER BY question_number
        """, (article_id,))
        rows = cursor.fetchall()
        questions = []
        for row in rows:
            questions.append({
                "id": row['id'],
                "question_number": row['question_number'],
                "type": row['question_type'],
                "question": row['question_text'],
                "options": [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
                "correct_answer": row['correct_answer'],
                "explanation": row['explanation']
            })
        return questions
    finally:
        conn.close()


def get_quiz_question_by_id(question_id: int) -> Optional[dict]:
    """Get a single quiz question by ID (useful for rendering in games)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, article_id, question_number, question_type, question_text,
               option_a, option_b, option_c, option_d,
               correct_answer, explanation
        FROM quiz_questions
        WHERE id = ?
    """, (question_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row['id'],
        "article_id": row['article_id'],
        "question_number": row['question_number'],
        "type": row['question_type'],
        "question": row['question_text'],
        "options": [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
        "correct_answer": row['correct_answer'],
        "explanation": row['explanation']
    }


def get_all_quiz_questions() -> list[dict]:
    """Get all quiz questions from all articles (for building game question bank)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, article_id, question_number, question_type, question_text,
               option_a, option_b, option_c, option_d,
               correct_answer, explanation
        FROM quiz_questions
        ORDER BY article_id, question_number
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        questions.append({
            "id": row['id'],
            "article_id": row['article_id'],
            "question_number": row['question_number'],
            "type": row['question_type'],
            "question": row['question_text'],
            "options": [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
            "correct_answer": row['correct_answer'],
            "explanation": row['explanation']
        })
    
    return questions


def get_quiz_by_type(question_type: str) -> list[dict]:
    """Get all quiz questions of a specific type (main_idea, new_word, sat_style)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, article_id, question_number, question_type, question_text,
               option_a, option_b, option_c, option_d,
               correct_answer, explanation
        FROM quiz_questions
        WHERE question_type = ?
        ORDER BY article_id, question_number
    """, (question_type,))
    
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        questions.append({
            "id": row['id'],
            "article_id": row['article_id'],
            "question_number": row['question_number'],
            "type": row['question_type'],
            "question": row['question_text'],
            "options": [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
            "correct_answer": row['correct_answer'],
            "explanation": row['explanation']
        })
    
    return questions


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process articles with DeepSeek API")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of articles per batch")
    parser.add_argument("--max-batches", type=int, help="Maximum number of batches to process")
    parser.add_argument("--query", type=int, help="Query feedback for a specific article ID")
    parser.add_argument("--quiz", type=int, help="Get quiz questions for article ID (for game development)")
    parser.add_argument("--quiz-id", type=int, help="Get a single quiz question by question ID")
    parser.add_argument("--all-quiz", action="store_true", help="Get all quiz questions from all articles")
    parser.add_argument("--quiz-type", type=str, help="Get quiz questions of specific type (main_idea/new_word/sat_style)")
    parser.add_argument("--init", action="store_true", help="Initialize tables only")
    
    args = parser.parse_args()
    
    if args.query:
        feedback = query_feedback(args.query)
        if feedback:
            print(json.dumps(feedback, ensure_ascii=False, indent=2))
        else:
            print(f"No feedback found for article {args.query}")
    elif args.quiz:
        questions = get_quiz_questions(args.quiz)
        if questions:
            print(json.dumps(questions, ensure_ascii=False, indent=2))
        else:
            print(f"No quiz questions found for article {args.quiz}")
    elif args.quiz_id:
        question = get_quiz_question_by_id(args.quiz_id)
        if question:
            print(json.dumps(question, ensure_ascii=False, indent=2))
        else:
            print(f"No quiz question found with ID {args.quiz_id}")
    elif args.all_quiz:
        questions = get_all_quiz_questions()
        print(json.dumps(questions, ensure_ascii=False, indent=2))
    elif args.quiz_type:
        questions = get_quiz_by_type(args.quiz_type)
        if questions:
            print(json.dumps(questions, ensure_ascii=False, indent=2))
        else:
            print(f"No quiz questions found of type '{args.quiz_type}'")
    elif args.init:
        init_deepseek_tables()
    else:
        process_articles_in_batches(batch_size=args.batch_size, max_batches=args.max_batches)
