#!/usr/bin/env python3
"""
Enhanced Subscription & Content Management System
Supports multiple difficulty levels and personalized content
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)
# Configuration
EMAIL_API_BASE_URL = os.environ.get('EMAIL_API_BASE_URL', 'https://emailapi.6ray.com')
EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY', '')
DB_PATH = '/Users/jidai/news/subscriptions.db'
ARTICLES_JSON = '/Users/jidai/news/articles_data_with_summaries.json'

def init_db():
    """Initialize enhanced database schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            website TEXT,
            description TEXT,
            color TEXT,
            emoji TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default categories
    categories = [
        ('World', 'pbs', 'World News', '#FF6B6B', '🌍'),
        ('Science', 'science', 'Scientific Research', '#4ECDC4', '🔬'),
        ('Technology', 'tech', 'Tech & Innovation', '#45B7D1', '💻'),
        ('Sports', 'swim', 'Sports & Athletics', '#FFA07A', '🏊'),
        ('Life', 'life', 'Lifestyle & Culture', '#98D8C8', '🎨'),
        ('Economy', 'economy', 'Economics & Finance', '#F7DC6F', '💰'),
    ]
    
    for name, website, desc, color, emoji in categories:
        try:
            c.execute('''
                INSERT INTO categories (name, website, description, color, emoji)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, website, desc, color, emoji))
        except sqlite3.IntegrityError:
            pass  # Category already exists
    
    # Enhanced articles table with category
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_article_id INTEGER,
            title TEXT NOT NULL,
            date TEXT,
            source TEXT,
            image_file TEXT,
            category_id INTEGER,
            original_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Article summaries by difficulty level
    c.execute('''
        CREATE TABLE IF NOT EXISTS article_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            language TEXT NOT NULL,
            summary TEXT,
            keywords TEXT,
            background TEXT,
            pro_arguments TEXT,
            con_arguments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles_enhanced(id),
            UNIQUE(article_id, difficulty, language)
        )
    ''')
    
    # Quiz questions by difficulty level
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            question_number INTEGER,
            question_text TEXT,
            options TEXT,
            correct_answer INTEGER,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles_enhanced(id)
        )
    ''')
    
    # Enhanced subscriptions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            age_group TEXT,
            difficulty_level TEXT,
            interests TEXT,
            frequency TEXT DEFAULT 'daily',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sent TIMESTAMP,
            confirmed BOOLEAN DEFAULT 0
        )
    ''')
    
    # Email logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            age_group TEXT,
            difficulty_level TEXT,
            subject TEXT,
            status TEXT,
            email_id TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized with enhanced schema")

init_db()

# Age group mappings
AGE_GROUPS = {
    'elementary': {
        'grades': '3-5',
        'age': '8-11',
        'difficulty': 'easy',
        'min_words': 100,
        'max_words': 200,
        'description': 'Elementary School (Grades 3-5)'
    },
    'middle': {
        'grades': '6-8',
        'age': '11-14',
        'difficulty': 'medium',
        'min_words': 300,
        'max_words': 500,
        'description': 'Middle School (Grades 6-8)'
    },
    'high': {
        'grades': '9-12',
        'age': '14-18',
        'difficulty': 'hard',
        'min_words': 500,
        'max_words': 700,
        'description': 'High School (Grades 9-12)'
    }
}

@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all available categories"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, emoji, description FROM categories ORDER BY name')
        categories = c.fetchall()
        conn.close()
        
        return jsonify({
            'categories': [
                {
                    'id': cat[0],
                    'name': cat[1],
                    'emoji': cat[2],
                    'description': cat[3]
                }
                for cat in categories
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscribe-enhanced', methods=['POST'])
def subscribe_enhanced():
    """Enhanced subscription with all user details"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        age_group = data.get('age_group', 'middle')
        interests = data.get('interests', [])  # List of category IDs
        frequency = data.get('frequency', 'daily')
        
        # Validate
        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        if not name or len(name) < 2:
            return jsonify({'error': 'Please enter your name'}), 400
        if age_group not in AGE_GROUPS:
            return jsonify({'error': 'Invalid age group'}), 400
        if not interests or len(interests) == 0:
            return jsonify({'error': 'Please select at least one interest'}), 400
        if frequency not in ['daily', 'weekly']:
            return jsonify({'error': 'Invalid frequency'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            # Get difficulty level based on age group
            difficulty = AGE_GROUPS[age_group]['difficulty']
            
            # Store interests as JSON string
            interests_json = json.dumps(interests)
            
            c.execute('''
                INSERT INTO subscriptions_enhanced 
                (email, name, age_group, difficulty_level, interests, frequency, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (email, name, age_group, difficulty, interests_json, frequency))
            
            conn.commit()
            
            print(f"✓ New subscription: {email} ({age_group}, {difficulty})")
            
            return jsonify({
                'success': True,
                'message': f'Welcome {name}! Subscription confirmed.',
                'difficulty': difficulty,
                'age_group': age_group
            }), 200
            
        except sqlite3.IntegrityError:
            # Update existing
            interests_json = json.dumps(interests)
            c.execute('''
                UPDATE subscriptions_enhanced
                SET name=?, age_group=?, difficulty_level=?, interests=?, frequency=?, status='active'
                WHERE email=?
            ''', (name, age_group, AGE_GROUPS[age_group]['difficulty'], interests_json, frequency, email))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Welcome back {name}! Preferences updated.'
            }), 200
            
        finally:
            conn.close()
    
    except Exception as e:
        print(f"Subscription error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-deepseek-summaries', methods=['POST'])
def generate_deepseek_summaries():
    """
    Generate 3 difficulty levels of summaries + questions in one batch
    Input: article_id, article_title, article_content
    Output: Returns prompt template for DeepSeek
    """
    try:
        data = request.json
        article_id = data.get('article_id')
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not article_id or not content:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Build combined prompt for all 3 levels
        prompt = f"""
Analyze this article and provide content for 3 difficulty levels:

ARTICLE TITLE: {title}
ARTICLE CONTENT:
{content}

===== TASK: Generate for all 3 levels in one response =====

For EACH difficulty level, provide BOTH summary AND 5 quiz questions.

---

LEVEL 1: ELEMENTARY (Grades 3-5, Age 8-11)
- Summary: 100-200 words, SIMPLE vocabulary, easy to understand
- Focus: Main facts, simple concepts
- NO: Background reading, arguments, original article link
- 5 Questions: Easy, recall-based

LEVEL 1 RESPONSE FORMAT:
{{
  "elementary": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [
      {{"word": "...", "frequency": 1, "explanation": "simple definition"}}
    ],
    "questions": [
      {{
        "question": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": 0,
        "explanation": "..."
      }}
    ]
  }}
}}

---

LEVEL 2: MIDDLE SCHOOL (Grades 6-8, Age 11-14)
- Summary: 300-500 words, intermediate vocabulary
- Focus: Facts, context, balanced perspective
- Include: background reading, PRO/CON arguments, original article link
- Same layout as High School
- 5 Questions: Medium difficulty, comprehension & analysis focus

LEVEL 2 RESPONSE FORMAT:
{{
  "middle": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [
      {{"word": "...", "frequency": 2, "explanation": "..."}}
    ],
    "background_reading": "...",
    "discussion": {{
      "pro": "...",
      "con": "..."
    }},
    "questions": [
      {{
        "question": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": 1,
        "explanation": "..."
      }}
    ]
  }}
}}

---

LEVEL 3: HIGH SCHOOL (Grades 9-12, Age 14-18)
- Summary: 500-700 words, sophisticated vocabulary
- Focus: Deep analysis, arguments, perspective
- Include: background reading, PRO/CON arguments, original article link
- Same layout as Middle School
- 5 Questions: Hard, analysis focus (structure, rhetoric, tone, intent)

LEVEL 3 RESPONSE FORMAT:
{{
  "high": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [
      {{"word": "...", "frequency": 3, "explanation": "..."}}
    ],
    "background_reading": "...",
    "discussion": {{
      "pro": "...",
      "con": "..."
    }},
    "questions": [
      {{
        "question": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": 2,
        "explanation": "..."
      }}
    ]
  }}
}}

---

RESPOND ONLY WITH VALID JSON. No markdown, no explanations. Just the JSON object with all three levels.
"""
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'article_id': article_id,
            'note': 'Send this prompt to DeepSeek API with temperature=0.7, max_tokens=8000'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/store-summaries', methods=['POST'])
def store_summaries():
    """Store generated summaries and questions to database"""
    try:
        data = request.json
        article_id = data.get('article_id')
        deepseek_response = data.get('summaries')  # Response from DeepSeek
        
        if not article_id or not deepseek_response:
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        stored_count = 0
        
        # Process each difficulty level
        for level_name, level_data in deepseek_response.items():
            if level_name not in ['elementary', 'middle', 'high']:
                continue
            
            difficulty = 'easy' if level_name == 'elementary' else 'medium' if level_name == 'middle' else 'hard'
            
            # Store summaries (EN and ZH)
            summary_en = level_data.get('summary_en', '')
            summary_zh = level_data.get('summary_zh', '')
            keywords = level_data.get('keywords', [])
            background = level_data.get('background_reading', '')
            discussion = level_data.get('discussion', {})
            
            # Store EN summary
            c.execute('''
                INSERT OR REPLACE INTO article_summaries
                (article_id, difficulty, language, summary, keywords, background, 
                 pro_arguments, con_arguments)
                VALUES (?, ?, 'en', ?, ?, ?, ?, ?)
            ''', (
                article_id, 
                difficulty, 
                summary_en,
                json.dumps(keywords),
                background,
                discussion.get('pro', ''),
                discussion.get('con', '')
            ))
            
            # Store ZH summary
            c.execute('''
                INSERT OR REPLACE INTO article_summaries
                (article_id, difficulty, language, summary, keywords, background,
                 pro_arguments, con_arguments)
                VALUES (?, ?, 'zh', ?, ?, ?, ?, ?)
            ''', (
                article_id,
                difficulty,
                summary_zh,
                json.dumps(keywords),
                background,
                discussion.get('pro', ''),
                discussion.get('con', '')
            ))
            
            # Store questions
            for idx, question in enumerate(level_data.get('questions', []), 1):
                c.execute('''
                    INSERT INTO quiz_questions
                    (article_id, difficulty, question_number, question_text, 
                     options, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    difficulty,
                    idx,
                    question.get('question', ''),
                    json.dumps(question.get('options', [])),
                    question.get('correct_answer', 0),
                    question.get('explanation', '')
                ))
            
            stored_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Stored summaries for {stored_count} difficulty levels',
            'article_id': article_id
        }), 200
    
    except Exception as e:
        print(f"Store summaries error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/article-content', methods=['GET'])
def get_article_content():
    """Fetch article content by difficulty level and language"""
    try:
        print(f"[API] Request received for article content")
        article_id = request.args.get('article_id', type=int)
        difficulty = request.args.get('difficulty', 'hard')
        language = request.args.get('language', 'en')
        
        print(f"[API] Parameters: id={article_id}, diff={difficulty}, lang={language}")
        
        if not article_id:
            return jsonify({'error': 'article_id required'}), 400
        
        # Map difficulty names to database values
        difficulty_map = {
            'high': 'hard',
            'hard': 'hard',
            'medium': 'medium',
            'mid': 'medium',
            'easy': 'easy'
        }
        difficulty = difficulty_map.get(difficulty.lower(), 'hard')
        print(f"[API] Mapped difficulty: {difficulty}")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        print(f"[API] Querying database...")
        # Query article_summaries table
        c.execute('''
            SELECT 
                article_id,
                difficulty,
                language,
                summary,
                keywords,
                background,
                pro_arguments,
                con_arguments
            FROM article_summaries
            WHERE article_id = ? AND difficulty = ? AND language = ?
            LIMIT 1
        ''', (article_id, difficulty, language))
        
        row = c.fetchone()
        conn.close()
        
        print(f"[API] Query result: {'Found' if row else 'Not found'}")
        
        if row:
            keywords_list = []
            if row['keywords']:
                try:
                    keywords_list = json.loads(row['keywords'])
                    if isinstance(keywords_list, str):
                        keywords_list = keywords_list.split(',')
                except:
                    keywords_list = row['keywords'].split(',') if isinstance(row['keywords'], str) else []
            
            result = {
                'article_id': row['article_id'],
                'difficulty': row['difficulty'],
                'language': row['language'],
                'summary': row['summary'] or '',
                'keywords': keywords_list,
                'background': row['background'] or '',
                'pro_arguments': row['pro_arguments'] or '',
                'con_arguments': row['con_arguments'] or ''
            }
            print(f"[API] Returning success response")
            return jsonify(result), 200
        else:
            print(f"[API] No content found, returning 404")
            # Fallback: return empty content
            return jsonify({
                'article_id': article_id,
                'difficulty': difficulty,
                'language': language,
                'summary': '',
                'keywords': [],
                'background': '',
                'pro_arguments': '',
                'con_arguments': ''
            }), 404
    
    except Exception as e:
        print(f"[API] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'enhanced-subscription-service',
        'age_groups': list(AGE_GROUPS.keys())
    }), 200

@app.route('/api/quiz-questions', methods=['GET'])
def get_quiz_questions():
    """Fetch quiz questions by article and difficulty level"""
    try:
        article_id = request.args.get('article_id', type=int)
        difficulty = request.args.get('difficulty', 'hard')
        
        if not article_id:
            return jsonify({'error': 'article_id required'}), 400
        
        # Map difficulty names to database values
        difficulty_map = {
            'high': 'hard',
            'hard': 'hard',
            'medium': 'medium',
            'mid': 'medium',
            'easy': 'easy'
        }
        difficulty = difficulty_map.get(difficulty.lower(), 'hard')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Query quiz_questions table
        c.execute('''
            SELECT 
                id,
                article_id,
                difficulty,
                question_number,
                question_text,
                options,
                correct_answer,
                explanation
            FROM quiz_questions
            WHERE article_id = ? AND difficulty = ?
            ORDER BY question_number
        ''', (article_id, difficulty))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            questions = []
            for row in rows:
                try:
                    options = json.loads(row['options']) if row['options'] else []
                except:
                    options = []
                
                questions.append({
                    'id': row['id'],
                    'question': row['question_text'],
                    'options': options,
                    'correct_answer': row['correct_answer'],
                    'explanation': row['explanation']
                })
            
            return jsonify({
                'article_id': article_id,
                'difficulty': difficulty,
                'questions': questions
            }), 200
        else:
            # No questions found
            return jsonify({
                'article_id': article_id,
                'difficulty': difficulty,
                'questions': []
            }), 404
    
    except Exception as e:
        print(f"Get quiz questions error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Enhanced Subscription Service")
    print("=" * 60)
    print(f"✓ Database: {DB_PATH}")
    print(f"✓ Email API: {EMAIL_API_BASE_URL}")
    print(f"✓ API Key: {'✓ Configured' if EMAIL_API_KEY else '✗ Not set'}")
    print("\nAge Groups:")
    for key, info in AGE_GROUPS.items():
        print(f"  • {key}: {info['description']}")
    print("\n" + "=" * 60)
    print("Starting server...")
    app.run(host='localhost', port=5001, debug=False, use_reloader=False)

