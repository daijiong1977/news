#!/usr/bin/env python3
"""
DeepSeek Research Mode Processor - Testing alternative API mode for better performance.
Compares with chat mode to see which gives better analysis quality.
"""

import requests
import json
import time
import sqlite3
import sys
from pathlib import Path
from typing import Optional
from argparse import ArgumentParser

DEEPSEEK_API_KEY = "sk-0ad0e8ca48544dd79ef790d17672eed2"
DEEPSEEK_RESEARCH_URL = "https://api.deepseek.com/beta/chat/completions"  # Research endpoint
DB_FILE = "articles.db"

def create_research_prompt(articles: list[dict]) -> str:
    """Create research-focused prompt for deeper analysis."""
    
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    
    prompt = f"""You are an expert research analyst and educational content specialist. 
Conduct deep research analysis on the following {len(articles)} article(s).

For EACH article, provide COMPREHENSIVE research-backed analysis in this JSON format:

{{
    "article_id": <id>,
    "research_summary_en": "<500-700 word detailed research summary with context and implications>",
    "research_summary_zh": "<500-700 word Chinese translation with research insights>",
    "research_keywords": [
        {{
            "keyword": "<specialized term or concept>",
            "frequency": <occurrence count>,
            "research_context": "<100-150 word explanation of how this relates to research/academia>"
        }},
        ... (top 8-12 research-relevant keywords)
    ],
    "research_context": "<300-400 word deep research background with historical/scientific context>",
    "critical_analysis": {{
        "strengths": ["<research insight 1>", "<insight 2>"],
        "limitations": ["<limitation 1>", "<limitation 2>"],
        "research_gaps": ["<gap 1>", "<gap 2>"]
    }},
    "deep_questions": [
        {{
            "question": "<challenging research-level question>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<detailed explanation with research basis>",
            "difficulty": "<basic/intermediate/advanced>",
            "cognitive_level": "<knowledge/comprehension/application/analysis/synthesis/evaluation>"
        }},
        ... (10 questions: mix of difficulty levels)
    ],
    "research_perspectives": {{
        "academic_view": {{
            "title": "<academic/scientific perspective>",
            "reasoning": "<detailed academic reasoning>"
        }},
        "practical_view": {{
            "title": "<practical/applied perspective>",
            "reasoning": "<practical implications and real-world application>"
        }},
        "research_gap_analysis": "<what additional research is needed to fully understand this topic>"
    }}
}}

IMPORTANT:
1. Research summaries (500-700 words) should be academically rigorous
2. Keywords should include specialized terms, not common words
3. Deep questions should test higher-order thinking (Bloom's taxonomy levels 4-6)
4. Include cognitive level for each question
5. Perspectives should emphasize research implications, not just opinions
6. Identify research gaps and areas needing further study
7. Use academic language and cite implicit connections to research
8. Return ONLY valid JSON, one object per article

ARTICLES TO RESEARCH:
{articles_json}

Generate comprehensive research-based analysis for all {len(articles)} articles. Return ONLY the JSON response."""
    
    return prompt


def send_to_deepseek_research(prompt: str, batch_num: int = 1) -> Optional[str]:
    """Send prompt to DeepSeek RESEARCH API and get response."""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Research mode uses slightly different parameters
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert research analyst providing deep, academically rigorous analysis. Focus on research implications, academic context, and critical thinking. Return responses only in valid JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,  # Lower temperature for more focused analysis
        "max_tokens": 8000,
        "thinking": {
            "type": "enabled",
            "budget_tokens": 5000
        }
    }
    
    print(f"\n📤 Sending batch {batch_num} to DeepSeek RESEARCH API (with extended thinking)...")
    print(f"   Payload size: {len(json.dumps(payload)) / 1024:.1f} KB")
    print(f"   Mode: Research with thinking enabled")
    print(f"   Temperature: 0.5 (for focused analysis)")
    print(f"   Timeout: 300 seconds...")
    
    try:
        start_time = time.time()
        response = requests.post(DEEPSEEK_RESEARCH_URL, json=payload, headers=headers, timeout=(30, 300))
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            
            print(f"✓ Received response from DeepSeek RESEARCH (batch {batch_num})")
            print(f"  Response time: {elapsed:.1f} seconds")
            return content
        else:
            print(f"✗ Unexpected response format from DeepSeek")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")
        return None


