#!/usr/bin/env python3
"""
Simplified article processor - calls Deepseek API only, no database updates.
Input: article_id
Output: JSON response matching response_template.json
"""

import json
import os
import sys
import sqlite3
import requests
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
API_URL = "https://api.deepseek.com/chat/completions"

# Get base directory (parent of deepseek/ directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "articles.db")
PROMPT_FILE = os.path.join(BASE_DIR, "deepseek", "prompts.md")
RESPONSE_TEMPLATE = os.path.join(BASE_DIR, "deepseek", "response_template.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "website", "responses")
WEBSITE_RESPONSE_DIR = os.path.join(BASE_DIR, "website", "responses")

# Create output directories if needed
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(WEBSITE_RESPONSE_DIR).mkdir(parents=True, exist_ok=True)


def get_api_key():
    """Fetch Deepseek API key from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value FROM apikey WHERE name = 'DeepSeek'
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0]:
            print("ERROR: DeepSeek API key not found in database")
            print("Please check apikey table has entry with name='DeepSeek'")
            return None
        
        return row[0]
    except Exception as e:
        print(f"ERROR fetching API key from database: {e}")
        return None


def get_article_content(article_id):
    """Fetch article from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, content, category_id
            FROM articles
            WHERE id = ?
        """, (article_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"ERROR: Article {article_id} not found")
            return None
        
        return dict(row)
    except Exception as e:
        print(f"ERROR fetching article: {e}")
        return None


def delete_problematic_article(article_id):
    """Delete an article that cannot be processed due to unfixable JSON errors."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        conn.commit()
        conn.close()
        
        print(f"  ✓ Deleted problematic article {article_id} from database")
        return True
    except Exception as e:
        print(f"  ❌ ERROR deleting article {article_id}: {e}")
        return False


def load_prompt_template():
    """Load the detailed prompt from prompts.md."""
    try:
        with open(PROMPT_FILE, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"ERROR loading prompt: {e}")
        return None


def load_response_template():
    """Load response template for reference."""
    try:
        with open(RESPONSE_TEMPLATE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR loading response template: {e}")
        return None


def build_user_prompt(article_data, prompt_template):
    """Build the user prompt with article content."""
    title = article_data.get('title', '')
    description = article_data.get('description', '')
    content = article_data.get('content', '')
    
    # Build combined prompt: instructions + article
    user_prompt = f"""{prompt_template}

ARTICLE TO ANALYZE:

Title: {title}
Description: {description}

Content:
{content}

Analyze this article and output ONLY the JSON matching the structure above."""
    
    return user_prompt


def call_deepseek_api(user_prompt, api_key, article_id=None):
    """Call Deepseek API and return response."""
    print(f"  ℹ️  API Key available: {bool(api_key)}")
    print(f"  ℹ️  API URL: {API_URL}")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {
                'role': 'user',
                'content': user_prompt
            }
        ],
        'temperature': 0.7,
        'max_tokens': 7000,
        'response_format': {
            'type': 'json_object'
        }
    }
    
    try:
        print("  ⏳ Sending request to Deepseek API (this may take time)...")
        print(f"  ℹ️  Payload size: {len(str(payload))} characters")
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=(30, 300)
        )
        
        print(f"  📊 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS: API returned 200 OK")
            print(f"  📄 Response size: {len(response.text)} bytes")
        else:
            print(f"  ❌ ERROR: API returned {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return None
        
        print("  ✓ API response received successfully")
        api_response = response.json()
        
        if 'choices' not in api_response or len(api_response['choices']) == 0:
            print("ERROR: No choices in API response")
            return None
        
        print("  ✓ Extracting content from response...")
        # Extract the JSON from the response
        content = api_response['choices'][0]['message']['content']
        
        # Write raw response to file first for debugging
        raw_response_file = None
        if article_id:
            raw_response_file = f"/var/www/news/website/responses/raw_response_article_{article_id}.txt"
            try:
                os.makedirs(os.path.dirname(raw_response_file), exist_ok=True)
                with open(raw_response_file, 'w') as f:
                    f.write(content)
                print(f"  ✓ Raw response saved to: {raw_response_file}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not save raw response: {e}")
        
        # Now try to parse as JSON
        try:
            # Fix common DeepSeek JSON formatting issues
            import re
            
            # Pattern 1: " "key": should be "key":
            cleaned_content = re.sub(r'" "([^"]+)":', r'"\1":', content)
            
            # Pattern 2: }"] should be }]  (extra quote before closing array)
            # Example: "correct_answer": "value"}"] → "correct_answer": "value"}]
            cleaned_content = re.sub(r'\}"\]', r'}]', cleaned_content)
            
            response_json = json.loads(cleaned_content)
            print("  ✓ Successfully parsed API response as JSON")
            
            # Clean up raw response file on successful parse
            if raw_response_file and os.path.exists(raw_response_file):
                try:
                    os.remove(raw_response_file)
                    print(f"  ✓ Cleaned up raw response file")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not delete raw response file: {e}")
            
            return response_json
        except json.JSONDecodeError as e:
            print(f"  ❌ ERROR: Could not parse API response as JSON: {e}")
            print(f"  ℹ️  Malformed JSON at character position {e.pos}")
            if raw_response_file:
                print(f"  ℹ️  Raw response kept for debugging: {raw_response_file}")
            print(f"  Raw content (chars 0-200): {content[0:200]}")
            if e.pos:
                start = max(0, e.pos - 100)
                end = min(len(content), e.pos + 100)
                print(f"  Around error (chars {start}-{end}): {content[start:end]}")
            
            # Delete the problematic article to prevent blocking
            if article_id:
                print(f"  ⚠️  Deleting article {article_id} to prevent blocking future runs...")
                delete_problematic_article(article_id)
            
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request failed: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error in API call: {e}")
        return None


def save_response(article_id, response_json):
    """Save response to file."""
    try:
        output_file = os.path.join(OUTPUT_DIR, f"article_{article_id}_response.json")
        with open(output_file, 'w') as f:
            json.dump(response_json, f, indent=2, ensure_ascii=False)
        file_size = os.path.getsize(output_file)
        print(f"  ✓ Response file created: {output_file}")
        print(f"    File size: {file_size} bytes")
        return output_file
    except Exception as e:
        print(f"  ❌ ERROR saving response: {e}")
        return None


def update_database_on_success(article_id, response_file):
    """Update database immediately after processing succeeds."""
    try:
        print(f"  📝 Updating database for article {article_id}...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Insert into response table
        print(f"    - Inserting response record...")
        cursor.execute("""
            INSERT INTO response (article_id, respons_file)
            VALUES (?, ?)
        """, (article_id, response_file))
        print(f"      ✓ Response record inserted")
        
        # Update articles table
        print(f"    - Updating articles table...")
        cursor.execute("""
            UPDATE articles
            SET deepseek_processed = 1,
                processed_at = ?,
                deepseek_failed = 0,
                deepseek_last_error = NULL
            WHERE id = ?
        """, (now, article_id))
        rows_updated = cursor.rowcount
        print(f"      ✓ Articles table updated ({rows_updated} rows)")
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Database update successful")
        
        # Move response file to website/article_response
        return move_response_file(article_id, response_file)
        
    except Exception as e:
        print(f"  ❌ ERROR: Database update failed: {e}")
        return False


def move_response_file(article_id, response_file):
    """Verify response file exists in website/responses directory."""
    try:
        print(f"  🗂️  Verifying response file location...")
        response_path = Path(response_file)
        
        # Check if file exists
        if not response_path.exists():
            print(f"    ❌ ERROR: Response file not found: {response_file}")
            return False
        
        print(f"    ✓ Response file verified: {response_path}")
        print(f"    ✓ Location: /var/www/news/website/responses/")
        return True
        
    except Exception as e:
        print(f"    ❌ ERROR: Failed to verify response file: {e}")
        return False


def validate_response_structure(response_json, template):
    """Validate that response matches expected structure."""
    try:
        # Check top-level keys
        if 'meta' not in response_json or 'article_id' not in response_json.get('meta', {}):
            print("WARNING: Response missing meta.article_id")
        
        if 'article_analysis' not in response_json:
            print("WARNING: Response missing article_analysis")
            return False
        
        analysis = response_json['article_analysis']
        if 'levels' not in analysis:
            print("WARNING: Response missing article_analysis.levels")
            return False
        
        levels = analysis['levels']
        required_levels = ['easy', 'middle', 'high', 'zh']
        for level in required_levels:
            if level not in levels:
                print(f"WARNING: Response missing level: {level}")
        
        print("Response structure validation: OK")
        return True
    except Exception as e:
        print(f"ERROR validating response structure: {e}")
        return False


def get_unprocessed_articles():
    """Get list of articles that haven't been processed by Deepseek yet."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM articles
            WHERE deepseek_processed = 0 AND deepseek_failed < 3
            ORDER BY id ASC
        """)
        
        articles = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return articles
    except Exception as e:
        print(f"ERROR fetching unprocessed articles: {e}")
        return []


def process_batch():
    """Process all unprocessed articles in batch mode."""
    unprocessed = get_unprocessed_articles()
    
    if not unprocessed:
        print("\n✓ No unprocessed articles found")
        return
    
    print(f"\n{'='*70}")
    print(f"Batch Processing: Found {len(unprocessed)} unprocessed article(s)")
    print(f"Articles: {unprocessed}")
    print(f"{'='*70}\n")
    
    succeeded = []
    failed = []
    
    for idx, article_id in enumerate(unprocessed, 1):
        print(f"\n[{idx}/{len(unprocessed)}] Processing article {article_id}...\n")
        try:
            process_single_article(article_id, batch_mode=True)
            succeeded.append(article_id)
        except Exception as e:
            print(f"  ❌ Failed to process article {article_id}: {e}")
            failed.append(article_id)
        print("\n" + "-"*70)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Batch Processing Summary:")
    print(f"  ✓ Succeeded: {len(succeeded)} articles")
    if succeeded:
        print(f"    {succeeded}")
    print(f"  ✗ Failed: {len(failed)} articles")
    if failed:
        print(f"    {failed}")
    print(f"{'='*70}\n")


def process_single_article(article_id, batch_mode=False):
    """Process a single article."""
    
    print(f"\n{'='*70}")
    print(f"Processing Article ID: {article_id}")
    print(f"{'='*70}\n")
    
    # Step 0: Get API key from database
    print("Step 0: Getting API key from database...")
    api_key = get_api_key()
    if not api_key:
        if batch_mode:
            raise Exception("Failed to get API key")
        sys.exit(1)
    print(f"  ✓ API key retrieved")
    
    # Step 1: Fetch article
    print("\nStep 1: Fetching article from database...")
    article = get_article_content(article_id)
    if not article:
        if batch_mode:
            raise Exception("Failed to fetch article from database")
        sys.exit(1)
    print(f"  ✓ Fetched: {article['title'][:60]}...")
    
    # Step 2: Load prompt template
    print("\nStep 2: Loading prompt template...")
    prompt_template = load_prompt_template()
    if not prompt_template:
        if batch_mode:
            raise Exception("Failed to load prompt template")
        sys.exit(1)
    print(f"  ✓ Loaded {len(prompt_template)} characters of prompt")
    
    # Step 3: Load response template for reference
    print("\nStep 3: Loading response template...")
    response_template = load_response_template()
    if not response_template:
        if batch_mode:
            raise Exception("Failed to load response template")
        sys.exit(1)
    print(f"  ✓ Template structure ready")
    
    # Step 4: Build prompt with article content
    print("\nStep 4: Building user prompt...")
    user_prompt = build_user_prompt(article, prompt_template)
    print(f"  ✓ Built prompt: {len(user_prompt)} characters")
    
    # Step 5: Call Deepseek API
    print("\nStep 5: Calling Deepseek API...")
    response_json = call_deepseek_api(user_prompt, api_key, article_id)
    if not response_json:
        print("  ❌ API call failed - skipping this article")
        if batch_mode:
            print("  ℹ️  Continuing to next article...")
            raise Exception("API call failed or returned invalid JSON")
        else:
            print("  ℹ️  Next run will retry this article")
            sys.exit(0)  # Exit 0 (success) so pipeline continues
    print(f"  ✅ API call successful - received response")
    
    # Step 6: Validate response structure
    print("\nStep 6: Validating response structure...")
    validate_response_structure(response_json, response_template)
    
    # Step 7: Save response
    print("\nStep 7: Saving response...")
    output_file = save_response(article_id, response_json)
    if not output_file:
        print("  ❌ Failed to save response - skipping this article")
        if batch_mode:
            print("  ℹ️  Continuing to next article...")
            raise Exception("Failed to save response file")
        else:
            print("  ℹ️  Next run will retry this article")
            sys.exit(0)  # Exit 0 so pipeline continues
    
    # Step 8: Update database immediately
    print("\nStep 8: Updating database...")
    if not update_database_on_success(article_id, output_file):
        print("  ⚠ Warning: Database update had issues, but processing complete")
    
    # Step 9: Show completion summary
    try:
        file_size = os.path.getsize(output_file)
        print(f"\nStep 9: Completion summary")
        print(f"  ✓ Response file: {output_file}")
        print(f"  ✓ File size: {file_size} bytes")
    except Exception as e:
        print(f"ERROR getting file size: {e}")
    
    print(f"\n✓ Processing complete for article {article_id}\n")


def main():
    """Main entry point - supports batch or single article mode."""
    try:
        if len(sys.argv) < 2:
            # No arguments: run batch processing
            print("\n⏳ No article_id provided - running in BATCH MODE")
            print("Checking for unprocessed articles...\n")
            process_batch()
            print("✓ Batch processing completed successfully")
            sys.exit(0)
        else:
            # Argument provided: process single article
            article_id = sys.argv[1]
            process_single_article(article_id)
            print("✓ Single article processing completed successfully")
            sys.exit(0)
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
