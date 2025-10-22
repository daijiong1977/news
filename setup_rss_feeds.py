#!/usr/bin/env python3
"""
Create RSS feeds table and populate with feed URLs
"""

import sqlite3
import pathlib
import json
import sys

DB_FILE = pathlib.Path("articles.db")
CONFIG_FEEDS = pathlib.Path("config/feeds.json")

# Default embedded feed list (used if no config file present)
FEEDS = [
    ("US News", "https://feeds.nytimes.com/services/xml/rss/nyt/US.xml", "US News", True),
    ("Swimming", "https://www.swimmingworldmagazine.com/news/feed/", "Swimming", True),
    ("Technology", "https://feeds.arstechnica.com/arstechnica/index", "Technology", True),
    ("Science", "https://feeds.arstechnica.com/arstechnica/science", "Science", True),
    ("Politics", "https://feeds.nytimes.com/services/xml/rss/nyt/Politics.xml", "Politics", True),
    ("PBS", "https://www.pbs.org/newshour/feeds/rss/headlines", "PBS", True),
]

def load_feeds_from_config():
    """Load feeds from config/feeds.json if available.

    Returns a list of tuples: (name, url, category, enabled)
    """
    if not CONFIG_FEEDS.exists():
        print(f"i No config file at {CONFIG_FEEDS}, using embedded feed list")
        return FEEDS
    try:
        with CONFIG_FEEDS.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        feeds = []
        for item in doc.get("feeds", []):
            name = item.get("name") or item.get("url")
            url = item.get("url")
            category = item.get("category") or "Uncategorized"
            enabled = bool(item.get("enabled", True))
            feeds.append((name, url, category, enabled))
        print(f"i Loaded {len(feeds)} feeds from {CONFIG_FEEDS}")
        return feeds
    except Exception as e:
        print(f"! Failed to load {CONFIG_FEEDS}: {e}", file=sys.stderr)
        print("i Falling back to embedded feed list")
        return FEEDS

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Create rss_feeds table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS rss_feeds (
        feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_name TEXT NOT NULL UNIQUE,
        feed_url TEXT NOT NULL,
        category_name TEXT NOT NULL,
        active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Insert feeds (ignore if already exist)
FEEDS = load_feeds_from_config()

for name, url, category, active in FEEDS:
    try:
        cur.execute("""
            INSERT INTO rss_feeds (feed_name, feed_url, category_name, active)
            VALUES (?, ?, ?, ?)
        """, (name, url, category, active))
        print(f"✓ Added feed: {name}")
    except sqlite3.IntegrityError:
        print(f"⊘ Feed already exists: {name}")

conn.commit()

# Show all feeds
print("\n=== RSS Feeds Configuration ===")
cur.execute("SELECT feed_id, feed_name, feed_url, category_name, active FROM rss_feeds")
for feed_id, name, url, category, active in cur.fetchall():
    status = "✓ Active" if active else "✗ Inactive"
    print(f"[{feed_id}] {name:15} | {category:12} | {status}")
    print(f"    URL: {url}")

conn.close()
print("\n✓ Feeds table configured successfully")
