#!/usr/bin/env python3
"""
sync_feeds_from_config.py

Reconcile `config.json` rss_sources[].enabled with the `feeds` table in `articles.db`.

Usage:
  python3 sync_feeds_from_config.py        # dry-run: shows proposed updates
  python3 sync_feeds_from_config.py --apply # apply changes to DB

The script is safe to run repeatedly. It will only update rows where the `enable` value differs.
"""

import os
import json
import sqlite3
import argparse

DB_PATH = os.path.join(os.getcwd(), 'articles.db')
CONFIG_PATH = os.path.join(os.getcwd(), 'config.json')


def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def map_config_enabled(cfg):
    # Expect config to have rss_sources: [{"name": ..., "enabled": true}, ...]
    mapping = {}
    for item in cfg.get('rss_sources', []):
        name = item.get('name') or item.get('feed_name') or item.get('title')
        if not name:
            continue
        enabled = bool(item.get('enabled', True))
        mapping[name] = enabled
    return mapping


def read_db_feeds(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, feed_name, enable FROM feeds')
    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes to DB')
    args = parser.parse_args()

    if not os.path.exists(CONFIG_PATH):
        print(f"Config not found at {CONFIG_PATH}")
        return

    cfg = load_config()
    mapping = map_config_enabled(cfg)

    conn = sqlite3.connect(DB_PATH)
    try:
        feeds = read_db_feeds(conn)
        to_update = []
        for fid, name, enable in feeds:
            # Try exact match on feed_name
            if name in mapping:
                desired = 1 if mapping[name] else 0
                if desired != enable:
                    to_update.append((fid, name, enable, desired))

        if not to_update:
            print('No feed enablement differences found. DB matches config.')
            return

        print('Proposed updates:')
        for fid, name, old, new in to_update:
            print(f"  id={fid} name='{name}' enable: {old} -> {new}")

        if args.apply:
            cur = conn.cursor()
            for fid, name, old, new in to_update:
                cur.execute('UPDATE feeds SET enable = ? WHERE id = ?', (new, fid))
            conn.commit()
            print(f"Applied {len(to_update)} updates to feeds table")
        else:
            print('\nDry-run mode; rerun with --apply to make these changes')

    finally:
        conn.close()


if __name__ == '__main__':
    main()
