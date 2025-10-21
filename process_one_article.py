#!/usr/bin/env python3
"""
Simple single-article processor for Deepseek
Use: python3 process_one_article.py <article_id>
Processes ONE article at a time with verified prompt.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import requests

# Get API key
api_key = os.environ.get('DEEPSEEK_API_KEY', 'sk-dd996c4863a04d3ebad13c7ee52ca31b')
if not api_key:
    print("ERROR: DEEPSEEK_API_KEY not set")
    sys.exit(1)

# Configuration
DB_PATH = os.path.join(os.getcwd(), 'articles.db')
API_URL = 'https://api.deepseek.com/chat/completions'
OUTPUT_DIR = os.getcwd()

# Load example structure to show AI the exact format
EXAMPLE_JSON_PATH = os.path.join(os.getcwd(), 'example_response_structure.json')
with open(EXAMPLE_JSON_PATH) as f:
    example_data = json.load(f)
    # Use only the easy level as a minimal example to keep prompt size down
    EXAMPLE_JSON_STR = json.dumps({"article_analysis": {"levels": {"easy": example_data["article_analysis"]["levels"]["easy"], "mid": "...", "hard": "..."}}}, indent=2)

# Compact prompts dictionary - WITH EXAMPLE JSON
COMPACT_PROMPTS = {
    'default': f"""You are an expert editorial analyst and educator. Analyze this article for three difficulty levels (easy/mid/hard) and return a JSON EXACTLY matching this structure:

CRITICAL REQUIREMENTS:
- Include zh_title: Chinese translation of the article title
- Include zh_hard in hard level: 500-700 word Chinese summary for hard level
- All other fields as specified below

EXAMPLE STRUCTURE (follow this exactly):
{EXAMPLE_JSON_STR.replace('{', '{{').replace('}', '}}')}

Requirements:
- Summaries: easy (100-200w), mid (300-500w), hard (500-700w), zh_hard (500-700w Chinese)
- Keywords: 10 per level with explanations
- Questions: 8 (easy), 10 (mid), 12 (hard) multiple choice with 4 options each
- Background reading: 100-150w (easy), 150-250w (mid), 200-300w (hard)
- Analysis: mid and hard levels only, ~100w each analyzing article structure and arguments
- Perspectives: 2 perspectives + synthesis for each level, each with attitude (positive/neutral/negative)
- Synthesis always has attitude "neutral"

ARTICLE:
{{articles_json}}

