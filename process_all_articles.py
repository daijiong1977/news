#!/usr/bin/env python3
"""
Batch process all articles with Deepseek API and populate target tables
"""

import subprocess
import sys
import os
import time

# Set API key
DEEPSEEK_API_KEY = "sk-dd996c4863a04d3ebad13c7ee52ca31b"

def process_article(article_id):
    """Process a single article"""
    print(f"\n{'='*60}")
    print(f"Processing Article {article_id}...")
    print(f"{'='*60}")
    
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
    
    result = subprocess.run(
        ["python3", "process_single_article.py", str(article_id)],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Article {article_id} processed successfully")
        return True
    else:
        print(f"❌ Article {article_id} failed:")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    print("🚀 Starting batch processing of all 20 articles...")
    print(f"Total to process: 20 articles")
    
    # Get current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    successful = 0
    failed = 0
    
    for article_id in range(1, 21):
        if process_article(article_id):
            successful += 1
        else:
            failed += 1
        
        # Small delay between API calls
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        print("\n⚠️ Migration note: `deepseek_feedback` is deprecated. If you need to migrate legacy rows, run populate_all_summary_tables.py manually (it's migration-only).")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
