#!/usr/bin/env python3
"""
Generate Interactive 3-Tier Article Page with Dropdown Selection
- Load article 1 (first one in the JSON)
- Send to DeepSeek for 3-level generation (with Chinese for ALL levels)
- Create SINGLE interactive HTML with dropdown to switch levels
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
    
    prompt = f"""Create 3-level personalized content for this article for different age groups. Provide BOTH English and Chinese for ALL levels.

ARTICLE TITLE: {title}

ARTICLE CONTENT:
{content}

Generate content at 3 difficulty levels:

LEVEL 1: ELEMENTARY (Grades 3-5, Age 8-11)  
- Summary: 100-200 words, very simple vocabulary
- Keywords: 10 simple keywords
- 5 Questions: Easy, fact-based
- Provide: English + Chinese

LEVEL 2: MIDDLE SCHOOL (Grades 6-8, Age 11-14)  
- Summary: 300-500 words, intermediate vocabulary
- Background: Context paragraph
- Discussion: Pro/Con arguments
- Keywords: 10 intermediate keywords
- 5 Questions: Medium, comprehension-based
- Provide: English + Chinese

LEVEL 3: HIGH SCHOOL (Grades 9-12, Age 14-18)
- Summary: 500-700 words, sophisticated vocabulary
- Background: Deep context paragraph
- Discussion: Detailed Pro/Con arguments
- Keywords: 10 advanced keywords
- 5 Questions: Hard, analysis-focused
- Provide: English + Chinese

