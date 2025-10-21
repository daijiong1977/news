#!/usr/bin/env python3
"""
Direct Database Query Server for React Frontend
No Flask - just raw SQLite queries exposed via HTTP
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sqlite3
from pathlib import Path

DB_PATH = '/Users/jidai/news/articles.db'
IMAGES_DIR = Path('/Users/jidai/news/article_images')

class DBQueryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        try:
            # Handle image requests first (before sending JSON headers)
            if path.startswith('/api/images/'):
                filename = path.split('/')[-1]
                self.serve_image(filename)
                return
            
            # For other requests, send JSON headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            if path == '/api/articles':
                response = self.get_articles(query_params)
            elif path.startswith('/api/articles/'):
                article_id = path.split('/')[-1]
                response = self.get_article_detail(int(article_id), query_params)
            elif path == '/api/categories':
                response = self.get_categories()
            elif path == '/api/health':
                response = self.get_health()
            else:
                response = {'error': 'Not found'}
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            print(f"Error: {e}")
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle CORS OPTIONS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_articles(self, params):
        """Query articles from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        difficulty = params.get('difficulty', ['mid'])[0]
        language = params.get('language', ['en'])[0]
        category = params.get('category', [''])[0]
        limit = int(params.get('limit', ['20'])[0])
        
        # Get difficulty_id and language_id
        cursor.execute('SELECT difficulty_id FROM difficulty_levels WHERE difficulty = ?', (difficulty,))
        diff_result = cursor.fetchone()
        difficulty_id = diff_result['difficulty_id'] if diff_result else 2
        
        cursor.execute('SELECT language_id FROM languages WHERE language = ?', (language,))
        lang_result = cursor.fetchone()
        language_id = lang_result['language_id'] if lang_result else 1
        
        # Get category_id if category filter is provided
        category_id = None
        if category:
            cursor.execute('SELECT category_id FROM categories WHERE category_name = ?', (category,))
            cat_result = cursor.fetchone()
            category_id = cat_result['category_id'] if cat_result else None
        
        # Query articles with images
        query = '''
            SELECT DISTINCT a.id, a.title, a.zh_title, a.description, a.source, a.pub_date, a.category_id, img.image_name
            FROM articles a
            LEFT JOIN article_summaries s ON a.id = s.article_id 
                AND s.difficulty_id = ? AND s.language_id = ?
            LEFT JOIN article_images img ON a.id = img.article_id
        '''
        
        # Add category filter if provided
        if category_id:
            query += ' WHERE a.category_id = ?'
            query += ' ORDER BY a.pub_date DESC LIMIT ?'
            cursor.execute(query, (difficulty_id, language_id, category_id, limit))
        else:
            query += ' ORDER BY a.pub_date DESC LIMIT ?'
            cursor.execute(query, (difficulty_id, language_id, limit))
        
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
                'image': f'/api/images/{row["image_name"]}' if row['image_name'] else None
            }
            articles.append(article_data)
        
        conn.close()
        return articles
    
    def get_article_detail(self, article_id, params):
        """Query article detail from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        difficulty = params.get('difficulty', ['mid'])[0]
        language = params.get('language', ['en'])[0]
        
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
            return {'error': 'Article not found'}
        
        article_dict = dict(article)
        
        # Get summary
        cursor.execute('''
            SELECT summary FROM article_summaries 
            WHERE article_id = ? AND difficulty_id = ? AND language_id = ?
        ''', (article_id, difficulty_id, language_id))
        
        summary_row = cursor.fetchone()
        summary = summary_row['summary'] if summary_row else ''
        
        # Get image
        cursor.execute('SELECT image_name FROM article_images WHERE article_id = ? LIMIT 1', (article_id,))
        img_row = cursor.fetchone()
        image = f'/api/images/{img_row["image_name"]}' if img_row and img_row['image_name'] else None
        
        conn.close()
        
        return {
            'article': article_dict,
            'summary': summary,
            'image': image,
            'keywords': [],
            'questions': [],
            'comments': [],
            'analysis': '',
            'perspectives': []
        }
    
    def serve_image(self, filename):
        """Serve image file"""
        filepath = IMAGES_DIR / filename
        
        if not filepath.exists() or not str(filepath).startswith(str(IMAGES_DIR)):
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Image not found'}).encode())
            return
        
        # Determine content type
        content_type = 'image/jpeg'
        if filename.endswith('.png'):
            content_type = 'image/png'
        elif filename.endswith('.webp'):
            content_type = 'image/webp'
        
        with open(filepath, 'rb') as f:
            image_data = f.read()
        
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(image_data))
        self.end_headers()
        self.wfile.write(image_data)
    
    def get_categories(self):
        """Get all categories from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT category_id as id, category_name as name FROM categories ORDER BY category_name')
        categories = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def get_health(self):
        """Health check"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        articles_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM article_images')
        images_count = cursor.fetchone()[0]
        
        conn.close()
        return {
            'status': 'ok',
            'articles': articles_count,
            'images': images_count
        }
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server():
    host = '0.0.0.0'
    port = 8000
    server_address = (host, port)
    httpd = HTTPServer(server_address, DBQueryHandler)
    
    print("🚀 Direct Database Query Server")
    print(f"📡 Listening on http://localhost:{port}")
    print(f"📊 Database: {DB_PATH}")
    print("🔗 Endpoints:")
    print("   - GET /api/articles - List articles")
    print("   - GET /api/articles/<id> - Article detail")
    print("   - GET /api/categories - List categories")
    print("   - GET /api/images/<filename> - Serve images")
    print("   - GET /api/health - Health check")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
