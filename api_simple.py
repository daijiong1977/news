#!/usr/bin/env python3
"""
Flask API for News App - Works with new schema
Articles only, with optional summaries when available
"""
import sqlite3
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)

DB_PATH = '/Users/jidai/news/articles.db'
IMAGES_DIR = Path('/Users/jidai/news/article_images')

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Get articles with optional difficulty/language filtering"""
    try:
        difficulty = request.args.get('difficulty', 'mid')
        language = request.args.get('language', 'en')
        limit = int(request.args.get('limit', 20))
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get difficulty_id and language_id from the lookup tables
        cursor.execute('SELECT difficulty_id FROM difficulty_levels WHERE difficulty = ?', (difficulty,))
        diff_result = cursor.fetchone()
        difficulty_id = diff_result['difficulty_id'] if diff_result else 2  # default to 'mid'
        
        cursor.execute('SELECT language_id FROM languages WHERE language = ?', (language,))
        lang_result = cursor.fetchone()
        language_id = lang_result['language_id'] if lang_result else 1  # default to 'en'
        
        # Get articles that have summaries for the requested difficulty/language
        # This ensures we only return articles that have been processed
        cursor.execute('''
            SELECT DISTINCT a.id, a.title, a.zh_title, a.description, a.source, a.pub_date, a.category_id, img.image_name
            FROM articles a
            LEFT JOIN article_summaries s ON a.id = s.article_id 
                AND s.difficulty_id = ? AND s.language_id = ?
            LEFT JOIN article_images img ON a.id = img.article_id
            ORDER BY a.pub_date DESC
            LIMIT ?
        ''', (difficulty_id, language_id, limit))
        
        articles = []
        for row in cursor.fetchall():
            article_data = {
                'id': row['id'],
                'title': row['title'],
                'zh_title': row['zh_title'] or row['title'],
                'description': row['description'],
                'source': row['source'],
                'pub_date': row['pub_date'],
                'category_id': row['category_id'],
                'image': None
            }
            
            # Add image if available
            if row['image_name']:
                article_data['image'] = f'/api/images/{row["image_name"]}'
            
            articles.append(article_data)
        
        conn.close()
        return jsonify(articles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    """Get article detail with summary if available"""
    try:
        difficulty = request.args.get('difficulty', 'mid')
        language = request.args.get('language', 'en')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get difficulty_id and language_id
        cursor.execute('SELECT difficulty_id FROM difficulty_levels WHERE difficulty = ?', (difficulty,))
        diff_result = cursor.fetchone()
        difficulty_id = diff_result['difficulty_id'] if diff_result else 2
        
        cursor.execute('SELECT language_id FROM languages WHERE language = ?', (language,))
        lang_result = cursor.fetchone()
        language_id = lang_result['language_id'] if lang_result else 1
        
        # Get article
        cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            return jsonify({'error': 'Article not found'}), 404
        
        article_dict = dict(article)
        
        # Get summary for this difficulty/language
        cursor.execute('''
            SELECT summary FROM article_summaries 
            WHERE article_id = ? AND difficulty_id = ? AND language_id = ?
        ''', (article_id, difficulty_id, language_id))
        
        summary_row = cursor.fetchone()
        summary = summary_row['summary'] if summary_row else ''
        
        conn.close()
        
        return jsonify({
            'article': article_dict,
            'summary': summary,
            'keywords': [],  # Empty until keywords table is populated
            'questions': [],  # Empty until questions are added
            'comments': [],
            'analysis': '',
            'perspectives': []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        articles_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM article_summaries')
        summaries_count = cursor.fetchone()[0]
        
        conn.close()
        return jsonify({
            'status': 'ok',
            'articles': articles_count,
            'summaries': summaries_count
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):
    """Serve article images"""
    try:
        filepath = IMAGES_DIR / filename
        if filepath.exists() and str(filepath).startswith(str(IMAGES_DIR)):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting News API Server...")
    print("📡 Listening on http://localhost:8000")
    print("📊 Database: articles.db")
    print(f"📸 Images directory: {IMAGES_DIR}")
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