Return ONLY valid JSON matching the example structure above. No markdown. No explanations.""",
}

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

def get_category_prompt(category_id):
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
    
    # Prepare article JSON - use content if available, otherwise description
    article_content = article['content'] if article['content'] else article['description']
    if article_content and len(article_content) > 1500:
        article_content = article_content[:1500]
    
    article_json = json.dumps({
        'title': article['title'],
        'description': article['description'],
        'content': article_content
    }, ensure_ascii=False, indent=2)
    
    # Format prompt with article
    prompt = prompt_template.format(articles_json=article_json)
    
    print(f"\n{'='*70}")
    print(f"Processing Article ID: {article['id']}")
    print(f"Title: {article['title'][:60]}...")
    print(f"Category ID: {article['category_id']}")
    print(f"Prompt size: {len(prompt)} characters")
    print(f"{'='*70}")
    
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
        'response_format': {
            'type': 'json_object',
            'json_schema': {
                'name': 'article_analysis',
                'description': 'Article analysis with three difficulty levels and Chinese translations',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'article_analysis': {
                            'type': 'object',
                            'properties': {
                                'title': {'type': 'string'},
                                'zh_title': {'type': 'string', 'description': 'Chinese translation of the article title'},
                                'levels': {
                                    'type': 'object',
                                    'properties': {
                                        'easy': {
                                            'type': 'object',
                                            'properties': {
                                                'summary': {'type': 'string'},
                                                'keywords': {
                                                    'type': 'array',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'term': {'type': 'string'},
                                                            'explanation': {'type': 'string'}
                                                        }
                                                    }
                                                },
                                                'questions': {
                                                    'type': 'array',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'question': {'type': 'string'},
                                                            'options': {
                                                                'type': 'array',
                                                                'items': {'type': 'string'}
                                                            },
                                                            'correct_answer': {'type': 'string'}
                                                        }
                                                    }
                                                },
                                                'background_reading': {'type': 'string'},
                                                'perspectives': {
                                                    'type': 'array',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'perspective': {'type': 'string'},
                                                            'attitude': {'type': 'string', 'enum': ['positive', 'neutral', 'negative']}
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        'mid': {
                                            'type': 'object',
                                            'properties': {
                                                'summary': {'type': 'string'},
                                                'keywords': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                },
                                                'questions': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                },
                                                'background_reading': {'type': 'string'},
                                                'analysis': {'type': 'string'},
                                                'perspectives': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                }
                                            }
                                        },
                                        'hard': {
                                            'type': 'object',
                                            'properties': {
                                                'summary': {'type': 'string'},
                                                'keywords': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                },
                                                'questions': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                },
                                                'background_reading': {'type': 'string'},
                                                'analysis': {'type': 'string'},
                                                'zh_hard': {'type': 'string'},
                                                'perspectives': {
                                                    'type': 'array',
                                                    'items': {'type': 'object'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
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
    print("PROCESS ONE ARTICLE - SAVE TO DISK FOR VERIFICATION")
    print("="*70)
    
    # Get first unprocessed article
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
        print("No unprocessed articles found")
        return
    
    article_id = row[0]
    print(f"Found unprocessed article: ID {article_id}")
    
    # Fetch article
    article = fetch_article_data(article_id)
    if not article:
        sys.exit(1)
    
    # Get appropriate prompt
    prompt_name = get_category_prompt(article['category_id'])
    prompt_template = COMPACT_PROMPTS.get(prompt_name, COMPACT_PROMPTS['default'])
    print(f"Using prompt: {prompt_name.upper()}")
    
    # Process article
    response = process_article_with_api(article, prompt_template)
    
    if response is None:
        print("\nERROR: Failed to process article")
        sys.exit(1)
    
    # Save response to disk for verification
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'response_article_{article_id}_{timestamp}.json'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, 'w') as f:
        json.dump(response, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Response saved to: {output_filename}")
    print(f"Full path: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    print(f"{'='*70}")
    
    # Display response structure for verification
    print("\n" + "="*70)
    print("RESPONSE STRUCTURE FOR VERIFICATION")
    print("="*70)
    
    try:
        if 'article_analysis' in response:
            aa = response['article_analysis']
            print(f"\n✓ Has 'article_analysis' key")
            
            if 'zh_title' in aa and aa['zh_title']:
                print(f"✓ Has 'zh_title': {aa['zh_title'][:60]}...")
            else:
                print(f"✗ Missing or empty 'zh_title'")
            
            if 'levels' in aa:
                print(f"✓ Has 'levels' key")
                levels = aa['levels']
                
                for level_name in ['easy', 'mid', 'hard']:
                    if level_name in levels:
                        level = levels[level_name]
                        print(f"\n  {level_name.upper()}:")
                        print(f"    ✓ summary: {len(level.get('summary', ''))} chars")
                        print(f"    ✓ keywords: {len(level.get('keywords', []))} items")
                        print(f"    ✓ questions: {len(level.get('questions', []))} items")
                        print(f"    ✓ background_reading: {len(level.get('background_reading', ''))} chars")
                        
                        if 'analysis' in level:
                            print(f"    ✓ analysis: {len(level['analysis'])} chars")
                        
                        if 'zh_hard' in level and level['zh_hard']:
                            print(f"    ✓ zh_hard: {len(level['zh_hard'])} chars")
                        elif level_name == 'hard':
                            print(f"    ✗ Missing zh_hard (Chinese summary for hard level)")
                        
                        perspectives = level.get('perspectives', [])
                        print(f"    ✓ perspectives: {len(perspectives)} items")
                    else:
                        print(f"\n  ✗ MISSING level: {level_name}")
            else:
                print(f"✗ Missing 'levels' key")
        else:
            print(f"✗ Missing 'article_analysis' key")
    
    except Exception as e:
        print(f"✗ Error analyzing response: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("NEXT STEP:")
    print(f"1. Check the file: {output_filename}")
    print(f"2. Verify the structure looks correct")
    print(f"3. Once confirmed, run: python3 insert_from_response.py {output_path}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
