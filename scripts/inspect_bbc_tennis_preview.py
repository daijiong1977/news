#!/usr/bin/env python3
"""Report content lengths for BBC Tennis entries in preview_articles.html"""
from bs4 import BeautifulSoup
import os
p = 'preview_articles.html'
if not os.path.exists(p):
    print('preview_articles.html not found')
    raise SystemExit(1)
with open(p, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

results = []
for div in soup.select('div.article'):
    # title
    h2 = div.find('h2')
    title = h2.get_text().strip() if h2 else ''
    em = div.find('em')
    src = None
    url = None
    if em:
        txt = em.get_text()
        # em contains "Source - Original" link
        a = em.find('a')
        if a and a.get('href'):
            url = a.get('href')
        # source is the text before the hyphen
        src_text = em.get_text()
        if ' - ' in src_text:
            src = src_text.split(' - ')[0].strip()
        else:
            parts = src_text.split(':')
            src = parts[0].strip()
    content_paras = [p.get_text().strip() for p in div.find_all('p')]
    # Remove the leading em paragraph and image caption if present
    # Reconstruct content as paragraphs after the em and optional img
    # Find index of em in p list
    content_text = '\n\n'.join(content_paras[1:]) if len(content_paras) > 1 else ''
    results.append({'title': title, 'source': src, 'url': url, 'content_len': len(content_text), 'content_preview': content_text[:200]})

for r in results:
    if r['source'] and 'BBC Tennis' in r['source']:
        print(r['title'])
        print('  URL:', r['url'])
        print('  content_len:', r['content_len'])
        print('  preview:', r['content_preview'].replace('\n',' '))
        print()
