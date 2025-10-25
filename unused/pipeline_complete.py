#!/usr/bin/env python3
"""
Complete pipeline: Crawl → Download Images → Process with Deepseek → Populate Tables
Processes all unprocessed articles dynamically
"""

import subprocess
import sqlite3
import os
from pathlib import Path

DEEPSEEK_API_KEY = "sk-dd996c4863a04d3ebad13c7ee52ca31b"
DB_PATH = '/var/www/news/articles.db'

def run_step(description, command):
    """Run a pipeline step"""
    print(f"\n{'='*70}")
    print(f"📍 {description}")
    print(f"{'='*70}")
    result = subprocess.run(command, shell=True)
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False

def get_unprocessed_articles():
    """Get list of unprocessed article IDs"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM articles WHERE deepseek_processed = 0 ORDER BY id')
    articles = [row[0] for row in c.fetchall()]
    conn.close()
    return articles

def main():
    os.chdir('/var/www/news')
    
    print("\n" + "="*70)
    print("🚀 COMPLETE PIPELINE - DYNAMIC ARTICLE PROCESSING")
    print("="*70)
    
    # Step 1: Crawl articles
    if not run_step(
        "Step 1/4: Crawling fresh articles",
        "python3 data_collector.py"
    ):
        print("❌ Crawling failed. Aborting pipeline.")
        return 1
    
    # Check how many articles were crawled
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM articles')
    total_articles = c.fetchone()[0]
    conn.close()
    
    print(f"\n📊 Total articles in database: {total_articles}")
    
    # Step 2: Download images
    if not run_step(
        "Step 2/4: Downloading article images",
        "python3 download_article_images.py"
    ):
        print("⚠️  Image download had issues, but continuing...")
    
    # Step 3: Process with Deepseek (all unprocessed articles)
    unprocessed = get_unprocessed_articles()
    print(f"\n{'='*70}")
    print(f"Step 3/4: Processing {len(unprocessed)} unprocessed articles with Deepseek")
    print(f"{'='*70}")
    
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
    
    successful = 0
    failed = 0
    
    for i, article_id in enumerate(unprocessed, 1):
        print(f"\n[{i}/{len(unprocessed)}] Processing article {article_id}...")
        result = subprocess.run(
            f"python3 process_single_article.py {article_id}",
            shell=True,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ Article {article_id} processed")
            successful += 1
        else:
            print(f"  ❌ Article {article_id} failed")
            failed += 1
            if result.stderr:
                print(f"  Error: {result.stderr[:100]}")
    
    print(f"\n{'='*70}")
    print(f"📊 Deepseek Processing Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"{'='*70}")
    
    # Step 4: Populate target tables
    if successful > 0:
        if run_step(
            "Step 4/4: Populating summary tables from Deepseek feedback",
            "python3 populate_all_summary_tables.py"
        ):
            print("\n" + "="*70)
            print("✅ PIPELINE COMPLETE!")
            print("="*70)
            return 0
    else:
        print("⚠️  No articles processed, skipping table population")
        return 1

if __name__ == "__main__":
    exit(main())
