#!/usr/bin/env python3
"""
Complete pipeline: Crawl → Download Images → Process with Deepseek → Populate Tables
"""

import subprocess
import sys
import os
import json

DEEPSEEK_API_KEY = "sk-dd996c4863a04d3ebad13c7ee52ca31b"

def run_command(description, command, env=None):
    """Run a command and report status"""
    print(f"\n{'='*70}")
    print(f"📍 {description}")
    print(f"{'='*70}")
    
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    result = subprocess.run(command, shell=True, env=run_env)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False

def count_articles():
    """Count articles in database"""
    import sqlite3
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM articles')
    count = c.fetchone()[0]
    conn.close()
    return count

def count_processed():
    """Count processed articles"""
    import sqlite3
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM deepseek_feedback')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_unprocessed_articles():
    """Get list of unprocessed article IDs"""
    import sqlite3
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('''
        SELECT id FROM articles 
        WHERE deepseek_processed = 0
        ORDER BY id
    ''')
    articles = [row[0] for row in c.fetchall()]
    conn.close()
    return articles

def main():
    os.chdir('/Users/jidai/news')
    
    print("\n" + "="*70)
    print("🚀 COMPLETE PIPELINE: CRAWL → IMAGES → DEEPSEEK → POPULATE")
    print("="*70)
    
    # Step 1: Crawl articles
    if not run_command(
        "Step 1/4: Crawling fresh articles",
        "python3 data_collector.py"
    ):
        print("❌ Crawling failed. Aborting pipeline.")
        return 1
    
    article_count = count_articles()
    print(f"📊 Articles crawled: {article_count}")
    
    # Step 2: Download images
    if not run_command(
        "Step 2/4: Downloading article images",
        "python3 download_article_images.py"
    ):
        print("⚠️  Image download had issues, but continuing...")
    
    # Step 3: Process with Deepseek (one at a time)
    unprocessed = get_unprocessed_articles()
    print(f"\n{'='*70}")
    print(f"Step 3/4: Processing {len(unprocessed)} articles with Deepseek")
    print(f"{'='*70}")
    
    env_deepseek = {"DEEPSEEK_API_KEY": DEEPSEEK_API_KEY}
    
    for i, article_id in enumerate(unprocessed, 1):
        print(f"\n📄 Processing article {article_id} ({i}/{len(unprocessed)})")
        result = subprocess.run(
            f"python3 process_single_article.py {article_id}",
            shell=True,
            env={**os.environ, **env_deepseek},
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ Article {article_id} processed")
        else:
            print(f"  ❌ Article {article_id} failed")
            if "error" in result.stderr.lower():
                print(f"  Error: {result.stderr[:200]}")
    
    processed = count_processed()
    print(f"\n📊 Articles processed with Deepseek: {processed}/{article_count}")
    
    # Step 4: Populate target tables
    if processed > 0:
        if run_command(
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
    sys.exit(main())
