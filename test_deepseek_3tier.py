#!/usr/bin/env python3
"""
Test Script: Generate 3-Tier Content for One Article
- Gets article content
- Sends to DeepSeek for 3-level generation
- Stores in database
- Generates 3 HTML files (easy, medium, hard)
"""

import os
import json
import sqlite3
import requests
from datetime import datetime

# Configuration
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
DB_PATH = '/Users/jidai/news/subscriptions.db'
ARTICLES_JSON = '/Users/jidai/news/articles_data_with_summaries.json'

def load_article(article_id):
    """Load article from JSON"""
    try:
        with open(ARTICLES_JSON, 'r') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        articles = data if isinstance(data, list) else data.get('articles', [])
        
        for article in articles:
            if article.get('id') == article_id:
                return article
        
        print(f"❌ Article {article_id} not found")
        return None
    except Exception as e:
        print(f"❌ Error loading article: {e}")
        return None

def init_db():
    """Initialize database tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create tables if not exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS article_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                difficulty TEXT,
                language TEXT,
                summary TEXT,
                keywords TEXT,
                background TEXT,
                pro_arguments TEXT,
                con_arguments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                difficulty TEXT,
                question_number INTEGER,
                question_text TEXT,
                options TEXT,
                correct_answer INTEGER,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def generate_deepseek_prompt(article):
    """Generate batch prompt for DeepSeek"""
    title = article.get('title', '')
    content = article.get('original_content', '')
    
    prompt = f"""Create 3-level personalized content for this article for different age groups.

ARTICLE TITLE: {title}

ARTICLE CONTENT:
{content}

Generate content at 3 difficulty levels:

LEVEL 1: ELEMENTARY (Grades 3-5, Age 8-11)  
- Summary: 100-200 words, very simple vocabulary
- Focus: Main facts only
- NO: background, arguments, or complex discussion
- Keywords: 10 simple keywords (grade 3-5 level)
- 5 Questions: Easy, fact-based

LEVEL 2: MIDDLE SCHOOL (Grades 6-8, Age 11-14)  
- Summary: 300-500 words, intermediate vocabulary
- Focus: Facts with context
- Include: background reading, pro/con arguments
- Keywords: 10 intermediate keywords (grade 6-8 level, CAN include level 1 keywords)
- 5 Questions: Medium, comprehension-based

LEVEL 3: HIGH SCHOOL (Grades 9-12, Age 14-18)
- Summary: 500-700 words, sophisticated vocabulary
- Focus: Analysis and arguments
- Include: background reading, detailed pro/con arguments
- Keywords: 10 advanced keywords (grade 9-12 level)
- 5 Questions: Hard, analysis-focused
- Chinese translations: ONLY provide Chinese if requested in JSON (for high school)

