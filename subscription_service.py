#!/usr/bin/env python3
"""
Email Subscription Service
Handles user subscriptions and sends daily/weekly digests via Email API
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# Configuration
EMAIL_API_BASE_URL = os.environ.get('EMAIL_API_BASE_URL', 'https://emailapi.6ray.com')
EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY', '')
DB_PATH = '/Users/jidai/news/subscriptions.db'
ARTICLES_JSON = '/Users/jidai/news/articles_data_with_summaries.json'

# Ensure database exists
def init_db():
    """Initialize subscription database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            frequency TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            category TEXT DEFAULT 'world',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sent TIMESTAMP,
            confirmation_token TEXT,
            confirmed BOOLEAN DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT,
            email_id TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def load_articles():
    """Load articles from JSON file"""
    try:
        with open(ARTICLES_JSON, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading articles: {e}")
        return []

def send_email_via_api(to_email, subject, message, from_name="Daily Digest"):
    """Send email via Email API"""
    try:
        payload = {
            'to_email': to_email,
            'subject': subject,
            'message': message,
            'from_name': from_name
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': EMAIL_API_KEY
        }
        
        response = requests.post(
            f"{EMAIL_API_BASE_URL}/send-email",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get('email_id', 'unknown')
        else:
            return False, response.text
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, str(e)

def generate_digest_html(articles, frequency, language='en'):
    """Generate HTML email digest"""
    lang = 'en' if language == 'en' else 'zh'
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .article {{ margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background: #f9f9f9; }}
            .article h3 {{ margin: 0 0 10px 0; color: #667eea; }}
            .article p {{ margin: 8px 0; }}
            .article .summary {{ font-size: 14px; color: #666; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📰 Daily Digest</h1>
                <p>Your AI-powered news summary</p>
            </div>
            
            <div style="margin: 20px 0;">
    """
    
    for article in articles:
        summary = article.get('summary_en' if lang == 'en' else 'summary_zh', '')[:300] + "..."
        keywords = ', '.join([kw.get('word', '') for kw in article.get('keywords', [])[:3]])
        
        html += f"""
            <div class="article">
                <h3>{article.get('title', 'Untitled')}</h3>
                <p><strong>{article.get('source', 'Unknown Source')}</strong> • {article.get('date', '')}</p>
                <p class="summary">{summary}</p>
                <p><strong>Key Topics:</strong> {keywords}</p>
                <a href="http://localhost:8000/main_articles_interface_v2.html" class="button">Read Full Analysis</a>
            </div>
        """
    
    html += """
            </div>
            
            <div class="footer">
                <p>You are receiving this because you subscribed to Daily Digest.</p>
                <p><a href="http://localhost:8000/unsubscribe">Unsubscribe</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle subscription requests"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        frequency = data.get('frequency', 'daily')
        
        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        if frequency not in ['daily', 'weekly']:
            return jsonify({'error': 'Invalid frequency'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO subscriptions (email, frequency, status)
                VALUES (?, ?, 'active')
            ''', (email, frequency))
            conn.commit()
            
            # Log the subscription
            print(f"New subscription: {email} ({frequency})")
            
            return jsonify({
                'success': True,
                'message': f'Subscription confirmed for {frequency} digest'
            }), 200
        except sqlite3.IntegrityError:
            # Email already subscribed, update frequency
            c.execute('''
                UPDATE subscriptions
                SET frequency = ?, status = 'active'
                WHERE email = ?
            ''', (frequency, email))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Subscription updated to {frequency} digest'
            }), 200
        finally:
            conn.close()
    
    except Exception as e:
        print(f"Subscription error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/unsubscribe', methods=['POST', 'GET'])
def unsubscribe():
    """Handle unsubscribe requests"""
    try:
        email = request.args.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email address required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            UPDATE subscriptions
            SET status = 'inactive'
            WHERE email = ?
        ''', (email,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Unsubscribed'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-digest', methods=['POST'])
def send_digest():
    """Send digest to all active subscribers (triggered by scheduler)"""
    try:
        frequency = request.json.get('frequency', 'daily')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get active subscriptions
        c.execute('''
            SELECT email, frequency, category, id
            FROM subscriptions
            WHERE status = 'active' AND frequency = ?
        ''', (frequency,))
        
        subscribers = c.fetchall()
        articles = load_articles()
        
        success_count = 0
        error_count = 0
        
        for email, freq, category, sub_id in subscribers:
            try:
                # Filter articles by category
                filtered_articles = [a for a in articles if category.lower() in a.get('source', '').lower()]
                if not filtered_articles:
                    filtered_articles = articles[:2]  # Fallback to first 2 articles
                
                # Generate digest HTML
                subject = f"📰 {frequency.capitalize()} Digest - {datetime.now().strftime('%Y-%m-%d')}"
                html_content = generate_digest_html(filtered_articles, frequency)
                
                # Send via Email API
                success, email_id = send_email_via_api(email, subject, html_content)
                
                if success:
                    # Log successful send
                    c.execute('''
                        INSERT INTO email_logs (email, subject, status, email_id)
                        VALUES (?, ?, 'sent', ?)
                    ''', (email, subject, email_id))
                    
                    c.execute('''
                        UPDATE subscriptions
                        SET last_sent = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (sub_id,))
                    
                    success_count += 1
                    print(f"✓ Sent to {email}")
                else:
                    error_count += 1
                    print(f"✗ Failed to send to {email}: {email_id}")
                    
                    c.execute('''
                        INSERT INTO email_logs (email, subject, status)
                        VALUES (?, ?, 'failed')
                    ''', (email, subject))
            
            except Exception as e:
                error_count += 1
                print(f"Error sending to {email}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'sent': success_count,
            'failed': error_count,
            'total': len(subscribers)
        }), 200
    
    except Exception as e:
        print(f"Send digest error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'subscription-service'}), 200

if __name__ == '__main__':
    print("Starting Subscription Service...")
    print(f"Email API: {EMAIL_API_BASE_URL}")
    print(f"API Key configured: {bool(EMAIL_API_KEY)}")
    app.run(host='localhost', port=5001, debug=True)
