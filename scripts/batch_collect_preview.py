#!/usr/bin/env python3
"""Batch collect up to 3 clean articles per enabled feed and write a master review HTML.

Follows the preview rules: skip video/transcript, clean paragraphs, apply age-13 banned-word filter (config/age13_banned.txt), download preview image with min 70KB (trusted-host bypass), and collect up to 3 accepted articles per feed from top 20 items.

Backs up DB and article_images first, clears articles and article_images tables and removes existing image files.
Does NOT insert collected articles into the DB; writes a single HTML file for review and saves images under article_images/.
"""
import os
import shutil
import sqlite3
from datetime import datetime
import re
import html as _html

BASE=os.path.dirname(os.path.dirname(__file__))
DB=os.path.join(BASE,'articles.db')
IMG_DIR=os.path.join(BASE,'article_images')
BACKUP_DIR=os.path.join(BASE,'backups')
CFG=os.path.join(BASE,'config','age13_banned.txt')

# ensure dirs
os.makedirs(IMG_DIR,exist_ok=True)
os.makedirs(BACKUP_DIR,exist_ok=True)

# backup DB and images
ts=datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy(DB, os.path.join(BACKUP_DIR, f'articles.db.backup.{ts}'))
# copy images dir
shutil.copytree(IMG_DIR, os.path.join(BACKUP_DIR, f'article_images.backup.{ts}'), dirs_exist_ok=True)
print('Backed up DB and images to backups/')

# load age13 banned words
words=[]
if os.path.exists(CFG):
    with open(CFG,encoding='utf-8') as f:
        for ln in f:
            ln=ln.strip()
            if not ln or ln.startswith('#'):
                continue
            if ln.startswith('"') and ln.endswith('"'):
                ln=ln[1:-1]
            words.append(ln.lower())

pat=None
if words:
    pat=re.compile(r'(?i)(?<!\w)(' + '|'.join(re.escape(w) for w in words) + r')(?!\w)')

# helper imports from data_collector
import sys
sys.path.insert(0, BASE)
from data_collector import parse_rss_feed, clean_paragraphs, download_image_preview, is_video_article, is_transcript_article
import requests

# clear articles & article_images tables and remove images
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute('DELETE FROM article_images')
cur.execute('DELETE FROM articles')
conn.commit()
print('Cleared articles and article_images tables in DB')
# remove files in IMG_DIR
for fn in os.listdir(IMG_DIR):
    fp=os.path.join(IMG_DIR,fn)
    try:
        os.remove(fp)
    except Exception:
        pass
print('Removed existing image files')

# enable all feeds
cur.execute('UPDATE feeds SET enable=1')
conn.commit()
print('Enabled all feeds')

# gather enabled feeds
cur.execute('SELECT feed_id, feed_name, feed_url FROM feeds WHERE enable=1')
feeds=cur.fetchall()
print('Found',len(feeds),'enabled feeds')

master_items=[]

for feed_id, feed_name, feed_url in feeds:
    print('\nProcessing feed:',feed_name, feed_url)
    articles=parse_rss_feed(feed_url, feed_name, None, max_articles=20)
    kept=0
    for art in articles:
        if kept>=3:
            break
        # skip heuristics
        if is_video_article(art.get('title',''), art.get('description',''), art.get('url','')):
            continue
        if is_transcript_article(art.get('content',''), art.get('title','')):
            continue
        paras=(art.get('content') or '').split('\n')
        cleaned=clean_paragraphs(paras)
        if not cleaned:
            continue
        # age13 filter
        combined = art.get('title','') + '\n\n' + '\n\n'.join(cleaned)
        if pat and pat.search(combined):
            print('  Dropped (age13) ->', art.get('title','')[:80])
            continue
        # fetch page and download image
        try:
            resp = requests.get(art['url'], timeout=10)
            resp.raise_for_status()
            img_local = download_image_preview(art['url'], resp.text, min_bytes=70000)
            if not img_local:
                print('  Skipped (no large image) ->', art.get('title','')[:80])
                continue
            # accepted
            master_items.append({
                'title':art.get('title',''),
                'url':art.get('url',''),
                'source':feed_name,
                'pubDate':art.get('pubDate'),
                'image':img_local,
                'content':'\n\n'.join(cleaned)
            })
            kept+=1
            print('  Accepted ->', art.get('title','')[:80])
        except Exception as e:
            print('  ! error',e)
            continue

# write master HTML
out=['<!doctype html>','<html><head><meta charset="utf-8"><title>Batch Review</title>',
     '<style>body{font-family:Arial,Helvetica,sans-serif;line-height:1.45;margin:20px} .article{margin-bottom:60px} img{max-width:800px;height:auto}</style>','</head><body>']
out.append(f"<h1>Batch Review - {datetime.now().isoformat()}</h1>")
for it in master_items:
    out.append("<div class='article'>")
    out.append(f"<h2>{_html.escape(it['title'])}</h2>")
    out.append(f"<p><em>{_html.escape(it['source'])} - <a href='{_html.escape(it['url'])}'>Original</a> - {_html.escape(str(it.get('pubDate')))}</em></p>")
    if it['image'] and os.path.exists(it['image']):
        out.append(f"<p><img src='{_html.escape(it['image'])}'></p>")
    for p in it['content'].split('\n\n'):
        out.append(f"<p>{_html.escape(p)}</p>")
    out.append('</div>')

out.append('</body></html>')
fn=f"batch_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
with open(fn,'w',encoding='utf-8') as f:
    f.write('\n'.join(out))

print('\nWrote',fn,'with',len(master_items),'items')
conn.close()