Return ONLY valid JSON with this exact structure:
{{
  "elementary": {{
    "summary_en": "...",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
    "questions": [
      {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": 0, "explanation": "..."}}
    ]
  }},
  "middle": {{
    "summary_en": "...",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
    "background": "...",
    "discussion": {{"pro": "...", "con": "..."}},
    "questions": [
      {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": 1, "explanation": "..."}}
    ]
  }},
  "high": {{
    "summary_en": "...",
    "summary_zh": "... (if original article has Chinese)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
    "background": "...",
    "discussion": {{"pro": "...", "con": "..."}},
    "questions": [
      {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": 2, "explanation": "..."}}
    ]
  }}
}}"""
    
    return prompt

def call_deepseek(prompt):
    """Call DeepSeek API"""
    try:
        if not DEEPSEEK_API_KEY:
            print("❌ ERROR: DEEPSEEK_API_KEY environment variable not set")
            print("   Set it with: export DEEPSEEK_API_KEY='your-api-key'")
            return None
        
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 8000
        }
        
        print("🔄 Calling DeepSeek API...")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ DeepSeek error: {response.status_code}")
            print(response.text)
            return None
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON from response
        try:
            # Try to extract JSON if it's wrapped in markdown
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            data = json.loads(content)
            print("✅ DeepSeek response received and parsed")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Response: {content[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ API call error: {e}")
        return None

def store_content(article_id, title, content_data):
    """Store generated content in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        levels = ['elementary', 'middle', 'high']
        
        # Check if original article has Chinese version
        has_chinese = 'summary_zh' in content_data.get('elementary', {})
        
        for level in levels:
            level_data = content_data.get(level, {})
            
            # Store summary
            summary_en = level_data.get('summary_en', '')
            summary_zh = level_data.get('summary_zh', '')
            keywords = json.dumps(level_data.get('keywords', []))
            background = level_data.get('background', '')
            
            discussion = level_data.get('discussion', {})
            pro = discussion.get('pro', '')
            con = discussion.get('con', '')
            
            difficulty_map = {'elementary': 'easy', 'middle': 'medium', 'high': 'hard'}
            difficulty = difficulty_map[level]
            
            # Always store English version
            c.execute('''
                INSERT INTO article_summaries 
                (article_id, difficulty, language, summary, keywords, background, pro_arguments, con_arguments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (article_id, difficulty, 'en', summary_en, keywords, background, pro, con))
            
            # Store Chinese version ONLY for HIGH SCHOOL, or if original has Chinese
            if level == 'high' or has_chinese:
                c.execute('''
                    INSERT INTO article_summaries 
                    (article_id, difficulty, language, summary, keywords, background, pro_arguments, con_arguments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (article_id, difficulty, 'zh', summary_zh, keywords, background, pro, con))
            
            # Store questions
            questions = level_data.get('questions', [])
            for i, q in enumerate(questions, 1):
                c.execute('''
                    INSERT INTO quiz_questions
                    (article_id, difficulty, question_number, question_text, options, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    difficulty,
                    i,
                    q.get('question', ''),
                    json.dumps(q.get('options', [])),
                    q.get('correct_answer', 0),
                    q.get('explanation', '')
                ))
        
        conn.commit()
        conn.close()
        print("✅ Content stored in database")
        return True
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return False

def retrieve_content(article_id):
    """Retrieve generated content from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        content_by_level = {}
        
        # Get summaries
        c.execute('''
            SELECT difficulty, language, summary, keywords, background, pro_arguments, con_arguments
            FROM article_summaries
            WHERE article_id = ?
            ORDER BY difficulty, language
        ''', (article_id,))
        
        summaries = c.fetchall()
        
        for difficulty, language, summary, keywords, background, pro, con in summaries:
            if difficulty not in content_by_level:
                content_by_level[difficulty] = {}
            
            content_by_level[difficulty][language] = {
                'summary': summary,
                'keywords': json.loads(keywords) if keywords else [],
                'background': background,
                'pro_arguments': pro,
                'con_arguments': con
            }
        
        # Get questions
        c.execute('''
            SELECT difficulty, question_number, question_text, options, correct_answer, explanation
            FROM quiz_questions
            WHERE article_id = ?
            ORDER BY difficulty, question_number
        ''', (article_id,))
        
        questions = c.fetchall()
        questions_by_level = {}
        
        for difficulty, qnum, qtext, opts, correct, expl in questions:
            if difficulty not in questions_by_level:
                questions_by_level[difficulty] = []
            
            questions_by_level[difficulty].append({
                'number': qnum,
                'question': qtext,
                'options': json.loads(opts) if opts else [],
                'correct_answer': correct,
                'explanation': expl
            })
        
        conn.close()
        print("✅ Content retrieved")
        return content_by_level, questions_by_level
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return {}, {}

def generate_html_elementary(article, content, questions):
    """Generate HTML for Elementary level (simplified)"""
    # Get English content, default to empty strings if missing
    en_content = content.get('en', {}) if content else {}
    summary = en_content.get('summary', '(Content not available)')
    keywords = en_content.get('keywords', [])
    
    questions_html = []
    for q in questions.get('easy', []):
        q_html = f'''
        <div class="question">
            <div class="question-text">Q{q['number']}: {q['question']}</div>
            <div class="options">
                {''.join(f'<div class="option">{opt}</div>' for opt in q['options'])}
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                <strong>Answer:</strong> {q['options'][q['correct_answer']]} - {q['explanation']}
            </div>
        </div>
        '''
        questions_html.append(q_html)
    
    keywords_html = ''.join(f'<div class="keyword">{kw}</div>' for kw in keywords)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elementary - {article['title']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .level-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.3);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #667eea;
            font-size: 20px;
            margin-bottom: 15px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .summary {{
            line-height: 1.8;
            font-size: 16px;
            color: #333;
        }}
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .keyword {{
            background: #e8f0ff;
            color: #667eea;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        .quiz-container {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
        }}
        .question {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .question-text {{
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 16px;
        }}
        .options {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .option {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <div class="level-badge">Elementary Level (Grades 3-5)</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>What You Should Know</h2>
                <div class="summary">{summary}</div>
            </div>
            
            <div class="section">
                <h2>Key Topics</h2>
                <div class="keywords">{keywords_html}</div>
            </div>
            
            <div class="section">
                <h2>Let's Check What You Learned</h2>
                <div class="quiz-container">
                    {''.join(questions_html)}
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
</body>
</html>
"""
    return html

def generate_html_middle(article, content, questions):
    """Generate HTML for Middle School level (standard)"""
    en_content = content.get('en', {}) if content else {}
    summary = en_content.get('summary', '(Content not available)')
    keywords = en_content.get('keywords', [])
    background = en_content.get('background', '(Background not available)')
    pro_args = en_content.get('pro_arguments', '(Arguments not available)')
    con_args = en_content.get('con_arguments', '(Arguments not available)')
    
    questions_html = []
    for q in questions.get('medium', []):
        q_html = f'''
        <div class="question">
            <div class="question-text">Q{q['number']}: {q['question']}</div>
            <div class="options">
                {''.join(f'<div class="option">{opt}</div>' for opt in q['options'])}
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                <strong>Answer:</strong> {q['options'][q['correct_answer']]} - {q['explanation']}
            </div>
        </div>
        '''
        questions_html.append(q_html)
    
    keywords_html = ''.join(f'<div class="keyword">{kw}</div>' for kw in keywords)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Middle School - {article['title']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .level-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.3);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #f5576c;
            font-size: 22px;
            margin-bottom: 15px;
            border-bottom: 3px solid #f5576c;
            padding-bottom: 10px;
        }}
        .summary {{
            line-height: 1.8;
            font-size: 16px;
            color: #333;
        }}
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .keyword {{
            background: #ffe8f0;
            color: #f5576c;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        .background {{
            line-height: 1.7;
            color: #555;
            background: #fff5f8;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #f5576c;
        }}
        .discussion {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .argument {{
            padding: 15px;
            border-radius: 8px;
        }}
        .argument.pro {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
        }}
        .argument.con {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .argument h3 {{
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .argument p {{
            line-height: 1.6;
            font-size: 14px;
            color: #333;
        }}
        .quiz-container {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
        }}
        .question {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #f5576c;
        }}
        .question-text {{
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 16px;
        }}
        .options {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .option {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <div class="level-badge">Middle School Level (Grades 6-8)</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>Article Summary</h2>
                <div class="summary">{summary}</div>
            </div>
            
            <div class="section">
                <h2>Key Topics</h2>
                <div class="keywords">{keywords_html}</div>
            </div>
            
            <div class="section">
                <h2>Background Information</h2>
                <div class="background">{background}</div>
            </div>
            
            <div class="section">
                <h2>Different Perspectives</h2>
                <div class="discussion">
                    <div class="argument pro">
                        <h3>Supporting Arguments</h3>
                        <p>{pro_args}</p>
                    </div>
                    <div class="argument con">
                        <h3>Counter Arguments</h3>
                        <p>{con_args}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Check Your Understanding</h2>
                <div class="quiz-container">
                    {''.join(questions_html)}
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
</body>
</html>
"""
    return html

def generate_html_high(article, content, questions):
    """Generate HTML for High School level (advanced)"""
    en_content = content.get('en', {}) if content else {}
    summary = en_content.get('summary', '(Content not available)')
    keywords = en_content.get('keywords', [])
    background = en_content.get('background', '(Background not available)')
    pro_args = en_content.get('pro_arguments', '(Arguments not available)')
    con_args = en_content.get('con_arguments', '(Arguments not available)')
    
    questions_html = []
    for q in questions.get('hard', []):
        q_html = f'''
        <div class="question">
            <div class="question-text">Q{q['number']}: {q['question']}</div>
            <div class="options">
                {''.join(f'<div class="option">{opt}</div>' for opt in q['options'])}
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                <strong>Answer:</strong> {q['options'][q['correct_answer']]} - {q['explanation']}
            </div>
        </div>
        '''
        questions_html.append(q_html)
    
    keywords_html = ''.join(f'<div class="keyword">{kw}</div>' for kw in keywords)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High School - {article['title']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .level-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.3);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #00f2fe;
            font-size: 22px;
            margin-bottom: 15px;
            border-bottom: 3px solid #00f2fe;
            padding-bottom: 10px;
        }}
        .summary {{
            line-height: 1.8;
            font-size: 16px;
            color: #333;
        }}
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .keyword {{
            background: #e0f7ff;
            color: #00f2fe;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        .background {{
            line-height: 1.7;
            color: #555;
            background: #f0feff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #00f2fe;
        }}
        .discussion {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .argument {{
            padding: 15px;
            border-radius: 8px;
        }}
        .argument.pro {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
        }}
        .argument.con {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .argument h3 {{
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .argument p {{
            line-height: 1.6;
            font-size: 14px;
            color: #333;
        }}
        .quiz-container {{
            background: #f0feff;
            padding: 20px;
            border-radius: 10px;
        }}
        .question {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #00f2fe;
        }}
        .question-text {{
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 16px;
        }}
        .options {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .option {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }}
        .footer {{
            background: #f0feff;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <div class="level-badge">High School Level (Grades 9-12)</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>In-Depth Analysis</h2>
                <div class="summary">{summary}</div>
            </div>
            
            <div class="section">
                <h2>Key Concepts</h2>
                <div class="keywords">{keywords_html}</div>
            </div>
            
            <div class="section">
                <h2>Historical & Contextual Background</h2>
                <div class="background">{background}</div>
            </div>
            
            <div class="section">
                <h2>Critical Analysis</h2>
                <div class="discussion">
                    <div class="argument pro">
                        <h3>Supporting Arguments</h3>
                        <p>{pro_args}</p>
                    </div>
                    <div class="argument con">
                        <h3>Counter Arguments & Limitations</h3>
                        <p>{con_args}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Advanced Comprehension & Analysis</h2>
                <div class="quiz-container">
                    {''.join(questions_html)}
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    """Main workflow"""
    print("=" * 70)
    print("🚀 DEEPSEEK 3-TIER CONTENT GENERATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Initialize database
    print("Step 1: Initializing database...")
    if not init_db():
        return False
    
    # Step 2: Load article
    print("\nStep 2: Loading article...")
    article = load_article(6)
    if not article:
        return False
    print(f"✅ Loaded: {article['title'][:60]}...")
    
    # Step 3: Generate prompt
    print("\nStep 3: Generating DeepSeek prompt...")
    prompt = generate_deepseek_prompt(article)
    print(f"✅ Prompt created ({len(prompt)} characters)")
    
    # Step 4: Call DeepSeek
    print("\nStep 4: Calling DeepSeek API (this may take a minute)...")
    content_data = call_deepseek(prompt)
    if not content_data:
        return False
    
    # Step 5: Store in database
    print("\nStep 5: Storing content in database...")
    if not store_content(article['id'], article['title'], content_data):
        return False
    
    # Step 6: Retrieve content
    print("\nStep 6: Retrieving content from database...")
    content_by_level, questions_by_level = retrieve_content(article['id'])
    if not content_by_level:
        print("❌ No content retrieved")
        return False
    
    # Step 7: Generate HTML files
    print("\nStep 7: Generating HTML files...")
    
    # Elementary
    html_elementary = generate_html_elementary(article, content_by_level.get('easy', {}), questions_by_level)
    with open('/Users/jidai/news/article_6_elementary.html', 'w') as f:
        f.write(html_elementary)
    print("✅ article_6_elementary.html created")
    
    # Middle
    html_middle = generate_html_middle(article, content_by_level.get('medium', {}), questions_by_level)
    with open('/Users/jidai/news/article_6_middle.html', 'w') as f:
        f.write(html_middle)
    print("✅ article_6_middle.html created")
    
    # High
    html_high = generate_html_high(article, content_by_level.get('hard', {}), questions_by_level)
    with open('/Users/jidai/news/article_6_high.html', 'w') as f:
        f.write(html_high)
    print("✅ article_6_high.html created")
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Generated 3 HTML files")
    print("=" * 70)
    print("\n📂 View the generated files:")
    print("   Elementary: file:///Users/jidai/news/article_6_elementary.html")
    print("   Middle:     file:///Users/jidai/news/article_6_middle.html")
    print("   High:       file:///Users/jidai/news/article_6_high.html")
    print("\n💾 Data stored in database:")
    print(f"   Location: {DB_PATH}")
    print("   Tables: article_summaries, quiz_questions")
    print("\n")
    
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
