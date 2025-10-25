#!/usr/bin/env python3
"""
Safely repopulate the `feeds` table from config/verified_feeds.dm.
Creates a timestamped backup of articles.db before making changes.
"""
import sqlite3
import pathlib
import shutil
import json
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / 'articles.db'
VERIFIED = ROOT / 'config' / 'verified_feeds.dm'
BACKUP_DIR = ROOT / 'backups'

if not VERIFIED.exists():
    print(f"Verified feeds config not found at {VERIFIED}")
    raise SystemExit(1)

# 1) Backup DB
#
# NOTE: This creates a local, timestamped backup in `backups/` before
# making any changes. Backups are intended for local recovery only and
# MUST NOT be committed to version control or pushed to remote hosts.
# See docs/GROUND_RULES.md for details.
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
backup_path = BACKUP_DIR / f'articles_db_backup_{stamp}.db'
shutil.copy2(DB, backup_path)
print(f"Created DB backup: {backup_path}")

# 2) Load verified feeds
with VERIFIED.open('r', encoding='utf-8') as f:
    vdoc = json.load(f)
feeds = [f for f in vdoc.get('feeds', []) if f.get('enabled', True)]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 3) Build category map (ensure categories exist)
category_map = {}
for feed in feeds:
    cat = feed.get('category') or 'Uncategorized'
    if cat in category_map:
        continue
    cur.execute('SELECT category_id FROM categories WHERE category_name = ?', (cat,))
    r = cur.fetchone()
    if r:
        category_map[cat] = r[0]
    else:
        now = datetime.now().isoformat()
        cur.execute('INSERT INTO categories (category_name, description, prompt_name, created_at) VALUES (?, ?, ?, ?)', (cat, f'{cat} (auto)', 'default', now))
        category_map[cat] = cur.lastrowid
        print(f"Created category: {cat} -> id {category_map[cat]}")

# 4) Clear feeds table
cur.execute('DELETE FROM feeds')
print('Cleared existing feeds table')

# 5) Insert feeds
now = datetime.now().isoformat()
for feed in feeds:
    name = feed.get('name') or feed.get('url')
    url = feed.get('url')
    cat = feed.get('category') or 'Uncategorized'
    cat_id = category_map[cat]
    cur.execute('INSERT INTO feeds (feed_name, feed_url, category_id, enable, created_at) VALUES (?, ?, ?, ?, ?)', (name, url, cat_id, 1, now))
    print(f"Inserted feed: {name} -> {cat} (id {cat_id})")

conn.commit()

# 6) Show final feeds
print('\nFinal feeds table:')
cur.execute('SELECT feed_id, feed_name, feed_url, category_id, enable FROM feeds ORDER BY feed_id')
for row in cur.fetchall():
    print(row)

conn.close()
print('\nDone')
