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
    
    # Create prompt using new structure
    prompt = f"""You are an expert educational content creator specializing in making complex articles accessible at multiple reading levels.

Article Details:
- Title: {article['title']}
- Source: {article['source']}
- URL: {article['url']}
- Description: {article['description']}

Article Content:
{article['content']}

Analyze this article and create comprehensive educational content at four different levels: Easy, Mid, Hard, and Chinese (CN).

⚠️ CRITICAL LANGUAGE REQUIREMENT:
- Easy level: ENGLISH ONLY
- Mid level: ENGLISH ONLY
- Hard level: ENGLISH ONLY
- CN level: CHINESE ONLY (this is the ONLY place Chinese appears)
- NO Chinese text should appear in easy, mid, or hard levels
- NO English text should appear in CN level

Return ONLY a valid JSON response (no additional text) with this exact structure:

{{
  "article_analysis": {{
    "levels": {{
      "easy": {{
        "title": "<Simple, engaging title for beginners - 5-10 words - ENGLISH ONLY>",
        "summary": "<Beginner-friendly explanation using simple vocabulary and short sentences. ENGLISH ONLY. 200-300 words. Use analogies and everyday examples. Avoid jargon. NO CHINESE TEXT.>",
        "keywords": [
          {{"term": "<keyword>", "explanation": "<2-3 sentence simple explanation suitable for a child - ENGLISH ONLY - NO CHINESE>"}},
          (10 keywords total)
        ],
        "questions": [
          {{"question": "<Simple question>", "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"], "correct_answer": "<match one option exactly>"}},
          (5 questions total)
        ],
        "background_reading": "<2-3 paragraphs in simple terms. Include 'why this matters' section.>",
        "perspectives": [
          {{"perspective": "<Positive viewpoint - 1-2 sentences>", "attitude": "positive"}},
          {{"perspective": "<Negative viewpoint - 1-2 sentences>", "attitude": "negative"}},
          {{"perspective": "<Neutral viewpoint - 1-2 sentences>", "attitude": "neutral"}}
        ]
      }},
      "mid": {{
        "title": "<Intermediate title - 6-12 words, more specific - ENGLISH ONLY>",
        "summary": "<Intermediate explanation for high school/adults. ENGLISH ONLY. Include more technical details, cause-and-effect. Use standard vocabulary. 300-400 words. NO CHINESE TEXT.>",
        "keywords": [
          {{"term": "<keyword>", "explanation": "<3-4 sentence explanation with some technical terms and context - ENGLISH ONLY - NO CHINESE>"}},
          (10 keywords total)
        ],
        "questions": [
          {{"question": "<Question requiring understanding of concepts and relationships>", "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"], "correct_answer": "<match one option exactly>"}},
          (8-10 questions total)
        ],
        "background_reading": "<3-4 paragraphs of intermediate context. Include historical background, relevant research, and broader implications.>",
        "perspectives": [
          {{"perspective": "<Positive viewpoint with supporting arguments - 2-3 sentences>", "attitude": "positive"}},
          {{"perspective": "<Negative viewpoint with supporting arguments - 2-3 sentences>", "attitude": "negative"}},
          {{"perspective": "<Balanced viewpoint acknowledging complexity - 2-3 sentences>", "attitude": "neutral"}}
        ]
      }},
      "hard": {{
        "title": "<Advanced title - highly specific and precise, 7-15 words - ENGLISH ONLY>",
        "summary": "<Expert-level explanation for professionals. ENGLISH ONLY. Use technical terminology appropriately. Include methodology, nuances, limitations, implications. 400-500 words. NO CHINESE TEXT.>",
        "keywords": [
          {{"term": "<technical keyword>", "explanation": "<5-6 sentence detailed explanation with technical terminology, context, and relevance - ENGLISH ONLY - NO CHINESE>"}},
          (10 keywords total)
        ],
        "questions": [
          {{"question": "<Advanced question requiring critical thinking and synthesis>", "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"], "correct_answer": "<match one option exactly>"}},
          (10-12 questions total)
        ],
        "background_reading": "<4-5 paragraphs of advanced context. Include research methodology, historical evolution, scientific principles, policy implications.>",
        "analysis": "<Detailed analytical commentary - 3-4 paragraphs analyzing article's strengths, potential biases, methodological considerations, field implications, and gaps in coverage.>",
        "perspectives": [
          {{"perspective": "<Sophisticated positive viewpoint with nuanced arguments - 2-3 sentences>", "attitude": "positive"}},
          {{"perspective": "<Sophisticated negative viewpoint with nuanced arguments - 2-3 sentences>", "attitude": "negative"}},
          {{"perspective": "<Nuanced neutral viewpoint acknowledging trade-offs and complexity - 2-3 sentences>", "attitude": "neutral"}}
        ]
      }},
      "CN": {{
        "title": "<Complete Chinese translation of the article's main title - CHINESE ONLY>",
        "summary": "<Comprehensive Chinese translation of the entire article content, approximately 500 words. CHINESE ONLY - DO NOT mix English. Maintain original meaning, tone, and key information. Use standard Simplified Chinese.>"
      }}
    }}
  }}
}}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no code fences, no explanations
2. Easy level: ENGLISH ONLY - 200-300 word summary, 5 questions, simple vocabulary
3. Mid level: ENGLISH ONLY - 300-400 word summary, 8-10 questions, intermediate terminology  
4. Hard level: ENGLISH ONLY - 400-500 word summary, 10-12 questions, technical terminology, includes analysis
5. CN level: CHINESE ONLY - 500-word complete Chinese translation of entire article
6. ⚠️ NO CHINESE TEXT IN EASY/MID/HARD LEVELS - Chinese content belongs ONLY in CN level
7. ⚠️ NO ENGLISH TEXT IN CN LEVEL - All CN level content must be in Chinese
8. All levels: Exactly 10 keywords, 3 perspectives (positive/negative/neutral)
9. All correct_answer values MUST match one of the options exactly
10. Randomize option positions - don't always put correct answer in same spot
11. Keywords should be central to understanding the article

Generate the complete analysis now."""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert educational content creator and analyst. Return responses ONLY as valid JSON with no additional text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 8000
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
            
            # Parse and save response
            try:
                feedback = json.loads(content)
                
                # Save response to file with timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                response_file = pathlib.Path(f"responses/response_article_{article_id}_{timestamp}.json")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(response_file, 'w', encoding='utf-8') as f:
                    json.dump(feedback, f, ensure_ascii=False, indent=2)
                
                print(f"✓ Saved response to: {response_file}")
                print(f"✓ Response contains levels: {list(feedback.get('article_analysis', {}).get('levels', {}).keys())}")
                
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON response: {e}")
                print(f"Response content (first 500 chars): {content[:500]}")
        else:
            print(f"✗ Unexpected response format from DeepSeek")
            print(f"Response: {result}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_single_article.py <article_id>")
        sys.exit(1)
    
    article_id = int(sys.argv[1])
    process_article(article_id)
