#!/usr/bin/env python3
"""Process a single article with DeepSeek API for enhanced title and analysis."""

import sqlite3
import json
import pathlib
import requests
import os
import sys
from bs4 import BeautifulSoup

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY:
    raise RuntimeError('DEEPSEEK_API_KEY is not set in the environment.')

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DB_FILE = pathlib.Path("articles.db")

def get_article_content(article_id: int) -> dict:
    """Get article content from database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, source, url, description, content 
        FROM articles WHERE id = ?
    """, (article_id,))
    
    article = cursor.fetchone()
    conn.close()
    
    if not article:
        raise ValueError(f"Article {article_id} not found")
    
    # Extract clean text from HTML content
    clean_content = article['content']
    if clean_content:
        soup = BeautifulSoup(clean_content, 'html.parser')
        # Get all text, remove script/style tags
        for script in soup(['script', 'style']):
            script.decompose()
        clean_content = soup.get_text(separator='\n', strip=True)
    
    return {
        "id": article['id'],
        "title": article['title'],
        "source": article['source'],
        "url": article['url'],
        "description": article['description'],
        "content": clean_content
    }

def process_article(article_id: int):
    """Process a single article with DeepSeek."""
    
    article = get_article_content(article_id)
    print(f"\n📄 Processing Article {article_id}: {article['title']}")
    print(f"   Source: {article['source']}")
    print(f"   URL: {article['url']}")
    
    # Create prompt
    prompt = f"""You are an expert editorial analyst and educator. Process this article with comprehensive analysis.

Article Details:
- Title: {article['title']}
- Source: {article['source']}
- Description: {article['description']}

Article Content:
{article['content']}

Provide a JSON response with the following structure:

{{
    "article_id": {article['id']},
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
        ... (top 10 keywords: ONLY include words with frequency >= 3)
    ],
    "background_reading": "<200-300 word background on the topic>",
    "multiple_choice_questions": [
        {{
            "question": "<question text>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>",
            "type": "<what_questions/how_questions/why_questions>",
            "word_type": "<what/how/why>"
        }},
        ... (10 questions total: 3-4 "what", 3-4 "how", 3-4 "why")
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
        "synthesis": "<200 word synthesis>"
    }}
}}

IMPORTANT:
1. TITLE REWRITING: Rewrite to be more engaging/clear (8-12 words) and translate to Chinese
2. Summaries MUST be exactly 500-700 words
3. Chinese should be natural, not literal translation
4. Keywords must appear 3+ times in the article
5. Provide 3 difficulty-level explanations for each keyword
6. Background reading for someone with no prior knowledge
7. 10 multiple choice questions (3-4 of each type: what/how/why)
8. Two contrasting perspectives on the topic
9. Return ONLY valid JSON

Generate the analysis now. Return ONLY the JSON response."""

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
    
    print("\n📤 Sending to DeepSeek API...")
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=(30, 300))
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            
            print("✓ Received response from DeepSeek")
            
            # Parse and store in database
            try:
                feedback = json.loads(content)
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                # Update articles table with rewritten title and Chinese title
                if 'rewritten_title' in feedback and feedback['rewritten_title']:
                    cursor.execute("""
                        UPDATE articles 
                        SET title = ?, zh_title = ?
                        WHERE id = ?
                    """, (
                        feedback.get('rewritten_title', ''),
                        feedback.get('rewritten_title_zh', ''),
                        article_id
                    ))
                    print(f"✓ Updated title: {feedback.get('rewritten_title')}")
                    print(f"✓ Updated zh_title: {feedback.get('rewritten_title_zh')}")
                
                # Insert or replace feedback
                cursor.execute("""
                    INSERT OR REPLACE INTO deepseek_feedback
                    (article_id, summary_en, summary_zh, key_words, 
                     background_reading, multiple_choice_questions, 
                     discussion_both_sides)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    feedback.get('summary_en', ''),
                    feedback.get('summary_zh', ''),
                    json.dumps(feedback.get('key_words', []), ensure_ascii=False),
                    feedback.get('background_reading', ''),
                    json.dumps(feedback.get('multiple_choice_questions', []), ensure_ascii=False),
                    json.dumps(feedback.get('discussion_both_sides', {}), ensure_ascii=False)
                ))
                
                # Mark article as processed
                cursor.execute("""
                    UPDATE articles 
                    SET deepseek_processed = 1
                    WHERE id = ?
                """, (article_id,))
                
                conn.commit()
                conn.close()
                
                print(f"✓ Stored analysis for article {article_id}")
                print(f"✓ Generated {len(feedback.get('multiple_choice_questions', []))} questions")
                print(f"✓ Extracted {len(feedback.get('key_words', []))} keywords")
                
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON response: {e}")
                print(f"Response: {content[:500]}")
        else:
            print(f"✗ Unexpected response format from DeepSeek")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_single_article.py <article_id>")
        sys.exit(1)
    
    article_id = int(sys.argv[1])
    process_article(article_id)
