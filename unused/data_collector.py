#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Data Collector: Fetch exactly num_per_source articles per feed from RSS.Data Collector v2: Simplified, faster, more reliable.

Reads config from mining/thresholds.jsonFetches exactly num_per_source articles per feed.

""""""



import sqlite3import sqlite3

import requestsimport requests

import xml.etree.ElementTree as ETimport xml.etree.ElementTree as ET

from datetime import datetimefrom datetime import datetime

import jsonimport json

import pathlibimport pathlib



DB_FILE = pathlib.Path("articles.db")DB_FILE = pathlib.Path("articles.db")

THRESHOLDS_FILE = pathlib.Path("mining/thresholds.json")THRESHOLDS_FILE = pathlib.Path("mining/thresholds.json")





def get_feeds_from_db(conn):def get_feeds_from_db(conn):

    """Get enabled feeds from database"""    """Get enabled feeds from database"""

    cur = conn.cursor()    cur = conn.cursor()

    cur.execute(    cur.execute(

        "SELECT feed_id, feed_name, feed_url, category_id FROM feeds WHERE enable = 1 ORDER BY feed_name"        "SELECT feed_id, feed_name, feed_url, category_id FROM feeds WHERE enable = 1 ORDER BY feed_name"

    )    )

    return cur.fetchall()    return cur.fetchall()





def article_exists(conn, url):def article_exists(conn, url):

    """Check if article already exists by URL"""    """Check if article already exists by URL"""

    cur = conn.cursor()    cur = conn.cursor()

    cur.execute("SELECT id FROM articles WHERE url = ?", (url,))    cur.execute("SELECT id FROM articles WHERE url = ?", (url,))

    return cur.fetchone() is not None    return cur.fetchone() is not None





