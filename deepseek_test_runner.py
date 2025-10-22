#!/usr/bin/env python3
"""Run an end-to-end testing flow for Deepseek on local DB.

Features:
- Simulate feeds (use existing unprocessed articles up to `--per-feed` limit)
- For each article: either use a provided response JSON (when --response-dir given) or skip API and mark preview step as complete by copying file to responses/
- Run canonical inserter (`insert_from_response.py`) per article
- Regenerate 4-block HTML for each processed article
- Verify normalized table counts and print a summary

Usage:
  python3 deepseek_test_runner.py --per-feed 10 --dry-run
  python3 deepseek_test_runner.py --per-feed 5 --response-dir ./responses --apply

"""

import argparse
import sqlite3
import os
import glob
import subprocess
from pathlib import Path

DB = 'articles.db'
RESP_DIR = 'responses'

def find_unprocessed(limit):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id FROM articles WHERE deepseek_processed=0 AND deepseek_failed<3 AND (deepseek_in_progress=0 OR deepseek_in_progress IS NULL) ORDER BY id LIMIT ?', (limit,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def run_inserter(response_file):
    cmd = ['python3', 'insert_from_response.py', response_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def regen_html(article_id):
    cmd = ['python3', 'generate_four_blocks.py', str(article_id)]
    subprocess.run(cmd)

def verify_article(article_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    q = {
        'summaries': 'SELECT COUNT(*) FROM article_summaries WHERE article_id=?',
        'questions': 'SELECT COUNT(*) FROM questions WHERE article_id=?',
        'choices': 'SELECT COUNT(*) FROM choices WHERE question_id IN (SELECT question_id FROM questions WHERE article_id=?)'
    }
    res = {}
    for k,ql in q.items():
        c.execute(ql, (article_id,))
        res[k] = c.fetchone()[0]
    c.execute('SELECT deepseek_processed, deepseek_in_progress, deepseek_failed FROM articles WHERE id=?', (article_id,))
    res['flags'] = c.fetchone()
    conn.close()
    return res

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--per-feed', type=int, default=10)
    p.add_argument('--response-dir', type=str, default=None)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()

    to_process = find_unprocessed(args.per_feed)
    if not to_process:
        print('No unprocessed articles found (matching selection).')
        return

    print('Articles to process:', to_process)

    os.makedirs(RESP_DIR, exist_ok=True)

    for aid in to_process:
        print('\n=== ARTICLE', aid, '===')
        # Find a response file in response-dir named response_article_<id>_*.json if provided
        response_file = None
        if args.response_dir:
            pat = os.path.join(args.response_dir, f'response_article_{aid}_*.json')
            files = glob.glob(pat)
            if files:
                response_file = files[0]
                print('Using provided response file:', response_file)

        if not response_file:
            # Check if there's already a response in RESP_DIR
            pat2 = os.path.join(RESP_DIR, f'response_article_{aid}_*.json')
            files2 = glob.glob(pat2)
            if files2:
                response_file = files2[0]

        if not response_file:
            print('No response JSON found for article', aid, '- skipping (dry preview required)')
            continue

        print('Would run inserter on', response_file)
        if args.dry_run:
            print('DRY RUN: Skipping actual insert')
            continue

        rc, out, err = run_inserter(response_file)
        print('Inserter rc=', rc)
        print(out)
        if rc != 0:
            print('Inserter error:', err)
            continue

        regen_html(aid)
        v = verify_article(aid)
        print('Verify:', v)

    print('\nDone')

if __name__ == '__main__':
    main()
