#!/usr/bin/env python3
"""
Test script: Process ONE article with compact prompt and save response to disk.
Uses confirmed timeout=(30, 300) format.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import requests
from urllib.parse import urljoin

# Get API key
api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    print("ERROR: DEEPSEEK_API_KEY not set")
    sys.exit(1)

# Configuration
DB_PATH = '/Users/jidai/news/articles.db'
API_URL = 'https://api.deepseek.com/chat/completions'
OUTPUT_DIR = '/Users/jidai/news'

# Compact prompts dictionary
COMPACT_PROMPTS = {
    'default': """You are an expert editorial analyst and educator. Analyze this article for three difficulty levels (easy/mid/hard) and return a JSON with:
- Summaries: easy (100-200w), mid (300-500w), hard (500-700w), zh_hard (500-700w Chinese)
- Keywords: 10 per level with explanations
- Questions: 8 (easy), 10 (mid), 12 (hard) multiple choice with 4 options each
- Background reading: 100-150w (easy), 150-250w (mid), 200-300w (hard)
- Analysis: mid and hard levels only, ~100w each analyzing article structure and arguments
- Perspectives: 2 perspectives + synthesis for each level, each with attitude (positive/neutral/negative)
- Synthesis always has attitude "neutral"

ARTICLE:
{articles_json}

Return ONLY valid JSON with no markdown formatting.""",
    
    'sports': """You are an expert sports analyst and educator. Analyze this sports article for three difficulty levels and return JSON with:
- Summaries explaining athletic performance simply
- Keywords relevant to sports: athletes, competitions, records, techniques
- Questions about sport performance and strategy
- Background on sport context and rules
- Perspectives on athletic achievement from different viewpoints

ARTICLE:
{articles_json}

Return ONLY valid JSON.""",
    
    'tech': """You are an expert technology analyst and educator. Analyze this tech article for three difficulty levels and return JSON with:
- Summaries explaining technology clearly (simple to technical)
- Keywords: tech terms, products, innovations, methods
- Questions about tech concepts and implications
- Background on technology context and market
- Perspectives on technological impact and adoption

ARTICLE:
{articles_json}

Return ONLY valid JSON.""",
    
    'science': """You are an expert science communicator and educator. Analyze this science article for three difficulty levels and return JSON with:
- Summaries explaining research simply (basic to advanced)
- Keywords: scientific terms, organisms, methods, concepts
- Questions about discoveries, methodology, implications
- Background on scientific context and field
- Perspectives on research significance and applications

ARTICLE:
{articles_json}

Return ONLY valid JSON.""",
    
    'politics': """You are an expert political analyst and civics educator. Analyze this political article for three difficulty levels and return JSON with:
- Summaries explaining politics clearly (simple to complex)
- Keywords: political terms, policies, institutions, actors
- Questions about governance, policy, and political dynamics
- Background on political context and history
- Perspectives on political issues from different viewpoints

ARTICLE:
{articles_json}

Return ONLY valid JSON.""",
}

def get_category_name(category_id):
    """Map category_id to prompt key"""
    category_map = {
        1: 'default',      # US News
        2: 'default',      # World News
        3: 'sports',       # Sports
        4: 'tech',         # Technology
        5: 'science',      # Science
        6: 'politics',     # Politics
        7: 'default',      # Business
        8: 'default',      # Health
    }
    return category_map.get(category_id, 'default')

def fetch_article_data(article_id):
    """Fetch article from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, description, content, category_id, deepseek_processed 
            FROM articles 
            WHERE id = ?
        """, (article_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"ERROR: Article {article_id} not found")
            return None
        
        return dict(row)
    finally:
        conn.close()

def process_article_with_api(article, prompt_template):
    """Send article to Deepseek API and get response"""
    
    # Prepare article JSON - use description if content is too long, otherwise use content
    article_content = article['content'] if article['content'] else article['description']
    if len(article_content) > 1500:
        article_content = article_content[:1500]
    
    article_json = json.dumps({
        'title': article['title'],
        'description': article['description'],
        'content': article_content
    }, ensure_ascii=False, indent=2)
    
    # Format prompt with article
    prompt = prompt_template.format(articles_json=article_json)
    
    print(f"\n{'='*60}")
    print(f"Processing Article ID: {article['id']}")
    print(f"Title: {article['title'][:50]}...")
    print(f"Category ID: {article['category_id']}")
    print(f"Prompt size: {len(prompt)} characters")
    print(f"{'='*60}")
    
    # Prepare request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.7,
        'max_tokens': 6000,
    }
    
    try:
        print("Sending request to Deepseek API...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=(30, 300)  # CRITICAL: (connect_timeout, read_timeout)
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: API returned {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        # Parse response
        api_response = response.json()
        
        if 'choices' not in api_response or len(api_response['choices']) == 0:
            print("ERROR: No choices in API response")
            return None
        
        content = api_response['choices'][0]['message']['content']
        print(f"Response received: {len(content)} characters")
        
        # Try to parse as JSON to validate
        try:
            parsed_json = json.loads(content)
            print(f"✓ Valid JSON response")
            print(f"  Keys: {list(parsed_json.keys())}")
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"ERROR: Response is not valid JSON: {e}")
            print(f"Content preview: {content[:200]}")
            return None
            
    except requests.exceptions.Timeout as e:
        print(f"ERROR: Request timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return None

def main():
    """Main function"""
    
    # Get first unprocessed article
    print("\n" + "="*60)
    print("COMPACT PROMPT TEST - SINGLE ARTICLE")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM articles 
        WHERE deepseek_processed = 0 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("ERROR: No unprocessed articles found")
        sys.exit(1)
    
    article_id = row[0]
    print(f"\nFound unprocessed article: ID {article_id}")
    
    # Fetch article
    article = fetch_article_data(article_id)
    if not article:
        sys.exit(1)
    
    # Get appropriate prompt
    category_name = get_category_name(article['category_id'])
    prompt_template = COMPACT_PROMPTS.get(category_name, COMPACT_PROMPTS['default'])
    print(f"Using prompt: {category_name.upper()}")
    
    # Process article
    result = process_article_with_api(article, prompt_template)
    
    if result is None:
        print("\nERROR: Failed to process article")
        sys.exit(1)
    
    # Save to disk
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'test_compact_response_{timestamp}.json'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    output_data = {
        'article_id': article_id,
        'title': article['title'],
        'category_id': article['category_id'],
        'category_name': category_name,
        'timestamp': timestamp,
        'response': result
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ SUCCESS: Response saved to {output_filename}")
    print(f"{'='*60}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    print(f"Full path: {output_path}")
    print(f"\nResponse structure:")
    print(f"  - article_id: {output_data['article_id']}")
    print(f"  - title: {output_data['title'][:60]}...")
    print(f"  - category_name: {output_data['category_name']}")
    print(f"  - Response keys: {list(result.keys())}")

if __name__ == '__main__':
    main()
