#!/usr/bin/env python3
"""
User Subscription API
Created: 2025-10-26
Purpose: Minimal backend API for user registration, token recovery, and stats sync
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import sqlite3
import uuid
import time
import json
import requests
from pathlib import Path
import os

app = Flask(__name__)

# CORS Configuration (optional - for future GitHub Pages migration)
# Uncomment and configure when deploying statistics to GitHub Pages
CORS_ENABLED = os.getenv('ENABLE_CORS', 'false').lower() == 'true'
GITHUB_PAGES_URL = os.getenv('GITHUB_PAGES_URL', '')  # e.g., https://username.github.io

if CORS_ENABLED and GITHUB_PAGES_URL:
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://news.6ray.com",
                GITHUB_PAGES_URL
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-Token"]
        }
    })
    print(f"✅ CORS enabled for: news.6ray.com, {GITHUB_PAGES_URL}")
else:
    print("ℹ️  CORS disabled (set ENABLE_CORS=true and GITHUB_PAGES_URL to enable)")

# Configuration
EMAIL_API_URL = os.getenv('EMAIL_API_URL', 'https://emailapi.6ray.com')
DB_PATH = Path(__file__).parent.parent / 'articles.db'

# Admin authentication (simple password - same as existing admin panel)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'didadi')


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_auth(f):
    """Decorator for admin-only endpoints"""
    def decorated_function(*args, **kwargs):
        password = request.headers.get('X-Admin-Password')
        if password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.route('/api/user/register', methods=['POST'])
def register_user():
    """
    Register new user and bootstrap with emailapi
    
    Request body:
        {
            "email": "user@example.com",
            "name": "John Doe",
            "reading_style": "relax|enjoy|research|chinese"
        }
    
    Response:
        {
            "success": true,
            "user_id": "uuid",
            "bootstrap_token": "key_id.secret",
            "bootstrap_failed": 0|1,
            "message": "Registration successful"
        }
    """
    data = request.json
    email = data.get('email')
    name = data.get('name')
    reading_style = data.get('reading_style')
    
    # Validation
    if not email or not name or not reading_style:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: email, name, reading_style'
        }), 400
    
    if reading_style not in ['relax', 'enjoy', 'research', 'chinese']:
        return jsonify({
            'success': False,
            'error': 'Invalid reading_style. Must be: relax, enjoy, research, or chinese'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already registered
        existing = cursor.execute(
            'SELECT user_id, bootstrap_token FROM user_subscriptions WHERE email = ?',
            (email,)
        ).fetchone()
        
        if existing:
            return jsonify({
                'success': True,
                'user_id': existing['user_id'],
                'bootstrap_token': existing['bootstrap_token'],
                'message': 'Email already registered'
            })
        
        # Call emailapi bootstrap
        device_id = f"news-user-{email}"
        bootstrap_token = None
        bootstrap_failed = 0
        
        try:
            response = requests.post(
                f'{EMAIL_API_URL}/client/bootstrap',
                json={'device_id': device_id, 'display_name': name},
                timeout=5
            )
            if response.status_code == 200:
                bootstrap_token = response.json().get('api_key')
                print(f"✅ Bootstrap successful for {email}")
            else:
                print(f"⚠️  Bootstrap returned {response.status_code} for {email}")
                bootstrap_failed = 1
        except Exception as e:
            print(f"⚠️  Bootstrap failed: {e}")
            bootstrap_failed = 1
        
        # Generate local fallback token if bootstrap failed
        if not bootstrap_token:
            bootstrap_token = f"local-{uuid.uuid4()}"
            print(f"ℹ️  Using local fallback token for {email}")
        
        # Create user
        user_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        cursor.execute('''
            INSERT INTO user_subscriptions (
                user_id, email, name, reading_style, bootstrap_token,
                bootstrap_failed, subscription_status, verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
        ''', (user_id, email, name, reading_style, bootstrap_token, 
              bootstrap_failed, timestamp, timestamp))
        
        # Send verification email if bootstrap succeeded
        if not bootstrap_failed and bootstrap_token and not bootstrap_token.startswith('local-'):
            try:
                verify_url = f"https://news.6ray.com/api/verify?token={bootstrap_token}"
                requests.post(
                    f'{EMAIL_API_URL}/send-email',
                    headers={'X-API-Key': bootstrap_token},
                    json={
                        'to_email': email,
                        'subject': 'Verify your News Oh,Ye! subscription',
                        'message': f'Welcome {name}!\n\nClick here to verify: {verify_url}\n\nThis link will activate your email newsletter subscription.',
                        'from_name': 'News Oh,Ye!'
                    },
                    timeout=5
                )
                print(f"✅ Verification email sent to {email}")
            except Exception as e:
                print(f"⚠️  Failed to send verification email: {e}")
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'bootstrap_token': bootstrap_token,
            'bootstrap_failed': bootstrap_failed,
            'message': 'Registration successful'
        })
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()


@app.route('/api/user/token', methods=['POST'])
def get_user_token():
    """
    Recover bootstrap token by email (when user loses token)
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Response:
        {
            "success": true,
            "user_id": "uuid",
            "bootstrap_token": "key_id.secret",
            "name": "John Doe",
            "reading_style": "enjoy",
            "bootstrap_failed": 0|1
        }
    """
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user = cursor.execute('''
            SELECT user_id, bootstrap_token, name, reading_style, bootstrap_failed
            FROM user_subscriptions
            WHERE email = ?
        ''', (email,)).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'bootstrap_token': user['bootstrap_token'],
            'name': user['name'],
            'reading_style': user['reading_style'],
            'bootstrap_failed': user['bootstrap_failed']
        })
        
    finally:
        conn.close()


@app.route('/api/user/sync-stats', methods=['POST'])
def sync_user_stats():
    """
    Sync user statistics from localStorage to DB (user-initiated)
    
    Headers:
        X-User-Token: bootstrap_token
    
    Request body:
        {
            "stats": {
                "word_article123_democracy": {"completed": true, "timestamp": 1234567890},
                "quiz_article123_1234567890": {"score": 8, "total": 10, "timestamp": 1234567890}
            }
        }
    
    Response:
        {
            "success": true,
            "message": "Stats synced successfully",
            "last_sync": 1234567890
        }
    """
    token = request.headers.get('X-User-Token')
    data = request.json
    stats_data = data.get('stats')
    
    if not token or not stats_data:
        return jsonify({
            'success': False,
            'error': 'Missing X-User-Token header or stats data'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by token
        user = cursor.execute(
            'SELECT user_id FROM user_subscriptions WHERE bootstrap_token = ?',
            (token,)
        ).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        user_id = user['user_id']
        timestamp = int(time.time())
        
        # Upsert stats (SQLite 3.24.0+ syntax)
        cursor.execute('''
            INSERT INTO user_stats_sync (user_id, stats_json, last_sync)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                stats_json = excluded.stats_json,
                last_sync = excluded.last_sync
        ''', (user_id, json.dumps(stats_data), timestamp))
        
        conn.commit()
        
        print(f"✅ Stats synced for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Stats synced successfully',
            'last_sync': timestamp
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/verify', methods=['GET'])
def verify_email():
    """
    Verify user email via token link (called from email)
    
    Query params:
        token: bootstrap_token
    
    Response:
        Redirects to main page with verified=true parameter
    """
    token = request.args.get('token')
    
    if not token:
        return jsonify({'success': False, 'error': 'Token required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by token
        user = cursor.execute(
            'SELECT user_id, email FROM user_subscriptions WHERE bootstrap_token = ?',
            (token,)
        ).fetchone()
        
        if not user:
            return '''
                <html>
                <head><title>Verification Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Verification Failed</h1>
                    <p>Invalid or expired verification link.</p>
                    <a href="https://news.6ray.com">Return to News Oh,Ye!</a>
                </body>
                </html>
            ''', 404
        
        # Mark as verified
        cursor.execute('''
            UPDATE user_subscriptions
            SET verified = 1, subscription_status = 'active', updated_at = ?
            WHERE user_id = ?
        ''', (int(time.time()), user['user_id']))
        
        conn.commit()
        
        print(f"✅ Email verified for {user['email']}")
        
        # Redirect to main page with success message
        return redirect('https://news.6ray.com/?verified=true')
        
    except Exception as e:
        conn.rollback()
        return f'''
            <html>
            <head><title>Verification Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Verification Error</h1>
                <p>An error occurred: {str(e)}</p>
                <a href="https://news.6ray.com">Return to News Oh,Ye!</a>
            </body>
            </html>
        ''', 500
    finally:
        conn.close()


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.route('/api/admin/subscriptions', methods=['GET'])
@require_auth
def get_subscriptions():
    """
    Get all subscriptions (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "success": true,
            "total": 10,
            "verified": 7,
            "pending": 3,
            "subscriptions": [...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        subscriptions = cursor.execute('''
            SELECT user_id, email, name, reading_style, subscription_status,
                   verified, bootstrap_failed, created_at, updated_at
            FROM user_subscriptions
            ORDER BY created_at DESC
        ''').fetchall()
        
        total = len(subscriptions)
        verified = sum(1 for s in subscriptions if s['verified'] == 1)
        pending = total - verified
        
        return jsonify({
            'success': True,
            'total': total,
            'verified': verified,
            'pending': pending,
            'subscriptions': [dict(row) for row in subscriptions]
        })
        
    finally:
        conn.close()


@app.route('/api/admin/subscriptions/export', methods=['GET'])
@require_auth
def export_subscriptions():
    """
    Export email list as JSON (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "export_date": 1234567890,
            "total_count": 10,
            "subscribers": [...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        subscribers = cursor.execute('''
            SELECT email, name, reading_style, verified, created_at
            FROM user_subscriptions
            WHERE subscription_status = 'active'
            ORDER BY created_at DESC
        ''').fetchall()
        
        export_data = {
            'export_date': int(time.time()),
            'total_count': len(subscribers),
            'subscribers': [
                {
                    'email': row['email'],
                    'name': row['name'],
                    'reading_style': row['reading_style'],
                    'verified': bool(row['verified']),
                    'joined_date': row['created_at']
                }
                for row in subscribers
            ]
        }
        
        return jsonify(export_data)
        
    finally:
        conn.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'news-user-api',
        'timestamp': int(time.time())
    })


# ============================================================================
# ADMIN PANEL ENDPOINTS
# ============================================================================

@app.route('/api/admin/feeds', methods=['GET'])
@require_auth
def get_feeds():
    """
    Get all RSS feeds with category information (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "feeds": [{feed_id, feed_name, feed_url, category_name, enable, created_at}, ...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        feeds = cursor.execute('''
            SELECT 
                f.feed_id,
                f.feed_name,
                f.feed_url,
                f.enable,
                f.created_at,
                c.category_name,
                c.category_id
            FROM feeds f
            LEFT JOIN categories c ON f.category_id = c.category_id
            ORDER BY f.feed_name
        ''').fetchall()
        
        return jsonify({
            'feeds': [dict(feed) for feed in feeds]
        })
        
    finally:
        conn.close()


@app.route('/api/admin/categories', methods=['GET'])
@require_auth
def get_categories():
    """
    Get all categories (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "categories": [{category_id, category_name, description, prompt_name, created_at}, ...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        categories = cursor.execute('''
            SELECT category_id, category_name, description, prompt_name, created_at
            FROM categories
            ORDER BY category_name
        ''').fetchall()
        
        return jsonify({
            'categories': [dict(cat) for cat in categories]
        })
        
    finally:
        conn.close()


@app.route('/api/admin/articles', methods=['GET'])
@require_auth
def get_articles():
    """
    Get articles with optional filters (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Query Parameters:
        limit: Max number of articles (default 50)
        offset: Pagination offset (default 0)
        source: Filter by source
        processed: Filter by processing status (true/false/all)
        date: Filter by date (YYYY-MM-DD)
    
    Response:
        {
            "articles": [...],
            "total": count,
            "limit": limit,
            "offset": offset
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        source = request.args.get('source', None)
        processed = request.args.get('processed', 'all')
        date_filter = request.args.get('date', None)
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if source:
            where_clauses.append('source = ?')
            params.append(source)
        
        if processed == 'true':
            where_clauses.append('deepseek_processed = 1')
        elif processed == 'false':
            where_clauses.append('deepseek_processed = 0')
        
        if date_filter:
            where_clauses.append("DATE(pub_date) = ?")
            params.append(date_filter)
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        # Get total count
        total = cursor.execute(f'''
            SELECT COUNT(*) as count FROM articles WHERE {where_sql}
        ''', params).fetchone()['count']
        
        # Get articles
        articles = cursor.execute(f'''
            SELECT 
                id, title, source, url, description,
                pub_date, crawled_at, deepseek_processed,
                deepseek_failed, processed_at, zh_title
            FROM articles
            WHERE {where_sql}
            ORDER BY pub_date DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset]).fetchall()
        
        return jsonify({
            'articles': [dict(art) for art in articles],
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    finally:
        conn.close()


@app.route('/api/admin/apikeys', methods=['GET'])
@require_auth
def get_apikeys():
    """
    Get all API keys (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "apikeys": [{key_id, name, value}, ...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        apikeys = cursor.execute('''
            SELECT key_id, name, value
            FROM apikey
            ORDER BY name
        ''').fetchall()
        
        return jsonify({
            'apikeys': [dict(key) for key in apikeys]
        })
        
    finally:
        conn.close()


@app.route('/api/admin/stats', methods=['GET'])
@require_auth
def get_stats():
    """
    Get system statistics (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "articles": {total, processed, failed, pending},
            "by_source": [{source, count}, ...],
            "by_date": [{date, count}, ...],
            "images": {total, with_image},
            "recent_activity": {last_crawl, last_processed}
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Article statistics
        total_articles = cursor.execute('SELECT COUNT(*) as count FROM articles').fetchone()['count']
        processed = cursor.execute('SELECT COUNT(*) as count FROM articles WHERE deepseek_processed = 1').fetchone()['count']
        failed = cursor.execute('SELECT COUNT(*) as count FROM articles WHERE deepseek_failed > 0').fetchone()['count']
        pending = total_articles - processed - failed
        
        # By source
        by_source = cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
            ORDER BY count DESC
        ''').fetchall()
        
        # By date (last 7 days)
        by_date = cursor.execute('''
            SELECT DATE(pub_date) as date, COUNT(*) as count
            FROM articles
            WHERE pub_date >= DATE('now', '-7 days')
            GROUP BY DATE(pub_date)
            ORDER BY date DESC
        ''').fetchall()
        
        # Image statistics
        total_images = cursor.execute('SELECT COUNT(*) as count FROM article_images').fetchone()['count']
        
        # Recent activity
        last_crawl = cursor.execute('''
            SELECT MAX(crawled_at) as last_crawl FROM articles
        ''').fetchone()['last_crawl']
        
        last_processed = cursor.execute('''
            SELECT MAX(processed_at) as last_processed FROM articles WHERE deepseek_processed = 1
        ''').fetchone()['last_processed']
        
        return jsonify({
            'articles': {
                'total': total_articles,
                'processed': processed,
                'failed': failed,
                'pending': pending
            },
            'by_source': [dict(row) for row in by_source],
            'by_date': [dict(row) for row in by_date],
            'images': {
                'total': total_images
            },
            'recent_activity': {
                'last_crawl': last_crawl,
                'last_processed': last_processed
            }
        })
        
    finally:
        conn.close()


@app.route('/api/admin/article/<article_id>', methods=['GET'])
@require_auth
def get_article_detail(article_id):
    """
    Get detailed article information including all related data (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "article": {...},
            "image": {...},
            "summaries": [...],
            "keywords": [...],
            "questions": [...],
            "comments": [...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get article
        article = cursor.execute('''
            SELECT * FROM articles WHERE id = ?
        ''', (article_id,)).fetchone()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Get related data
        image = cursor.execute('''
            SELECT * FROM article_images WHERE article_id = ?
        ''', (article_id,)).fetchone()
        
        summaries = cursor.execute('''
            SELECT s.*, d.difficulty
            FROM article_summaries s
            LEFT JOIN difficulty_levels d ON s.difficulty_id = d.difficulty_id
            WHERE s.article_id = ?
        ''', (article_id,)).fetchall()
        
        keywords = cursor.execute('''
            SELECT k.*, d.difficulty
            FROM keywords k
            LEFT JOIN difficulty_levels d ON k.difficulty_id = d.difficulty_id
            WHERE k.article_id = ?
        ''', (article_id,)).fetchall()
        
        questions = cursor.execute('''
            SELECT q.*, d.difficulty
            FROM questions q
            LEFT JOIN difficulty_levels d ON q.difficulty_id = d.difficulty_id
            WHERE q.article_id = ?
        ''', (article_id,)).fetchall()
        
        comments = cursor.execute('''
            SELECT c.*, d.difficulty
            FROM comments c
            LEFT JOIN difficulty_levels d ON c.difficulty_id = d.difficulty_id
            WHERE c.article_id = ?
        ''', (article_id,)).fetchall()
        
        return jsonify({
            'article': dict(article) if article else None,
            'image': dict(image) if image else None,
            'summaries': [dict(row) for row in summaries],
            'keywords': [dict(row) for row in keywords],
            'questions': [dict(row) for row in questions],
            'comments': [dict(row) for row in comments]
        })
        
    finally:
        conn.close()


# ============================================================================
# CRON JOB MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/cron/status', methods=['GET'])
@require_auth
def get_cron_status():
    """
    Get cron job status (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "enabled": true,
            "schedule": "0 13 * * *",
            "hour": 13,
            "minute": 0,
            "articles_per_seed": 3
        }
    """
    import subprocess
    
    try:
        # Check if cron job exists
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        crontab_content = result.stdout
        
        # Look for pipeline cron job
        for line in crontab_content.split('\n'):
            if 'run_pipeline.sh' in line and not line.strip().startswith('#'):
                # Parse cron schedule (e.g., "0 13 * * *")
                parts = line.split()
                if len(parts) >= 5:
                    minute = parts[0]
                    hour = parts[1]
                    
                    # Extract articles_per_seed from command line (if present)
                    articles_per_seed = 3  # default
                    if '--articles-per-seed' in line:
                        idx = line.index('--articles-per-seed')
                        next_part = line[idx:].split()[1]
                        articles_per_seed = int(next_part)
                    
                    return jsonify({
                        'enabled': True,
                        'schedule': f"{minute} {hour} * * *",
                        'hour': int(hour) if hour.isdigit() else 13,
                        'minute': int(minute) if minute.isdigit() else 0,
                        'articles_per_seed': articles_per_seed
                    })
        
        # No cron job found
        return jsonify({
            'enabled': False,
            'schedule': None,
            'hour': 13,
            'minute': 0,
            'articles_per_seed': 3
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cron/enable', methods=['POST'])
@require_auth
def enable_cron():
    """
    Enable/update cron job with specified settings (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Body:
        {
            "hour": 13,
            "minute": 0,
            "articles_per_seed": 3
        }
    
    Response:
        {
            "success": true,
            "message": "Cron job enabled successfully",
            "schedule": "0 13 * * *"
        }
    """
    import subprocess
    
    data = request.json
    hour = data.get('hour', 13)
    minute = data.get('minute', 0)
    articles_per_seed = data.get('articles_per_seed', 3)
    
    # Validate inputs
    if not (0 <= hour <= 23):
        return jsonify({'error': 'Hour must be between 0 and 23'}), 400
    if not (0 <= minute <= 59):
        return jsonify({'error': 'Minute must be between 0 and 59'}), 400
    if not (1 <= articles_per_seed <= 10):
        return jsonify({'error': 'Articles per seed must be between 1 and 10'}), 400
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout
        
        # Remove existing pipeline cron job
        lines = []
        for line in current_crontab.split('\n'):
            if 'run_pipeline.sh' not in line or line.strip().startswith('#'):
                if line.strip():  # Keep non-empty lines
                    lines.append(line)
        
        # Add new cron job
        project_dir = str(Path(__file__).parent.parent.absolute())
        cron_line = f"{minute} {hour} * * * cd {project_dir} && bash run_pipeline.sh >> log/cron_$(date +\\%Y\\%m\\%d).log 2>&1"
        
        # Update run_pipeline.sh to use the specified articles_per_seed
        pipeline_script = project_dir + '/run_pipeline.sh'
        with open(pipeline_script, 'r') as f:
            script_content = f.read()
        
        # Replace articles-per-seed parameter
        import re
        script_content = re.sub(
            r'--articles-per-seed\s+\d+',
            f'--articles-per-seed {articles_per_seed}',
            script_content
        )
        
        with open(pipeline_script, 'w') as f:
            f.write(script_content)
        
        lines.append(cron_line)
        
        # Write new crontab
        new_crontab = '\n'.join(lines) + '\n'
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
        
        return jsonify({
            'success': True,
            'message': f'Cron job enabled: Daily at {hour:02d}:{minute:02d} with {articles_per_seed} articles per feed',
            'schedule': f'{minute} {hour} * * *'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cron/disable', methods=['POST'])
@require_auth
def disable_cron():
    """
    Disable cron job (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "success": true,
            "message": "Cron job disabled successfully"
        }
    """
    import subprocess
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout
        
        # Remove pipeline cron job
        lines = []
        removed = False
        for line in current_crontab.split('\n'):
            if 'run_pipeline.sh' in line and not line.strip().startswith('#'):
                removed = True
                continue  # Skip this line
            if line.strip():
                lines.append(line)
        
        if not removed:
            return jsonify({'error': 'No cron job found to disable'}), 404
        
        # Write new crontab
        new_crontab = '\n'.join(lines) + '\n' if lines else ''
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
        
        return jsonify({
            'success': True,
            'message': 'Cron job disabled successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cron/logs', methods=['GET'])
@require_auth
def get_cron_logs():
    """
    Get list of cron log files (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        [
            {
                "filename": "cron_20251026.log",
                "size": 12345,
                "modified": 1234567890
            },
            ...
        ]
    """
    import glob
    
    try:
        log_dir = Path(__file__).parent.parent / 'log'
        log_files = []
        
        # Get all cron log files
        for log_file in sorted(glob.glob(str(log_dir / 'cron_*.log')), reverse=True):
            stat = os.stat(log_file)
            log_files.append({
                'filename': os.path.basename(log_file),
                'size': stat.st_size,
                'modified': stat.st_mtime
            })
        
        # Also include pipeline_nohup logs
        for log_file in sorted(glob.glob(str(log_dir / 'pipeline_nohup_*.log')), reverse=True):
            stat = os.stat(log_file)
            log_files.append({
                'filename': os.path.basename(log_file),
                'size': stat.st_size,
                'modified': stat.st_mtime
            })
        
        return jsonify(log_files[:20])  # Return last 20 log files
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cron/logs/<filename>', methods=['GET'])
@require_auth
def get_cron_log_content(filename):
    """
    Get content of a specific log file (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {
            "filename": "cron_20251026.log",
            "content": "..."
        }
    """
    try:
        # Security: validate filename
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        log_dir = Path(__file__).parent.parent / 'log'
        log_file = log_dir / filename
        
        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404
        
        # Read last 10000 lines to prevent memory issues
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            content = ''.join(lines[-10000:])
        
        return jsonify({
            'filename': filename,
            'content': content
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("News User API Server")
    print("=" * 70)
    print(f"Database: {DB_PATH}")
    print(f"Email API: {EMAIL_API_URL}")
    print(f"CORS: {'Enabled' if CORS_ENABLED else 'Disabled'}")
    print(f"Port: 5001")
    print("=" * 70)
    
    # Run server on port 5001 (replacing old HTML server)
    app.run(host='0.0.0.0', port=5001, debug=True)