Return ONLY valid JSON:
{{
  "elementary": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8", "kw9", "kw10"],
    "questions": [
      {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": 0, "explanation": "..."}}
    ]
  }},
  "middle": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8", "kw9", "kw10"],
    "background": "...",
    "background_zh": "...",
    "discussion": {{"pro": "...", "pro_zh": "...", "con": "...", "con_zh": "..."}},
    "questions": [
      {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": 1, "explanation": "..."}}
    ]
  }},
  "high": {{
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8", "kw9", "kw10"],
    "background": "...",
    "background_zh": "...",
    "discussion": {{"pro": "...", "pro_zh": "...", "con": "...", "con_zh": "..."}},
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
            return None
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            data = json.loads(content)
            print("✅ DeepSeek response received and parsed")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
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
        
        for level in levels:
            level_data = content_data.get(level, {})
            
            summary_en = level_data.get('summary_en', '')
            summary_zh = level_data.get('summary_zh', '')
            keywords = json.dumps(level_data.get('keywords', []))
            background = level_data.get('background', '')
            background_zh = level_data.get('background_zh', '')
            
            discussion = level_data.get('discussion', {})
            pro = discussion.get('pro', '')
            pro_zh = discussion.get('pro_zh', '')
            con = discussion.get('con', '')
            con_zh = discussion.get('con_zh', '')
            
            difficulty_map = {'elementary': 'easy', 'middle': 'medium', 'high': 'hard'}
            difficulty = difficulty_map[level]
            
            # Store English version
            c.execute('''
                INSERT INTO article_summaries 
                (article_id, difficulty, language, summary, keywords, background, pro_arguments, con_arguments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (article_id, difficulty, 'en', summary_en, keywords, background, pro, con))
            
            # Store Chinese version
            c.execute('''
                INSERT INTO article_summaries 
                (article_id, difficulty, language, summary, keywords, background, pro_arguments, con_arguments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (article_id, difficulty, 'zh', summary_zh, keywords, background_zh, pro_zh, con_zh))
            
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

def generate_interactive_html(article, content_by_level, questions_by_level):
    """Generate interactive HTML with dropdown to switch levels"""
    
    def build_level_html(difficulty, label, color, content, questions, lang='en'):
        """Build HTML section for one level"""
        en_content = content.get('en', {})
        zh_content = content.get('zh', {})
        
        if lang == 'en':
            summary = en_content.get('summary', '')
            keywords = en_content.get('keywords', [])
            background = en_content.get('background', '')
            pro = en_content.get('pro_arguments', '')
            con = en_content.get('con_arguments', '')
        else:
            summary = zh_content.get('summary', '')
            keywords = zh_content.get('keywords', [])
            background = zh_content.get('background', '')
            pro = zh_content.get('pro_arguments', '')
            con = zh_content.get('con_arguments', '')
        
        keywords_html = ''.join(f'<span class="keyword">{kw}</span>' for kw in keywords)
        
        questions_html = []
        for q in questions.get(difficulty, []):
            q_html = f'''
            <div class="question">
                <div class="question-text">Q{q['number']}: {q['question']}</div>
                <div class="options">
                    {''.join(f'<div class="option">{opt}</div>' for opt in q['options'])}
                </div>
                <div class="answer">
                    <strong>Answer:</strong> {q['options'][q['correct_answer']]} - {q['explanation']}
                </div>
            </div>
            '''
            questions_html.append(q_html)
        
        background_section = f'''
            <div class="section">
                <h3>📚 Background Information</h3>
                <p>{background}</p>
            </div>
        ''' if background else ''
        
        discussion_section = f'''
            <div class="section">
                <h3>💭 Different Perspectives</h3>
                <div class="discussion">
                    <div class="argument pro">
                        <h4>✅ Supporting Arguments</h4>
                        <p>{pro}</p>
                    </div>
                    <div class="argument con">
                        <h4>❌ Counter Arguments</h4>
                        <p>{con}</p>
                    </div>
                </div>
            </div>
        ''' if (pro or con) else ''
        
        return f'''
        <div class="level-content" id="level-{difficulty}-{lang}" style="display: none;">
            <div class="section">
                <h2>{label}</h2>
                <div class="summary">{summary}</div>
            </div>
            
            <div class="section">
                <h3>🎯 Key Topics</h3>
                <div class="keywords">{keywords_html}</div>
            </div>
            
            {background_section}
            {discussion_section}
            
            <div class="section">
                <h3>❓ Check Your Understanding</h3>
                <div class="quiz-container">
                    {''.join(questions_html)}
                </div>
            </div>
        </div>
        '''
    
    # Build all level sections
    easy_en = build_level_html('easy', 'Elementary Level (Grades 3-5)', '#667eea', content_by_level.get('easy', {}), questions_by_level, 'en')
    easy_zh = build_level_html('easy', '小学阶段 (3-5年级)', '#667eea', content_by_level.get('easy', {}), questions_by_level, 'zh')
    
    medium_en = build_level_html('medium', 'Middle School Level (Grades 6-8)', '#f5576c', content_by_level.get('medium', {}), questions_by_level, 'en')
    medium_zh = build_level_html('medium', '中学阶段 (6-8年级)', '#f5576c', content_by_level.get('medium', {}), questions_by_level, 'zh')
    
    hard_en = build_level_html('hard', 'High School Level (Grades 9-12)', '#00f2fe', content_by_level.get('hard', {}), questions_by_level, 'en')
    hard_zh = build_level_html('hard', '高中阶段 (9-12年级)', '#00f2fe', content_by_level.get('hard', {}), questions_by_level, 'zh')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive - {article['title']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 20px;
        }}
        .controls {{
            background: #f9f9f9;
            padding: 20px 30px;
            border-bottom: 1px solid #eee;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .control-group label {{
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }}
        select {{
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
        }}
        select:hover {{
            border-color: #667eea;
        }}
        select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            font-size: 24px;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .section h3 {{
            font-size: 18px;
            margin-bottom: 12px;
            color: #555;
        }}
        .summary {{
            line-height: 1.8;
            font-size: 16px;
            color: #444;
            text-align: justify;
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
        .discussion {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
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
        .argument h4 {{
            margin-bottom: 10px;
            font-size: 15px;
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
            border-left: 4px solid #667eea;
        }}
        .question-text {{
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 15px;
        }}
        .options {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .option {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
            font-size: 14px;
        }}
        .answer {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 13px;
        }}
        .footer {{
            background: #f9f9f9;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 13px;
            border-top: 1px solid #eee;
        }}
        @media (max-width: 768px) {{
            .controls {{
                grid-template-columns: 1fr;
            }}
            .discussion {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <p style="font-size: 16px; opacity: 0.9;">Choose your level and language below</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="level-select">📚 Education Level:</label>
                <select id="level-select" onchange="updateDisplay()">
                    <option value="easy">Elementary Level (Grades 3-5)</option>
                    <option value="medium">Middle School Level (Grades 6-8)</option>
                    <option value="hard">High School Level (Grades 9-12)</option>
                </select>
            </div>
            
            <div class="control-group">
                <label for="lang-select">🌐 Language:</label>
                <select id="lang-select" onchange="updateDisplay()">
                    <option value="en">English</option>
                    <option value="zh">Chinese (中文)</option>
                </select>
            </div>
        </div>
        
        <div class="content">
            {easy_en}
            {easy_zh}
            {medium_en}
            {medium_zh}
            {hard_en}
            {hard_zh}
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | 
            <a href="javascript:void(0)" style="color: #667eea;">Report Issue</a>
        </div>
    </div>
    
    <script>
        function updateDisplay() {{
            // Hide all content
            const allContent = document.querySelectorAll('.level-content');
            allContent.forEach(el => el.style.display = 'none');
            
            // Show selected
            const level = document.getElementById('level-select').value;
            const lang = document.getElementById('lang-select').value;
            const selected = document.getElementById(`level-${{level}}-${{lang}}`);
            
            if (selected) {{
                selected.style.display = 'block';
            }}
        }}
        
        // Show default on load
        window.addEventListener('load', updateDisplay);
    </script>
</body>
</html>
"""
    return html

def main():
    """Main workflow"""
    print("=" * 70)
    print("🚀 INTERACTIVE 3-TIER CONTENT GENERATION")
    print("=" * 70)
    print()
    
    # Step 1: Initialize database
    print("Step 1: Initializing database...")
    if not init_db():
        return False
    
    # Step 2: Load article (article 1)
    print("\nStep 2: Loading article...")
    article = load_article(11)
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
    
    # Step 7: Generate interactive HTML
    print("\nStep 7: Generating interactive HTML...")
    html = generate_interactive_html(article, content_by_level, questions_by_level)
    with open('/Users/jidai/news/article_interactive.html', 'w') as f:
        f.write(html)
    print("✅ article_interactive.html created")
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Generated interactive article page")
    print("=" * 70)
    print("\n📂 View the interactive page:")
    print("   http://localhost:8000/article_interactive.html")
    print("\n💾 Data stored in database:")
    print(f"   Location: {DB_PATH}")
    print("   Tables: article_summaries, quiz_questions")
    print("\n")
    
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
