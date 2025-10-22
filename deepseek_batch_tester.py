#!/usr/bin/env python3
"""Batch tester: for each source, process up to N articles and generate combined HTML with ZH info.

Usage:
  python3 deepseek_batch_tester.py --per-source 10 --response-dir ./responses --dry-run
  python3 deepseek_batch_tester.py --per-source 10 --response-dir ./responses --apply

"""

import argparse
import sqlite3
import os
import glob
import subprocess
from pathlib import Path
from datetime import datetime

DB = 'articles.db'
RESP_DIR = 'responses'
OUT_HTML = 'deepseek_test_results.html'

def get_sources():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT DISTINCT source FROM articles')
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def select_articles(source, limit):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id FROM articles WHERE source=? AND deepseek_processed=0 AND deepseek_failed<3 AND (deepseek_in_progress=0 OR deepseek_in_progress IS NULL) ORDER BY id LIMIT ?', (source, limit))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def find_response_for(aid, response_dir):
    # Check provided dir then default responses/
    patterns = []
    if response_dir:
        patterns.append(os.path.join(response_dir, f'response_article_{aid}_*.json'))
    patterns.append(os.path.join(RESP_DIR, f'response_article_{aid}_*.json'))
    for p in patterns:
        files = glob.glob(p)
        if files:
            return files[0]
    return None

def run_inserter(response_file):
    cmd = ['python3', 'insert_from_response.py', response_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def gen_combined_html(article_ids, out_path=OUT_HTML):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    parts = []
    for aid in article_ids:
        c.execute('SELECT id, title, zh_title, pub_date, image_local, image_url, processed_at FROM articles WHERE id=?', (aid,))
        row = c.fetchone()
        if not row:
            continue
        title = row['title']
        zh_title = row['zh_title'] or ''
        date = row['pub_date'] or row['processed_at'] or ''
        image = row['image_local'] or row['image_url'] or ''

        # zh summary: prefer hard level language_id=2
        c.execute('SELECT summary FROM article_summaries WHERE article_id=? AND language_id=2 ORDER BY difficulty_id DESC LIMIT 1', (aid,))
        zh = c.fetchone()
        zh_summary = zh['summary'] if zh else ''

        block = f"<div class=\"art\">\n  <h2>{title}</h2>\n  <h3>{zh_title}</h3>\n"
        if image:
            block += f"  <img src=\"{image}\" alt=\"{title}\" style=\"max-width:200px;height:auto\">\n"
        block += f"  <div class=\"meta\">Date: {date} | Article ID: {aid}</div>\n"
        if zh_summary:
            block += f"  <p class=\"zh\">{zh_summary}</p>\n"
        # link to 4-block page
        fb = Path.cwd() / f"article_{aid}_4blocks.html"
        if fb.exists():
            block += f"  <a href=\"{fb.name}\">Open 4-block page</a>\n"
        block += "</div>\n"
        parts.append(block)

    conn.close()

    html = '<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>Deepseek Test Results</title><style>body{font-family:Arial;} .art{background:#fff;padding:16px;margin:12px;border-radius:8px;box-shadow:0 3px 8px rgba(0,0,0,.08)} .zh{color:#333}</style></head><body>\n'
    html += f'<h1>Deepseek Test Results - {datetime.now().isoformat()}</h1>\n'
    html += '\n'.join(parts)
    html += '\n</body></html>'

    Path(out_path).write_text(html, encoding='utf8')
    print('WROTE', out_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--per-source', type=int, default=10)
    p.add_argument('--response-dir', type=str, default=None)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()

    sources = get_sources()
    print('Sources found:', sources)
    all_processed = []

    for src in sources:
        print('\n-- Source:', src)
        aids = select_articles(src, args.per_source)
        print('Articles to process for source', src, aids)
        for aid in aids:
            resp = find_response_for(aid, args.response_dir)
            if not resp:
                print('  No response file for', aid, '- skipping')
                continue
            print('  Found response for', aid, resp)
            if args.dry_run:
                continue
            if args.apply:
                rc, out, err = run_inserter(resp)
                print('   Inserter rc=', rc)
                if rc != 0:
                    print('   Inserter error:', err)
                    continue
                # regenerate per-article 4-block page
                subprocess.run(['python3', 'generate_four_blocks.py', str(aid)])
                all_processed.append(aid)

    # Generate combined HTML for processed articles (or for all that already processed if dry-run)
    if args.dry_run:
        # produce for already-processed articles in DB
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('SELECT id FROM articles WHERE deepseek_processed=1')
        processed_ids = [r[0] for r in c.fetchall()]
        conn.close()
        gen_combined_html(processed_ids)
    else:
        gen_combined_html(all_processed if all_processed else [])

if __name__ == '__main__':
    main()
