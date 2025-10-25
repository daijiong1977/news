#!/usr/bin/env python3
"""Generate verify_articles.html showing image, title, pub_date, crawled_at and full content

Writes to verify_articles.html in the repo root.
"""
import sqlite3
import html
from datetime import datetime
import os

DB = os.path.join(os.path.dirname(__file__), '..', 'articles.db')
OUT = os.path.join(os.path.dirname(__file__), '..', 'verify_articles.html')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = '''
SELECT a.id, a.title, a.source, a.url, a.pub_date, a.crawled_at, a.content,
       ai.image_id, ai.article_id as img_article_id, ai.image_name, ai.original_url as image_original_url, ai.local_location
FROM articles a
LEFT JOIN article_images ai ON (a.image_id IS NOT NULL AND a.image_id = ai.image_id) OR (ai.article_id = a.id)
ORDER BY a.id
'''
rows = cur.execute(query).fetchall()

now = datetime.utcnow().isoformat() + 'Z'

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n')
    f.write('<meta name="viewport" content="width=device-width,initial-scale=1">\n')
    f.write(f'<title>Verification: Articles ({len(rows)})</title>\n')
    f.write('<style>body{font-family:Arial,Helvetica,sans-serif;margin:20px} .article{border:1px solid #ddd;padding:12px;margin:12px 0;border-radius:6px} img{max-width:320px;height:auto;border:1px solid #ccc;margin-right:12px} .meta{color:#444;font-size:0.9em;margin-bottom:6px} .title{font-weight:700;font-size:1.05em;margin-bottom:6px} .content{white-space:pre-wrap;background:#fafafa;padding:8px;border-radius:4px}</style>\n')
    f.write('</head>\n<body>\n')
    f.write(f'<h1>Verification: Articles ({len(rows)})</h1>\n')
    f.write(f'<p>Generated: {html.escape(now)}</p>\n')
    f.write('<p>Each item shows the recorded local image (if any), original image URL, title, source, pub_date, crawled_at, and the full content. Images are referenced by their stored local path.</p>\n')

    for r in rows:
        f.write('<div class="article">\n')
        # image block
        img_tag = ''
        if r['local_location']:
            # local_location may be absolute or relative; make it relative if under repo
            local = r['local_location']
            # if path exists on disk, use it; otherwise leave as text link
            if os.path.exists(os.path.join(os.path.dirname(__file__), '..', local)):
                src = local
            else:
                src = local
            img_tag = f'<a href="{html.escape(r["image_original_url"] or "#")}" target="_blank"><img src="{html.escape(src)}" alt="image for article {r["id"]}"></a>'
        elif r['image_original_url']:
            img_tag = f'<a href="{html.escape(r["image_original_url"])}" target="_blank">[original image]</a>'

        if img_tag:
            f.write('<div style="display:flex;align-items:flex-start">')
            f.write(img_tag)
            f.write('<div>')
        else:
            f.write('<div>')

        title = r['title'] or ''
        f.write(f'<div class="title">{html.escape(title)}</div>\n')
        f.write('<div class="meta">')
        f.write(f'Source: {html.escape(r["source"] or "")}')
        if r['url']:
            f.write(f' — <a href="{html.escape(r["url"])}" target="_blank">original link</a>')
        if r['pub_date']:
            f.write(f' — Published: {html.escape(r["pub_date"]) }')
        if r['crawled_at']:
            f.write(f' — Crawled: {html.escape(r["crawled_at"]) }')
        f.write('</div>\n')

        # image original URL shown if present
        if r['image_original_url'] and not r['local_location']:
            f.write(f'<div class="meta">Image original: <a href="{html.escape(r["image_original_url"])}" target="_blank">{html.escape(r["image_original_url"])}</a></div>\n')

        # content
        content = r['content'] or ''
        f.write(f'<div class="content">{html.escape(content)}</div>\n')

        if img_tag:
            f.write('</div></div>')
        f.write('\n</div>\n')

    f.write('</body>\n</html>')

print('Wrote', OUT)
conn.close()
