#!/usr/bin/env python3
"""Generate a simple HTML page with four blocks: Hard, Mid, Easy, ZH (Chinese hard summary).

Usage: python3 generate_four_blocks.py [article_id]
"""

import sqlite3
import sys
import html
from pathlib import Path

DB = 'articles.db'

LEVEL_MAP = {'hard':3, 'mid':2, 'easy':1}

def fetch_summary(conn, article_id, difficulty_id, language_id=1):
    cur = conn.cursor()
    cur.execute(
        "SELECT title, summary FROM article_summaries WHERE article_id=? AND difficulty_id=? AND language_id=? ORDER BY id DESC LIMIT 1",
        (article_id, difficulty_id, language_id)
    )
    r = cur.fetchone()
    return dict(r) if r else None

def fetch_keywords(conn, article_id, difficulty_id):
    cur = conn.cursor()
    cur.execute("SELECT word, explanation FROM keywords WHERE article_id=? AND difficulty_id=?", (article_id, difficulty_id))
    return [dict(r) for r in cur.fetchall()]

def fetch_background(conn, article_id, difficulty_id):
    cur = conn.cursor()
    cur.execute("SELECT background_text FROM background_read WHERE article_id=? AND difficulty_id=? ORDER BY background_read_id", (article_id, difficulty_id))
    rows = [r[0] for r in cur.fetchall()]
    return "\n\n".join(rows) if rows else None

def fetch_questions(conn, article_id, difficulty_id):
    cur = conn.cursor()
    cur.execute("SELECT question_id, question_text FROM questions WHERE article_id=? AND difficulty_id=? ORDER BY question_id", (article_id, difficulty_id))
    questions = []
    for qid, qtext in cur.fetchall():
        cur.execute("SELECT choice_text, is_correct FROM choices WHERE question_id=? ORDER BY choice_id", (qid,))
        opts = [{'text':r[0], 'is_correct': bool(r[1])} for r in cur.fetchall()]
        questions.append({'id': qid, 'question': qtext, 'options': opts})
    return questions

def fetch_article_meta(conn, article_id):
    cur = conn.cursor()
    cur.execute("SELECT id, title, zh_title FROM articles WHERE id=?", (article_id,))
    r = cur.fetchone()
    return dict(r) if r else None

def build_block(title, summary, keywords, background, questions):
    s = '<div class="block">'
    s += f'<h2>{html.escape(title or "")}</h2>'
    if summary:
        s += f'<p class="summary">{html.escape(summary)}</p>'
    if keywords:
        s += '<div class="keywords"><h4>Keywords</h4><ul>'
        for kw in keywords:
            s += f'<li><strong>{html.escape(kw.get("word",""))}</strong>: {html.escape(kw.get("explanation",""))}</li>'
        s += '</ul></div>'
    if background:
        s += f'<div class="background"><h4>Background</h4><p>{html.escape(background)}</p></div>'
    if questions:
        s += '<div class="questions"><h4>Questions</h4>'
        for i,q in enumerate(questions,1):
            s += f'<div class="q"><div class="qtext">{i}. {html.escape(q.get("question",""))}</div><ul>'
            for opt in q.get('options',[]):
                mark = ' ✓' if opt.get('is_correct') else ''
                s += f'<li>{html.escape(opt.get("text",""))}{mark}</li>'
            s += '</ul></div>'
        s += '</div>'
    s += '</div>'
    return s

def main():
    aid = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    meta = fetch_article_meta(conn, aid)
    if not meta:
        print('Article not found', aid)
        return

    blocks = []
    # Hard, Mid, Easy (English)
    for level in ['hard','mid','easy']:
        did = LEVEL_MAP[level]
        summ = fetch_summary(conn, aid, did, language_id=1)
        keywords = fetch_keywords(conn, aid, did)
        background = fetch_background(conn, aid, did)
        questions = fetch_questions(conn, aid, did)
        title = summ.get('title') if summ and summ.get('title') else f"{meta.get('title')} ({level.title()})"
        summary_text = summ.get('summary') if summ else None
        blocks.append((level.title(), build_block(title, summary_text, keywords, background, questions)))

    # ZH block: Chinese summary for hard level
    zh_summ = fetch_summary(conn, aid, LEVEL_MAP['hard'], language_id=2)
    zh_title = zh_summ.get('title') if zh_summ and zh_summ.get('title') else meta.get('zh_title')
    zh_summary = zh_summ.get('summary') if zh_summ else None
    zh_keywords = fetch_keywords(conn, aid, LEVEL_MAP['hard'])
    zh_background = fetch_background(conn, aid, LEVEL_MAP['hard'])
    zh_questions = fetch_questions(conn, aid, LEVEL_MAP['hard'])
    blocks.append(('ZH', build_block(zh_title or meta.get('title'), zh_summary, zh_keywords, zh_background, zh_questions)))
    # Compose HTML
    # Build HTML by concatenation to avoid f-string brace escaping issues
    head = '<!doctype html>\n<html>\n<head>\n  <meta charset="utf-8">\n'
    head += '  <title>' + html.escape(meta.get('title','Article')) + ' - 4 Blocks</title>\n'
    head += '  <style>\n'
    head += "    body{font-family: Arial,Helvetica,sans-serif; padding:20px; background:#f6f9fc}\n"
    head += "    .container{max-width:1000px;margin:0 auto;display:grid;grid-template-columns:1fr;gap:18px}\n"
    head += "    .block{background:white;padding:18px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}\n"
    head += "    .summary{color:#333;margin:10px 0}\n"
    head += "    .keywords ul, .questions ul{margin-left:18px}\n"
    head += "    .qtext{font-weight:600}\n"
    head += '  </style>\n</head>\n<body>\n'

    body = '  <div class="container">\n'
    body += '    <h1>' + html.escape(meta.get('title','')) + '</h1>\n'
    body += '    <h3>4 Blocks: Hard / Mid / Easy / ZH</h3>\n'
    body += ''.join(b for _label,b in blocks)
    body += '\n  </div>\n'
    html_doc = head + body + '</body>\n</html>\n'

    out = Path.cwd() / f"article_{aid}_4blocks.html"
    out.write_text(html_doc, encoding='utf8')
    print('WROTE', out)
    conn.close()

if __name__ == '__main__':
    main()
