#!/usr/bin/env python3
"""
User Subscription API
Created: 2025-10-26
Purpose: Minimal backend API for user registration, token recovery, and stats sync
"""

from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import sqlite3
import uuid
import time
import json
import requests
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production-didadi-2025')

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


def require_session_auth(f):
    """Decorator for session-authenticated admin endpoints"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.route('/api/auth/login', methods=['POST'])
def admin_login():
    """
    Admin login endpoint (creates session)
    
    Request body:
        {
            "password": "admin_password"
        }
    
    Response:
        {
            "success": true
        }
    """
    data = request.get_json()
    password = data.get('password')
    
    if password == ADMIN_PASSWORD:
        session['authenticated'] = True
        session.permanent = True  # Keep session across browser restarts
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid password'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def admin_logout():
    """
    Admin logout endpoint (clears session)
    
    Response:
        {
            "success": true
        }
    """
    session.pop('authenticated', None)
    return jsonify({'success': True})


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """
    Check if user is authenticated
    
    Response:
        {
            "authenticated": true/false
        }
    """
    return jsonify({
        'authenticated': session.get('authenticated', False)
    })


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.route('/api/device/generate', methods=['GET'])
def generate_device_id():
    """
    Generate a unique device_id for tracking (works for anonymous users too)
    
    Returns a 20-character unique identifier that can be used for:
    - Anonymous user tracking
    - Offline token generation
    - User identification without email
    
    Response:
        {
            "device_id": "news-a1b2c3d4e5f6g7h8i9j0"
        }
    """
    device_id = f"news-{uuid.uuid4().hex[:20]}"
    
    return jsonify({
        'success': True,
        'device_id': device_id
    })


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
        # Generate device_id: must be 16+ chars, unique per user
        device_id = f"news-{uuid.uuid4().hex[:20]}"
        bootstrap_token = None
        bootstrap_failed = 0
        
        try:
            response = requests.post(
                f'{EMAIL_API_URL}/client/bootstrap',
                json={'email': email, 'device_id': device_id},
                timeout=5
            )
            if response.status_code == 200:
                bootstrap_token = response.json().get('api_key')
                print(f"✅ Bootstrap successful for {email}: {bootstrap_token}")
            else:
                print(f"⚠️  Bootstrap returned {response.status_code} for {email}: {response.text}")
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
                user_id, email, name, reading_style, device_id, bootstrap_token,
                bootstrap_failed, subscription_status, verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
        ''', (user_id, email, name, reading_style, device_id, bootstrap_token, 
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


@app.route('/api/user/delete', methods=['POST'])
def delete_user_subscription():
    """
    Delete user subscription and all associated data
    
    Headers:
        X-User-Token: bootstrap_token
    
    Request body:
        {
            "confirm": "DELETE"
        }
    
    Response:
        {
            "success": true,
            "message": "Subscription deleted successfully"
        }
    """
    token = request.headers.get('X-User-Token')
    data = request.json
    confirm = data.get('confirm') if data else None
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Missing X-User-Token header'
        }), 400
    
    if confirm != 'DELETE':
        return jsonify({
            'success': False,
            'error': 'Must confirm deletion with "DELETE"'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by token
        user = cursor.execute(
            'SELECT user_id, email, name FROM user_subscriptions WHERE bootstrap_token = ?',
            (token,)
        ).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        user_id = user['user_id']
        email = user['email']
        name = user['name']
        
        # Delete from user_stats_sync first (foreign key constraint)
        cursor.execute('DELETE FROM user_stats_sync WHERE user_id = ?', (user_id,))
        
        # Delete user subscription
        cursor.execute('DELETE FROM user_subscriptions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        
        print(f"🗑️  Deleted subscription for {name} ({email}) - User ID: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Subscription deleted successfully'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting subscription: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    """
    Get user information by token (for auto-login after verification)
    
    Headers:
        X-User-Token: bootstrap_token
    
    Response:
        {
            "success": true,
            "user_id": "uuid",
            "name": "User Name",
            "email": "user@example.com",
            "reading_style": "enjoy",
            "verified": true
        }
    """
    token = request.headers.get('X-User-Token')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Missing X-User-Token header'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by token
        user = cursor.execute('''
            SELECT user_id, name, email, reading_style, verified
            FROM user_subscriptions
            WHERE bootstrap_token = ?
        ''', (token,)).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'reading_style': user['reading_style'],
            'verified': bool(user['verified'])
        })
        
    except Exception as e:
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
        
        # Redirect to main page with success message AND token for auto-login
        return redirect(f'https://news.6ray.com/?verified=true&token={token}')
        
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


@app.route('/api/admin/subscriptions/<user_id>/reading-style', methods=['PUT'])
@require_auth
def update_subscription_reading_style(user_id):
    """
    Update subscription reading style (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Body:
        {
            "reading_style": "relax|enjoy|research|chinese"
        }
    """
    data = request.json or {}
    reading_style = data.get('reading_style')
    
    if reading_style not in ['relax', 'enjoy', 'research', 'chinese']:
        return jsonify({'error': 'Invalid reading style'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute('SELECT email FROM user_subscriptions WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update reading style
        cursor.execute('''
            UPDATE user_subscriptions
            SET reading_style = ?, updated_at = ?
            WHERE user_id = ?
        ''', (reading_style, int(time.time()), user_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Reading style updated to {reading_style}',
            'email': user['email']
        })
        
    finally:
        conn.close()


@app.route('/api/admin/subscriptions/<user_id>', methods=['DELETE'])
@require_auth
def delete_subscription(user_id):
    """
    Delete a subscription (admin only)
    
    Headers:
        X-Admin-Password: admin password
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user email before deletion
        cursor.execute('SELECT email FROM user_subscriptions WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user
        cursor.execute('DELETE FROM user_subscriptions WHERE user_id = ?', (user_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user["email"]} deleted successfully'
        })
        
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


@app.route('/api/admin/feeds', methods=['POST'])
@require_auth
def add_feed():
    """
    Add a new RSS feed (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Body:
        {
            "feed_name": str,
            "feed_url": str,
            "category_id": int,
            "enable": bool (optional, default True)
        }
    
    Response:
        {"message": "Feed added successfully", "feed_id": int}
    """
    data = request.get_json()
    
    feed_name = data.get('feed_name')
    feed_url = data.get('feed_url')
    category_id = data.get('category_id')
    enable = data.get('enable', True)
    
    if not feed_name or not feed_url or not category_id:
        return jsonify({'error': 'feed_name, feed_url, and category_id are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feeds (feed_name, feed_url, category_id, enable, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (feed_name, feed_url, category_id, 1 if enable else 0, current_time))
        
        conn.commit()
        feed_id = cursor.lastrowid
        
        return jsonify({
            'message': 'Feed added successfully',
            'feed_id': feed_id
        }), 201
        
    except sqlite3.IntegrityError as e:
        return jsonify({'error': 'Feed already exists or invalid category_id'}), 400
    finally:
        conn.close()


@app.route('/api/admin/feeds/<int:feed_id>', methods=['PUT'])
@require_auth
def update_feed(feed_id):
    """
    Update an existing RSS feed (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Body:
        {
            "feed_name": str (optional),
            "feed_url": str (optional),
            "category_id": int (optional),
            "enable": int (0 or 1, optional)
        }
    
    Response:
        {"message": "Feed updated successfully"}
    """
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build dynamic UPDATE query based on provided fields
        update_fields = []
        params = []
        
        if 'feed_name' in data:
            update_fields.append('feed_name = ?')
            params.append(data['feed_name'])
        
        if 'feed_url' in data:
            update_fields.append('feed_url = ?')
            params.append(data['feed_url'])
        
        if 'category_id' in data:
            update_fields.append('category_id = ?')
            params.append(data['category_id'])
        
        if 'enable' in data:
            update_fields.append('enable = ?')
            params.append(1 if data['enable'] else 0)
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(feed_id)
        query = f"UPDATE feeds SET {', '.join(update_fields)} WHERE feed_id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Feed not found'}), 404
        
        return jsonify({'message': 'Feed updated successfully'}), 200
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Invalid category_id or duplicate feed'}), 400
    finally:
        conn.close()


@app.route('/api/admin/feeds/<int:feed_id>', methods=['DELETE'])
@require_auth
def delete_feed(feed_id):
    """
    Delete an RSS feed (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {"message": "Feed deleted successfully"}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM feeds WHERE feed_id = ?', (feed_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Feed not found'}), 404
        
        return jsonify({'message': 'Feed deleted successfully'}), 200
        
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
# BACKUP & RESTORE ENDPOINTS
# ============================================================================

@app.route('/api/admin/backups', methods=['GET'])
@require_auth
def list_backups():
    """
    List all database backups (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        [{filename, size, created}, ...]
    """
    import os
    from pathlib import Path
    
    try:
        backups_dir = Path(__file__).parent.parent / 'backups'
        if not backups_dir.exists():
            return jsonify([])
        
        backups = []
        for file in backups_dir.glob('articles.db.*'):
            if file.is_file():
                stat = file.stat()
                backups.append({
                    'filename': file.name,
                    'size': stat.st_size,
                    'created': stat.st_mtime * 1000  # Convert to milliseconds for JavaScript
                })
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(backups)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backups/create', methods=['POST'])
@require_auth
def create_backup():
    """
    Create a new database backup (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {"message": "Backup created successfully", "filename": str}
    """
    import shutil
    from datetime import datetime
    
    try:
        db_path = Path(__file__).parent.parent / 'articles.db'
        backups_dir = Path(__file__).parent.parent / 'backups'
        backups_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'articles.db.{timestamp}'
        backup_path = backups_dir / backup_filename
        
        shutil.copy2(db_path, backup_path)
        
        return jsonify({
            'message': 'Backup created successfully',
            'filename': backup_filename
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backups/<filename>/restore', methods=['POST'])
@require_auth
def restore_backup(filename):
    """
    Restore database from a backup (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {"message": "Database restored successfully"}
    """
    import shutil
    from datetime import datetime
    
    try:
        db_path = Path(__file__).parent.parent / 'articles.db'
        backups_dir = Path(__file__).parent.parent / 'backups'
        backup_path = backups_dir / filename
        
        if not backup_path.exists():
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Create a safety backup of current database first
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safety_backup = backups_dir / f'articles.db.before_restore_{timestamp}'
        shutil.copy2(db_path, safety_backup)
        
        # Restore the backup
        shutil.copy2(backup_path, db_path)
        
        return jsonify({
            'message': f'Database restored successfully from {filename}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backups/<filename>', methods=['DELETE'])
@require_auth
def delete_backup(filename):
    """
    Delete a backup file (admin only)
    
    Headers:
        X-Admin-Password: admin password
    
    Response:
        {"message": "Backup deleted successfully"}
    """
    try:
        backups_dir = Path(__file__).parent.parent / 'backups'
        backup_path = backups_dir / filename
        
        if not backup_path.exists():
            return jsonify({'error': 'Backup file not found'}), 404
        
        backup_path.unlink()
        
        return jsonify({
            'message': 'Backup deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        # Check if cron job exists (check ec2-user's crontab, not root's)
        result = subprocess.run(['crontab', '-l', '-u', 'ec2-user'], capture_output=True, text=True)
        crontab_content = result.stdout
        
        # Look for pipeline cron job (check both script names)
        for line in crontab_content.split('\n'):
            if ('run_pipeline.sh' in line or 'run_pipeline_cron.sh' in line) and not line.strip().startswith('#'):
                # Parse cron schedule (e.g., "0 13 * * *" or "15 12 * * *")
                parts = line.split()
                if len(parts) >= 5:
                    minute = parts[0]
                    hour = parts[1]
                    
                    # Extract articles_per_seed from command line
                    # Format: run_pipeline_cron.sh 3  OR  --articles-per-seed 3
                    articles_per_seed = 3  # default
                    if '--articles-per-seed' in line:
                        idx = line.index('--articles-per-seed')
                        next_part = line[idx:].split()[1]
                        articles_per_seed = int(next_part)
                    elif 'run_pipeline_cron.sh' in line:
                        # Extract argument after script name (e.g., "run_pipeline_cron.sh 3")
                        script_parts = line.split('run_pipeline_cron.sh')
                        if len(script_parts) > 1:
                            args = script_parts[1].strip().split()
                            if args and args[0].isdigit():
                                articles_per_seed = int(args[0])
                    
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
        # Get current crontab (ec2-user's crontab)
        result = subprocess.run(['crontab', '-l', '-u', 'ec2-user'], capture_output=True, text=True)
        current_crontab = result.stdout
        
        # Remove existing pipeline cron job
        lines = []
        for line in current_crontab.split('\n'):
            if ('run_pipeline.sh' not in line and 'run_pipeline_cron.sh' not in line) or line.strip().startswith('#'):
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
        
        # Write new crontab (to ec2-user's crontab)
        new_crontab = '\n'.join(lines) + '\n'
        subprocess.run(['crontab', '-u', 'ec2-user', '-'], input=new_crontab, text=True, check=True)
        
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
        # Get current crontab (ec2-user's crontab)
        result = subprocess.run(['crontab', '-l', '-u', 'ec2-user'], capture_output=True, text=True)
        current_crontab = result.stdout
        
        # Remove pipeline cron job
        lines = []
        removed = False
        for line in current_crontab.split('\n'):
            if ('run_pipeline.sh' in line or 'run_pipeline_cron.sh' in line) and not line.strip().startswith('#'):
                removed = True
                continue  # Skip this line
            if line.strip():
                lines.append(line)
        
        if not removed:
            return jsonify({'error': 'No cron job found to disable'}), 404
        
        # Write new crontab (to ec2-user's crontab)
        new_crontab = '\n'.join(lines) + '\n' if lines else ''
        subprocess.run(['crontab', '-u', 'ec2-user', '-'], input=new_crontab, text=True, check=True)
        
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
    
    # ============================================
    # ADMIN API ENDPOINTS
    # ============================================
    
    @app.route('/api/admin/users', methods=['GET'])
    def admin_get_users():
        """Get all users (admin only)"""
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if admin_password != 'didadi':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, email, name, reading_style, verified, created_at
                FROM user_subscriptions
                ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'email': row[1],
                    'name': row[2],
                    'reading_style': row[3],
                    'verified': bool(row[4]),
                    'created_at': row[5]
                })
            
            conn.close()
            return jsonify({'success': True, 'users': users})
        
        except Exception as e:
            print(f"❌ Error fetching users: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/users/<user_id>/reading-style', methods=['PUT'])
    def admin_update_reading_style(user_id):
        """Update user's reading style (admin only)"""
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if admin_password != 'didadi':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            data = request.json
            reading_style = data.get('reading_style')
            
            if reading_style not in ['relax', 'enjoy', 'research', 'chinese']:
                return jsonify({'error': 'Invalid reading style'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_subscriptions
                SET reading_style = ?
                WHERE user_id = ?
            ''', (reading_style, user_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': f'Reading style updated to {reading_style}'})
        
        except Exception as e:
            print(f"❌ Error updating reading style: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/users/<user_id>', methods=['DELETE'])
    def admin_delete_user(user_id):
        """Delete a user (admin only)"""
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if admin_password != 'didadi':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user email before deletion
            cursor.execute('SELECT email FROM user_subscriptions WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return jsonify({'error': 'User not found'}), 404
            
            # Delete user
            cursor.execute('DELETE FROM user_subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': f'User {user[0]} deleted'})
        
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Run server on port 5001 (replacing old HTML server)
    app.run(host='0.0.0.0', port=5001, debug=True)
