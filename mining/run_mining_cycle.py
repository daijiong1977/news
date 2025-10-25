#!/usr/bin/env python3
"""
run_mining_cycle.py

Collect articles from RSS feeds and populate the database.

Usage:
  python3 run_mining_cycle.py

This script:
1. Runs data_collector to fetch articles from RSS feeds
2. Stores them in the articles database
3. Deepseek processing is handled by a separate pipeline phase
"""

import os
import sys
import json

THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), 'thresholds.json')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'articles.db')


def load_thresholds():
    with open(THRESHOLDS_PATH, 'r') as f:
        return json.load(f)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    """
    Main entry point: collect articles from RSS feeds and store in database.
    All processing (including Deepseek) is handled by separate pipeline phases.
    """
    thresholds = load_thresholds()
    
    # Run the article collector to populate articles table
    try:
        import data_collector
        num_per_source = thresholds.get('num_per_source', 3)
        print(f"Collecting up to {num_per_source} article(s) per source...")
        data_collector.collect_articles(num_per_source=num_per_source)
        print("✓ Article collection complete")
    except Exception as e:
        print(f"✗ Collection failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
