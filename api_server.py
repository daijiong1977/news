#!/usr/bin/env python3
"""
Simple Flask API server for the React frontend
Serves articles from SQLite database with filtering support
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database path
DB_PATH = '/Users/jidai/news/articles.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Get articles list with filtering"""
    try:
        difficulty = request.args.get('difficulty', 'mid')
        language = request.args.get('language', 'en')
        category = request.args.get('category', '')
        limit = request.args.get('limit', 20, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query - join with summaries to get difficulty level
        query = '''
            SELECT 
                a.id, a.title, a.zh_title, a.description, a.source, a.pub_date,
                a.category_id
            FROM articles a
            LEFT JOIN article_summaries s ON a.id = s.article_id
            WHERE 1=1
        '''
        params = []
        
        # Note: difficulty filtering is removed since it's per-summary, not per-article
        # We'll return all articles and let frontend filter if needed
        
        if category:
            query += ' AND a.category_id = ?'
            params.append(category)
        
        query += ' ORDER BY a.pub_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        result = []
        for article in articles:
            result.append({
                'id': article['id'],
                'title': article['title'],
                'zh_title': article['zh_title'] or article['title'],
                'description': article['description'],
                'source': article['source'],
                'pub_date': article['pub_date'],
                'category_id': article['category_id'],
            })
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    """Get single article with all details"""
    try:
        difficulty = request.args.get('difficulty', 'mid')
        language = request.args.get('language', 'en')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get article
        cursor.execute('''
            SELECT id, title, zh_title, description, source, pub_date, 
                   content, category_id
            FROM articles
            WHERE id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        if not article:
            conn.close()
            return jsonify({'error': 'Article not found'}), 404
        
        article_dict = dict(article)
        
        # Get summary for specific difficulty
        cursor.execute('''
            SELECT summary, summary_easy, summary_mid, summary_hard, zh_summary
            FROM article_summaries
            WHERE article_id = ?
        ''', (article_id,))
        
        summary_row = cursor.fetchone()
        summary_dict = {}
        if summary_row:
            summary_dict = dict(summary_row)
        
        # Get keywords
        cursor.execute('''
            SELECT keyword_id, keyword, frequency
            FROM article_keywords
            WHERE article_id = ?
            LIMIT 10
        ''', (article_id,))
        
        keywords = [{'id': row[0], 'keyword': row[1], 'frequency': row[2]} 
                   for row in cursor.fetchall()]
        
        # Get questions (quiz)
        cursor.execute('''
            SELECT id, question, options, correct_answer, explanation, difficulty
            FROM article_questions
            WHERE article_id = ?
            LIMIT 5
        ''', (article_id,))
        
        questions = []
        for row in cursor.fetchall():
            questions.append({
                'id': row[0],
                'question': row[1],
                'options': json.loads(row[2]) if row[2] else [],
                'correct_answer': row[3],
                'explanation': row[4],
                'difficulty': row[5]
            })
        
        # Get comments
        cursor.execute('''
            SELECT id, comment, created_at, user_name
            FROM article_comments
            WHERE article_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (article_id,))
        
        comments = [{'id': row[0], 'comment': row[1], 'created_at': row[2], 'user_name': row[3]} 
                   for row in cursor.fetchall()]
        
        # Get analysis
        cursor.execute('''
            SELECT analysis_text, perspectives
            FROM article_analysis
            WHERE article_id = ?
        ''', (article_id,))
        
        analysis_row = cursor.fetchone()
        analysis_dict = {}
        if analysis_row:
            analysis_dict = {
                'analysis_text': analysis_row[0],
                'perspectives': json.loads(analysis_row[1]) if analysis_row[1] else []
            }
        
        conn.close()
        
        # Select appropriate summary based on difficulty
        summary = ''
        if difficulty == 'easy':
            summary = summary_dict.get('summary_easy', '')
        elif difficulty == 'hard':
            summary = summary_dict.get('summary_hard', '')
        else:
            summary = summary_dict.get('summary_mid', '')
        
        if not summary:
            summary = summary_dict.get('summary', '')
        
        return jsonify({
            'article': article_dict,
            'summary': summary,
            'keywords': keywords,
            'questions': questions,
            'comments': comments,
            'analysis': analysis_dict.get('analysis_text', ''),
            'perspectives': analysis_dict.get('perspectives', []),
            'background_reading': ''  # Add if you have this table
        })
    
    except Exception as e:
        print(f"Error fetching article detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM articles')
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'articles_count': count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all available categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories ORDER BY name')
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting News API Server...")
    print("📡 Server running on http://localhost:8000")
    print("🔗 API endpoints:")
    print("   - GET  /api/articles - List articles")
    print("   - GET  /api/articles/<id> - Article detail")
    print("   - GET  /api/categories - Categories")
    print("   - GET  /api/health - Health check")
    app.run(host='localhost', port=8000, debug=True)
