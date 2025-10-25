#!/usr/bin/env python3
"""
Insert Deepseek response into database.
Updates response table and articles table based on processing result.
Then moves response file to website/article_response directory.
"""

import json
import sys
import sqlite3
import shutil
import os
from datetime import datetime
from pathlib import Path

# Get base directory (parent of deepseek/ directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "articles.db")
WEBSITE_RESPONSE_DIR = os.path.join(BASE_DIR, "website", "article_response")


def update_on_success(article_id, response_file):
    """Update database when processing succeeds."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Insert into response table
        cursor.execute("""
            INSERT INTO response (article_id, respons_file)
            VALUES (?, ?)
        """, (article_id, response_file))
        
        # Update articles table
        cursor.execute("""
            UPDATE articles
            SET deepseek_processed = 1,
                processed_at = ?,
                deepseek_failed = 0,
                deepseek_last_error = NULL
            WHERE id = ?
        """, (now, article_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Database updated successfully")
        print(f"  - Inserted response record (article_id={article_id})")
        print(f"  - Updated articles table (deepseek_processed=1)")
        
        # Move response file to website/article_response
        return move_response_file(article_id, response_file)
        
    except Exception as e:
        print(f"ERROR: Database update failed: {e}")
        return False


def move_response_file(article_id, response_file):
    """Move response file to website/article_response directory."""
    try:
        source_path = Path(response_file)
        
        # Check if source file exists
        if not source_path.exists():
            print(f"ERROR: Response file not found: {response_file}")
            return False
        
        # Create destination filename
        dest_filename = f"article_{article_id}_response.json"
        dest_path = Path(WEBSITE_RESPONSE_DIR) / dest_filename
        
        # Handle duplicate files (shouldn't happen, but be safe)
        if dest_path.exists():
            # Add timestamp to make unique
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_filename = f"article_{article_id}_response_{timestamp}.json"
            dest_path = Path(WEBSITE_RESPONSE_DIR) / dest_filename
            print(f"  ⚠ Duplicate filename, using: {dest_filename}")
        
        # Move file
        shutil.move(str(source_path), str(dest_path))
        
        print(f"✓ Response file moved")
        print(f"  - From: {response_file}")
        print(f"  - To: {dest_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to move response file: {e}")
        return False


def update_on_failure(article_id, error_message):
    """Update database when processing fails."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update articles table only
        cursor.execute("""
            UPDATE articles
            SET deepseek_processed = 0,
                deepseek_failed = deepseek_failed + 1,
                deepseek_last_error = ?
            WHERE id = ?
        """, (error_message, article_id))
        
        conn.commit()
        conn.close()
        
        print(f"✗ Error recorded in database")
        print(f"  - Incremented failure count")
        print(f"  - Stored error message: {error_message[:100]}")
        return True
        
    except Exception as e:
        print(f"ERROR: Database update failed: {e}")
        return False


def validate_response_file(response_file):
    """Validate response JSON file exists and is valid."""
    try:
        if not Path(response_file).exists():
            return False, f"File not found: {response_file}"
        
        with open(response_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic structure validation
        if 'meta' not in data or 'article_id' not in data.get('meta', {}):
            return False, "Invalid JSON structure: missing meta.article_id"
        
        if 'article_analysis' not in data:
            return False, "Invalid JSON structure: missing article_analysis"
        
        return True, "Valid"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python3 insert_from_response.py <article_id> <response_file> [--error <error_message>]")
        print()
        print("Examples:")
        print("  Success: python3 insert_from_response.py 1 deepseek/responses/article_1_response.json")
        print("  Failure: python3 insert_from_response.py 4 '' --error 'JSON parse error'")
        sys.exit(1)
    
    article_id = sys.argv[1]
    response_file = sys.argv[2]
    
    # Check if error flag is present
    is_error = len(sys.argv) > 3 and sys.argv[3] == '--error'
    
    print(f"\n{'='*70}")
    print(f"Updating Database for Article {article_id}")
    print(f"{'='*70}\n")
    
    if is_error:
        # Error case
        error_message = sys.argv[4] if len(sys.argv) > 4 else "Unknown error"
        print(f"Processing Status: FAILED")
        print(f"Error: {error_message}\n")
        
        success = update_on_failure(article_id, error_message)
        
    else:
        # Success case
        print(f"Processing Status: SUCCESSFUL")
        print(f"Response File: {response_file}\n")
        
        # Validate response file
        is_valid, validation_msg = validate_response_file(response_file)
        if not is_valid:
            print(f"ERROR: {validation_msg}")
            print(f"Database NOT updated (invalid response file)\n")
            sys.exit(1)
        
        print(f"Response File: {validation_msg}\n")
        
        success = update_on_success(article_id, response_file)
    
    print(f"\n{'='*70}\n")
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