def insert_article(conn, title, source, url, description, content, pub_date, category_id):def insert_article(conn, title, source, url, description, content, pub_date, category_id):

    """Insert article into database"""    """Insert article into database"""

    cur = conn.cursor()    cur = conn.cursor()

    try:    try:

        cur.execute("""        cur.execute("""

            INSERT INTO articles             INSERT INTO articles 

            (title, source, url, description, content, pub_date, crawled_at, category_id)            (title, source, url, description, content, pub_date, crawled_at, category_id)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (        """, (

            title[:500] if title else "",            title[:500] if title else "",

            source[:100] if source else "",            source[:100] if source else "",

            url[:500] if url else "",            url[:500] if url else "",

            description[:1000] if description else "",            description[:1000] if description else "",

            content[:5000] if content else "",            content[:5000] if content else "",

            pub_date[:50] if pub_date else datetime.now().isoformat(),            pub_date[:50] if pub_date else datetime.now().isoformat(),

            datetime.now().isoformat(),            datetime.now().isoformat(),

            category_id            category_id

        ))        ))

        conn.commit()        conn.commit()

        return cur.lastrowid        return cur.lastrowid

    except sqlite3.IntegrityError:    except sqlite3.IntegrityError:

        return None        return None





def fetch_articles_from_feed(feed_url, max_count=10):def fetch_articles_from_feed(feed_url, max_count=10):

    """Fetch articles from RSS feed"""    """Fetch articles from RSS feed"""

    articles = []    articles = []

    try:    try:

        response = requests.get(feed_url, timeout=10)        response = requests.get(feed_url, timeout=10)

        response.raise_for_status()        response.raise_for_status()

        root = ET.fromstring(response.content)        root = ET.fromstring(response.content)

        items = root.findall('.//item')        items = root.findall('.//item')

                

        for item in items[:max_count]:        for item in items[:max_count]:

            try:            try:

                title_elem = item.find('title')                title_elem = item.find('title')

                link_elem = item.find('link')                link_elem = item.find('link')

                desc_elem = item.find('description')                desc_elem = item.find('description')

                pubDate_elem = item.find('pubDate')                pubDate_elem = item.find('pubDate')

                                

                title = title_elem.text if title_elem is not None else "No title"                title = title_elem.text if title_elem is not None else "No title"

                url = link_elem.text if link_elem is not None else ""                url = link_elem.text if link_elem is not None else ""

                description = desc_elem.text if desc_elem is not None else ""                description = desc_elem.text if desc_elem is not None else ""

                pub_date = pubDate_elem.text if pubDate_elem is not None else datetime.now().isoformat()                pub_date = pubDate_elem.text if pubDate_elem is not None else datetime.now().isoformat()

                                

                if url:                if url:

                    articles.append({                    articles.append({

                        'title': title,                        'title': title,

                        'url': url,                        'url': url,

                        'description': description,                        'description': description,

                        'pub_date': pub_date                        'pub_date': pub_date

                    })                    })

            except Exception:            except Exception:

                continue                continue

                

        return articles        return articles

    except Exception as e:    except Exception as e:

        print(f"    Error fetching: {e}")        print(f"    Error fetching: {e}")

        return []        return []





def collect_articles(num_per_source=2):def collect_articles(num_per_source=2):

    """Main collection function"""    """Main collection function"""

    conn = sqlite3.connect(DB_FILE)    conn = sqlite3.connect(DB_FILE)

        

    feeds = get_feeds_from_db(conn)    feeds = get_feeds_from_db(conn)

        

    if not feeds:    if not feeds:

        print("No enabled feeds found in database")        print("No enabled feeds found in database")

        return        return

        

    print(f"\nCollecting {num_per_source} articles from {len(feeds)} feeds...")    print(f"\nCollecting {num_per_source} articles from {len(feeds)} feeds...")

    print("=" * 60)    print("=" * 60)

        

    total_collected = 0    total_collected = 0

        

    for feed_id, feed_name, feed_url, category_id in feeds:    for feed_id, feed_name, feed_url, category_id in feeds:

        print(f"  {feed_name:<25}", end=" ", flush=True)        print(f"  {feed_name:<25}", end=" ", flush=True)

                

        # Fetch more than needed to have some to choose from        # Fetch more than needed to have some to choose from

        articles = fetch_articles_from_feed(feed_url, max_count=num_per_source * 3)        articles = fetch_articles_from_feed(feed_url, max_count=num_per_source * 3)

                

        if not articles:        if not articles:

            print("✗ No articles found")            print("✗ No articles found")

            continue            continue

                

        inserted = 0        inserted = 0

        # Take only num_per_source articles        # Take only num_per_source articles

        for article in articles[:num_per_source]:        for article in articles[:num_per_source]:

            if not article_exists(conn, article['url']):            if not article_exists(conn, article['url']):

                aid = insert_article(                aid = insert_article(

                    conn,                    conn,

                    article['title'],                    article['title'],

                    feed_name,                    feed_name,

                    article['url'],                    article['url'],

                    article['description'],                    article['description'],

                    article['description'][:1000],                    article['description'][:1000],

                    article['pub_date'],                    article['pub_date'],

                    category_id                    category_id

                )                )

                if aid:                if aid:

                    inserted += 1                    inserted += 1

                

        print(f"✓ {inserted} inserted")        print(f"✓ {inserted} inserted")

        total_collected += inserted        total_collected += inserted

        

    print("=" * 60)    print("=" * 60)

    print(f"Total collected: {total_collected} new articles\n")    print(f"Total collected: {total_collected} new articles\n")

        

    # Verify    # Verify

    cur = conn.cursor()    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM articles")    cur.execute("SELECT COUNT(*) FROM articles")

    total_in_db = cur.fetchone()[0]    total_in_db = cur.fetchone()[0]

    print(f"Database now has {total_in_db} total articles")    print(f"Database now has {total_in_db} total articles")

        

    conn.close()    conn.close()





if __name__ == '__main__':if __name__ == '__main__':

    # Load num_per_source from thresholds.json    # Load num_per_source from thresholds.json

    num_per_source = 2    num_per_source = 2  # default

    try:    try:

        if THRESHOLDS_FILE.exists():        if THRESHOLDS_FILE.exists():

            with open(THRESHOLDS_FILE) as f:            with open(THRESHOLDS_FILE) as f:

                thresholds = json.load(f)                thresholds = json.load(f)

                num_per_source = thresholds.get('num_per_source', 2)                num_per_source = thresholds.get('num_per_source', 2)

                print(f"Config: num_per_source={num_per_source}")                print(f"Config: num_per_source={num_per_source}")

    except Exception as e:    except Exception as e:

        print(f"Warning: Could not load config: {e}")        print(f"Warning: Could not load config: {e}")

        

    collect_articles(num_per_source=num_per_source)    collect_articles(num_per_source=num_per_source)

