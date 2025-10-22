#!/usr/bin/env python3
"""Utility to prepare the articles DB for Deepseek testing.

Features:
- create a timestamped backup of articles.db
- reset deepseek flags for all articles or a selected set
- show counts of deepseek-related columns

Usage:
  python3 deepseek_testing_cleanup.py --backup
  python3 deepseek_testing_cleanup.py --reset-all --backup
  python3 deepseek_testing_cleanup.py --reset-ids 1 2 3
"""

import argparse
import sqlite3
import shutil
import os
import datetime

DB = 'articles.db'

def backup_db():
    backdir = 'backups'
    os.makedirs(backdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(backdir, f'articles.db.backup_{stamp}.sqlite')
    shutil.copy2(DB, dst)
    print('BACKUP CREATED:', dst)
    return dst

def reset_all_flags(conn):
    c = conn.cursor()
    c.execute('UPDATE articles SET deepseek_processed=0, deepseek_in_progress=0, deepseek_failed=0, processed_at=NULL')
    conn.commit()
    print('Reset deepseek flags for all articles')

def reset_ids(conn, ids):
    c = conn.cursor()
    q = 'UPDATE articles SET deepseek_processed=0, deepseek_in_progress=0, deepseek_failed=0, processed_at=NULL WHERE id IN ({})'.format(','.join('?' for _ in ids))
    c.execute(q, ids)
    conn.commit()
    print('Reset deepseek flags for article ids:', ids)

def show_counts(conn):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM articles')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1')
    processed = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_in_progress=1')
    inprog = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_failed>0')
    failed = c.fetchone()[0]
    print('Articles total:', total)
    print('Processed:', processed)
    print('In-progress:', inprog)
    print('Failed > 0:', failed)

def ensure_columns(conn):
    # Ensure expected columns exist (idempotent)
    c = conn.cursor()
    c.execute("PRAGMA table_info(articles)")
    cols = [r[1] for r in c.fetchall()]
    changed = False
    if 'deepseek_failed' not in cols:
        c.execute('ALTER TABLE articles ADD COLUMN deepseek_failed INTEGER DEFAULT 0')
        changed = True
    if 'deepseek_last_error' not in cols:
        c.execute("ALTER TABLE articles ADD COLUMN deepseek_last_error TEXT")
        changed = True
    if 'deepseek_in_progress' not in cols:
        c.execute('ALTER TABLE articles ADD COLUMN deepseek_in_progress INTEGER DEFAULT 0')
        changed = True
    if changed:
        conn.commit()
        print('Updated articles schema to include deepseek columns')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--backup', action='store_true')
    p.add_argument('--reset-all', action='store_true')
    p.add_argument('--reset-ids', nargs='*', type=int)
    p.add_argument('--show', action='store_true')
    args = p.parse_args()

    if not os.path.exists(DB):
        print('Database not found:', DB)
        return

    if args.backup:
        backup_db()

    conn = sqlite3.connect(DB)
    try:
        ensure_columns(conn)
        if args.reset_all:
            reset_all_flags(conn)
        if args.reset_ids:
            reset_ids(conn, args.reset_ids)
        if args.show or (not args.reset_all and not args.reset_ids and not args.backup):
            show_counts(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