def process_with_research_mode(batch_size: int = 1, max_batches: Optional[int] = None):
    """Process articles using research mode API."""
    
    print("\n" + "="*70)
    print("🔬 DeepSeek RESEARCH MODE PROCESSOR")
    print("="*70)
    print("This processor uses research-focused analysis with extended thinking.")
    print("Results will be saved for comparison with chat mode.\n")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get unprocessed articles
    cursor.execute("""
        SELECT id FROM articles 
        WHERE deepseek_processed = 0
        ORDER BY date_iso DESC
        LIMIT ?
    """, (batch_size,))
    
    article_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not article_ids:
        print("✓ No articles to process")
        return
    
    print(f"Found {len(article_ids)} unprocessed articles")
    print(f"Processing with batch_size={batch_size}, max_batches={max_batches}\n")
    
    batch_num = 1
    for article_id in article_ids[:batch_size]:
        if max_batches and batch_num > max_batches:
            break
        
        # Get article content
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        article = dict(cursor.fetchone())
        conn.close()
        
        # Read full content
        content_file = article['content_file']
        if Path(content_file).exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = article['snippet']
        
        article_data = [{
            "id": article['id'],
            "title": article['title'],
            "source": article['source'],
            "link": article['link'],
            "snippet": article['snippet'],
            "content": content,
            "date": article['date_iso']
        }]
        
        print(f"{'='*70}")
        print(f"BATCH {batch_num}: Processing article {article['id']}")
        print(f"{'='*70}")
        print(f"  Title: {article['title'][:60]}...")
        
        # Create prompt
        prompt = create_research_prompt(article_data)
        
        # Send to research API
        response_text = send_to_deepseek_research(prompt, batch_num=batch_num)
        
        if response_text:
            # Save response to file for inspection
            response_file = f"deepseek_research_batch_{batch_num}.json"
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"✓ Response saved to {response_file}")
            
            # Try to parse and validate
            try:
                feedback = json.loads(response_text)
                if isinstance(feedback, list):
                    feedbacks = feedback
                else:
                    feedbacks = [feedback]
                
                print(f"✓ Successfully parsed JSON response")
                print(f"  Questions generated: {len(feedbacks[0].get('deep_questions', []))}")
                print(f"  Keywords identified: {len(feedbacks[0].get('research_keywords', []))}")
                
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON: {e}")
        else:
            print(f"✗ Failed to get response from DeepSeek")
        
        # Rate limiting
        print(f"⏳ Waiting 3 seconds before next batch...")
        time.sleep(3)
        batch_num += 1


def main():
    parser = ArgumentParser(description="Process articles with DeepSeek Research Mode")
    parser.add_argument("--batch-size", type=int, default=1, help="Number of articles per batch")
    parser.add_argument("--max-batches", type=int, default=1, help="Maximum number of batches to process")
    parser.add_argument("--test-api", action="store_true", help="Test API connectivity first")
    
    args = parser.parse_args()
    
    if args.test_api:
        print("Testing DeepSeek Research API connectivity...")
        test_payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Respond with: RESEARCH_TEST"}],
            "temperature": 0.5,
            "max_tokens": 100
        }
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(DEEPSEEK_RESEARCH_URL, json=test_payload, headers=headers, timeout=30)
            if response.status_code == 200:
                print("✓ API connectivity test PASSED")
            else:
                print(f"✗ API test failed: {response.status_code}")
        except Exception as e:
            print(f"✗ API test error: {e}")
        return
    
    process_with_research_mode(batch_size=args.batch_size, max_batches=args.max_batches)


if __name__ == "__main__":
    main()
