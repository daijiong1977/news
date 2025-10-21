#!/usr/bin/env python3
"""
Create RSS feeds table and populate with feed URLs
"""

import sqlite3
import pathlib

DB_FILE = pathlib.Path("articles.db")

# Feed data
FEEDS = [
    ("US News", "https://feeds.nytimes.com/services/xml/rss/nyt/US.xml", "US News", True),
    ("Swimming", "https://www.swimmingworldmagazine.com/feed/", "Swimming", True),
    ("Technology", "https://feeds.arstechnica.com/arstechnica/index", "Technology", True),
    ("Science", "https://feeds.arstechnica.com/arstechnica/science", "Science", True),
    ("Politics", "https://feeds.nytimes.com/services/xml/rss/nyt/Politics.xml", "Politics", True),
    ("PBS", "https://www.pbs.org/newshour/feeds/rss/headlines", "PBS", True),
]

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
