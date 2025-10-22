#!/usr/bin/env python3
"""
run_mining_cycle.py

Sample 1-in-N unprocessed articles per source (N from config/thresholds.json), run Deepseek preview
and optionally insert normalized results using the existing inserter.

Usage:
  python3 run_mining_cycle.py         # dry-run (saves placeholder previews)
  python3 run_mining_cycle.py --apply # perform API calls and run inserter (requires DEEPSEEK_API_KEY)

This script purposely keeps DB operations isolated and calls `insert_from_response.py` as a subprocess
to avoid module-level DB conflicts.
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime
import argparse

THRESHOLDS_PATH = os.path.join('config', 'thresholds.json') if os.path.isdir('config') else 'config/thresholds.json'
DB_PATH = os.path.join(os.getcwd(), 'articles.db')


def load_thresholds():
    with open(THRESHOLDS_PATH, 'r') as f:
        return json.load(f)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_unprocessed_by_source(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, source FROM articles WHERE deepseek_processed = 0 AND (deepseek_failed IS NULL OR deepseek_failed < 4)")
    rows = cur.fetchall()
    by_source = {}
    for aid, src in rows:
        by_source.setdefault(src, []).append(aid)
    return by_source


def ensure_article_columns(conn):
    """Ensure `articles` table has the deepseek_* columns we rely on.
    Adds columns if they are missing (safe ALTER TABLE ADD COLUMN operations).
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(articles)")
    cols = [r[1] for r in cur.fetchall()]
    added = False
    if 'deepseek_failed' not in cols:
        cur.execute("ALTER TABLE articles ADD COLUMN deepseek_failed INTEGER DEFAULT 0")
        added = True
    if 'deepseek_last_error' not in cols:
        cur.execute("ALTER TABLE articles ADD COLUMN deepseek_last_error TEXT")
        added = True
    if 'deepseek_in_progress' not in cols:
        cur.execute("ALTER TABLE articles ADD COLUMN deepseek_in_progress INTEGER DEFAULT 0")
        added = True
    if 'deepseek_processed' not in cols:
        cur.execute("ALTER TABLE articles ADD COLUMN deepseek_processed INTEGER DEFAULT 0")
        added = True
    if added:
        conn.commit()
        print("Added missing deepseek_* columns to articles table")


def claim_article(conn, article_id):
    cur = conn.cursor()
    cur.execute("UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND (deepseek_in_progress IS NULL OR deepseek_in_progress = 0)", (article_id,))
    conn.commit()
    return cur.rowcount == 1


def release_claim(conn, article_id):
    cur = conn.cursor()
    cur.execute("UPDATE articles SET deepseek_in_progress = 0 WHERE id = ?", (article_id,))
    conn.commit()


def fetch_article_row(conn, article_id):
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, content, category_id FROM articles WHERE id = ?", (article_id,))
    r = cur.fetchone()
    if not r:
        return None
    return {'id': r[0], 'title': r[1], 'description': r[2], 'content': r[3], 'category_id': r[4]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Call API and run inserter after preview')
    args = parser.parse_args()

    thresholds = load_thresholds()
    sample_rate = int(thresholds.get('sample_rate', thresholds.get('num_per_source', 10)))
    seed = int(thresholds.get('random_seed', 42))
    responses_dir = thresholds.get('responses_dir', './responses')

    ensure_dir(responses_dir)
    random.seed(seed)

    if args.apply and not os.environ.get('DEEPSEEK_API_KEY'):
        print("ERROR: DEEPSEEK_API_KEY not set. Set it with: export DEEPSEEK_API_KEY=your_key_here")
        sys.exit(1)

    # First, run the article collector to populate `articles` table
    try:
        import data_collector
        # Use configured num_per_source (default comes from thresholds.json)
        num_per_source = thresholds.get('num_per_source', 1)
        print(f"Running collector to fetch up to {num_per_source} article(s) per source (sample_rate={sample_rate})...")
        data_collector.collect_articles(num_per_source=num_per_source)
    except Exception as e:
        print(f"Warning: collector failed or unavailable: {e}")

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_article_columns(conn)
        by_source = get_unprocessed_by_source(conn)
        print(f"Found {len(by_source)} sources with unprocessed articles")

        to_process = []
        for src, aids in by_source.items():
            selected = [aid for aid in aids if random.randrange(sample_rate) == 0]
            if selected:
                print(f"Source '{src}': selected {len(selected)} of {len(aids)} articles")
                to_process.extend(selected)

        print(f"Total selected: {len(to_process)}")

        # Import process_one_article only when we will call the API
        if args.apply:
            import process_one_article
            process_func = process_one_article.process_article_with_api
        else:
            process_func = None

        for aid in to_process:
            print(f"\n--- Article {aid} ---")
            if not claim_article(conn, aid):
                print(f"Could not claim {aid}; skipping")
                continue

            article = fetch_article_row(conn, aid)
            if not article:
                print(f"Article {aid} not found; releasing claim")
                release_claim(conn, aid)
                continue

            if args.apply:
                resp = process_func(article, process_one_article.COMPACT_PROMPTS['default'])
                if resp is None:
                    print(f"API processing failed for {aid}; incrementing failure and releasing claim")
                    cur = conn.cursor()
                    cur.execute("UPDATE articles SET deepseek_failed = COALESCE(deepseek_failed, 0) + 1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?", ("process_failed", aid))
                    conn.commit()
                    continue

                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{aid}_{ts}.json'
                fpath = os.path.join(responses_dir, fname)
                with open(fpath, 'w') as f:
                    json.dump(resp, f, ensure_ascii=False, indent=2)
                print(f"Saved preview to {fpath}")

                # Run inserter as subprocess
                print(f"Running inserter for {aid}")
                code = os.system(f'python3 insert_from_response.py "{fpath}"')
                if code != 0:
                    print(f"Inserter failed for {aid}: {code}")
                else:
                    print(f"Inserter succeeded for {aid}")
            else:
                # Dry-run: write a placeholder preview and release claim
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{aid}_{ts}.json'
                fpath = os.path.join(responses_dir, fname)
                placeholder = {'meta': {'article_id': aid, 'dry_run': True, 'selected_at': ts}}
                with open(fpath, 'w') as f:
                    json.dump(placeholder, f, ensure_ascii=False, indent=2)
                print(f"Dry-run saved placeholder to {fpath}")
                release_claim(conn, aid)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
