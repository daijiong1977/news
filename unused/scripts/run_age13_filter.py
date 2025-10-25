#!/usr/bin/env python3
"""Run age-13 banned-word filter for enabled BBC Entertainment feed and generate a report.

Produces a timestamped HTML showing accepted and dropped articles and prints a summary.
"""
import sqlite3
import os
import re
import html as _html
from datetime import datetime
from data_collector import parse_rss_feed, clean_paragraphs, download_image_preview

BASE=os.path.dirname(os.path.dirname(__file__))
CFG=os.path.join(BASE,'mining','age13_banned.txt')
DB=os.path.join(BASE,'articles.db')

# load banned words
words=[]
with open(CFG,encoding='utf-8') as f:
    for ln in f:
        ln=ln.strip()
        if not ln or ln.startswith('#'):
            continue
        # remove optional surrounding quotes
        if ln.startswith('"') and ln.endswith('"'):
            ln=ln[1:-1]
        words.append(ln.lower())

# compile pattern (word-boundary aware)
pat=re.compile(r'(?i)(?<!\w)(' + '|'.join(re.escape(w) for w in words) + r')(?!\w)')

# find enabled BBC Entertainment feed from DB
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("SELECT feed_url, feed_name FROM feeds WHERE enable=1 AND (feed_url LIKE '%entertainment%' OR feed_name LIKE '%Entertainment%')")
row=cur.fetchone()
if not row:
    print('No enabled Entertainment feed found')
    raise SystemExit(1)
feed_url, feed_name = row
print('Testing feed:', feed_name, feed_url)

articles = parse_rss_feed(feed_url, feed_name, None, max_articles=20)
accepted=[]
dropped=[]
min_image_bytes=70000
for art in articles:
    title=art.get('title','')
    paras=(art.get('content') or '').split('\n')
    cleaned=clean_paragraphs(paras)
    if not cleaned:
        # treat as dropped if no content
        dropped.append((art,'no content'))
        continue
    combined = title + '\n\n' + '\n\n'.join(cleaned)
    if pat.search(combined):
        dropped.append((art,'matched banned word'))
        continue
    # try to download preview image to mimic preview acceptance
    try:
        import requests
        resp = requests.get(art['url'], timeout=10)
        resp.raise_for_status()
        img_local = download_image_preview(art['url'], resp.text, min_bytes=min_image_bytes)
        if not img_local:
            dropped.append((art,'no large image'))
            continue
        accepted.append({'art':art,'content':'\n\n'.join(cleaned),'image':img_local})
    except Exception as e:
        dropped.append((art,f'error:{e}'))

# generate HTML report
out=['<!doctype html>','<html><head><meta charset="utf-8"><title>Entertainment Age13 Filter Report</title>',
     '<style>body{font-family:Arial,Helvetica,sans-serif;line-height:1.45;margin:20px} .article{margin-bottom:50px} img{max-width:700px;height:auto} .dropped{color:#900}</style>','</head><body>']
out.append(f"<h1>Entertainment Age13 Filter Report - {datetime.now().isoformat()}</h1>")
out.append(f"<h2>Feed: {_html.escape(feed_name)} - {_html.escape(feed_url)}</h2>")
out.append(f"<h3>Accepted ({len(accepted)})</h3>")
for a in accepted:
    art=a['art']
    out.append("<div class='article'>")
    out.append(f"<h4>{_html.escape(art.get('title',''))}</h4>")
    out.append(f"<p><em><a href='{_html.escape(art.get('url',''))}'>Original</a></em></p>")
    if a['image'] and os.path.exists(a['image']):
        out.append(f"<p><img src='{_html.escape(a['image'])}'></p>")
    for p in a['content'].split('\n\n'):
        out.append(f"<p>{_html.escape(p)}</p>")
    out.append('</div>')

out.append(f"<h3 class='dropped'>Dropped ({len(dropped)})</h3>")
for art,reason in dropped:
    out.append("<div class='article dropped'>")
    out.append(f"<h4>{_html.escape(art.get('title',''))}</h4>")
    out.append(f"<p><em><a href='{_html.escape(art.get('url',''))}'>Original</a> - {_html.escape(reason)}</em></p>")
    out.append('</div>')

out.append('</body></html>')
fn=f"entertainment_age13_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
with open(fn,'w',encoding='utf-8') as f:
    f.write('\n'.join(out))

print('Wrote',fn)
print('Accepted:',len(accepted),'Dropped:',len(dropped))
conn.close()
