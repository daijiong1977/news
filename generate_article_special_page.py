#!/usr/bin/env python3
"""
Generate article special pages with 3/5 keywords + 2/5 questions layout.
Side-by-side comparison of keywords and questions with background reading and discussion below.
"""

import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime

def get_article_data(article_id):
    """Get article and analysis data."""
    try:
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get core article data
        cursor.execute('SELECT id, title, date_iso, image_file, snippet, link, source, content_file FROM articles WHERE id = ?', (article_id,))
        article = cursor.fetchone()
        if not article:
            conn.close()
            return None

        # Get quiz questions from normalized tables
        cursor.execute('SELECT question_id, question_text, question_number FROM questions WHERE article_id = ? ORDER BY question_number', (article_id,))
        qrows = cursor.fetchall()
        questions = []
        for q in qrows:
            qid = q[0]
            qtext = q[1]
            qnum = q[2]
            cursor.execute('SELECT choice_text, is_correct FROM choices WHERE question_id = ? ORDER BY choice_id', (qid,))
            choices = cursor.fetchall()
            options = [c[0] for c in choices]
            questions.append({'question_id': qid, 'question_text': qtext, 'question_number': qnum, 'options': options})

        conn.close()
        return {'article': article, 'questions': questions}
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_article_page(article_id, output_dir='article_pages'):
    """Generate article special page with side-by-side layout."""
    
    Path(output_dir).mkdir(exist_ok=True)
    
    data = get_article_data(article_id)
    if not data:
        return False
    
    article = data['article']
    questions = data['questions']
    
    # Parse data
    summary_en = article['summary_en'] or "Summary not available"
    summary_zh = article['summary_zh'] or "摘要不可用"
    
    try:
        keywords_data = json.loads(article['key_words']) if article['key_words'] else []
    except:
        keywords_data = []
    
    # Filter keywords: frequency >= 3 only
    filtered_keywords = [kw for kw in keywords_data if isinstance(kw, dict) and kw.get('frequency', 1) >= 3]
    if not filtered_keywords and keywords_data:
        filtered_keywords = keywords_data[:3]
    
    # Select 5 random questions from available
    selected_questions = random.sample(list(questions), min(5, len(questions))) if questions else []
    selected_questions.sort(key=lambda q: q['question_number'])
    
    try:
        discussion_data = json.loads(article['discussion_both_sides']) if article['discussion_both_sides'] else {}
    except:
        discussion_data = {}
    
    # Get original content file path
    original_file = article['content_file'] if article['content_file'] else None
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']} - Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 15px;
            line-height: 1.3;
        }}
        
        .header-meta {{
            font-size: 0.95em;
            opacity: 0.9;
        }}
        
        .header-meta span {{
            margin: 0 10px;
        }}
        
        .nav {{
            background: white;
            padding: 15px 20px;
            border-bottom: 1px solid #ddd;
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .nav-btn {{
            padding: 10px 20px;
            background: #f0f0f0;
            color: #333;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
        }}
        
        .nav-btn:hover {{
            background: #667eea;
            color: white;
        }}
        
        .nav-btn.active {{
            background: #667eea;
            color: white;
        }}
        
        .content {{
            padding: 30px 20px;
        }}
        
        .summary-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .summary-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            align-items: center;
        }}
        
        .summary-label {{
            font-weight: 600;
            color: #333;
        }}
        
        .lang-toggle {{
            display: flex;
            gap: 5px;
        }}
        
        .lang-btn {{
            padding: 8px 15px;
            border: 2px solid #ddd;
            background: white;
            color: #333;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        
        .lang-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .summary-text {{
            font-size: 1.05em;
            line-height: 1.8;
            color: #333;
            display: none;
        }}
        
        .summary-text.active {{
            display: block;
        }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .keywords-section, .questions-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1.4em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: inline-block;
        }}
        
        .keyword-card {{
            background: #f8f9ff;
            padding: 18px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }}
        
        .keyword-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }}
        
        .keyword-card h4 {{
            color: #667eea;
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        
        .keyword-frequency {{
            display: inline-block;
            padding: 3px 8px;
            background: #667eea;
            color: white;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .keyword-text {{
            color: #555;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        
        .question-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
        }}
        
        .question-card:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }}
        
        .question-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 0.85em;
            margin-right: 10px;
        }}
        
        .question-text {{
            font-weight: 600;
            color: #333;
            margin-bottom: 12px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }}
        
        .question-type {{
            display: inline-block;
            padding: 3px 8px;
            background: #e8f4f8;
            color: #667eea;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .options {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            display: none;
        }}
        
        .options.visible {{
            display: block;
        }}
        
        .option {{
            padding: 8px;
            margin: 6px 0;
            background: #f0f0f0;
            border-radius: 4px;
            border-left: 3px solid #ddd;
        }}
        
        .option.correct {{
            background: #e8f5e9;
            border-left-color: #4caf50;
        }}
        
        .expand-btn {{
            background: none;
            border: none;
            color: #667eea;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9em;
            padding: 5px 0;
            margin-top: 10px;
        }}
        
        .expand-btn:hover {{
            text-decoration: underline;
        }}
        
        .below-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .background-section {{
            margin-bottom: 30px;
        }}
        
        .discussion-section {{
            margin-bottom: 30px;
        }}
        
        .perspective {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
        }}
        
        .perspective:nth-child(2) {{
            border-left-color: #764ba2;
        }}
        
        .perspective h4 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .perspective p {{
            color: #555;
            line-height: 1.7;
        }}
        
        .synthesis {{
            background: #f0f4ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #4caf50;
        }}
        
        .synthesis h4 {{
            color: #4caf50;
            margin-bottom: 10px;
        }}
        
        .synthesis p {{
            color: #555;
            line-height: 1.7;
        }}
        
        .links-section {{
            background: #fff3e0;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ff9800;
        }}
        
        .links-section h4 {{
            color: #ff9800;
            margin-bottom: 12px;
        }}
        
        .links-section a {{
            display: inline-block;
            margin-right: 15px;
            color: #ff9800;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        
        .links-section a:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
            background: white;
            border-top: 1px solid #ddd;
        }}
        
        @media (max-width: 1024px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.4em;
            }}
            
            .summary-controls {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .nav {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <div class="header-meta">
                <span>📅 {article['date_iso']}</span>
                <span>•</span>
                <span>📰 {article['source']}</span>
            </div>
        </div>
        
        <div class="nav">
            <button class="nav-btn active" onclick="scrollToSection('summary')">📋 Summary</button>
            <button class="nav-btn" onclick="scrollToSection('keywords-questions')">🔍 Analysis</button>
            <button class="nav-btn" onclick="scrollToSection('background')">📚 Background</button>
            <button class="nav-btn" onclick="scrollToSection('discussion')">💬 Discussion</button>
            <button class="nav-btn" onclick="window.open('{f'article_pages/article_{article_id}_original.html' if original_file else 'javascript:alert(\'Original content not available\')'}')" style="background: #f0ad4e; color: white;">📖 Original Article</button>
        </div>
        
        <div class="content">
            <!-- Summary Section -->
            <div class="summary-section" id="summary">
                <div class="summary-controls">
                    <span class="summary-label">📝 Summary:</span>
                    <div class="lang-toggle">
                        <button class="lang-btn active" onclick="setLanguage('en', this)">English</button>
                        <button class="lang-btn" onclick="setLanguage('zh', this)">中文</button>
                    </div>
                </div>
                
                <div class="summary-text active" id="summary-en">
                    {summary_en}
                </div>
                <div class="summary-text" id="summary-zh">
                    {summary_zh}
                </div>
            </div>
            
            <!-- Main Layout: Keywords + Questions -->
            <div class="main-layout" id="keywords-questions">
                <!-- Keywords Section (3/5 width) -->
                <div class="keywords-section">
                    <div class="section-title">🔑 Key Terms</div>
                    <div style="margin-top: 20px;">
"""
    
    # Add keywords
    for idx, kw in enumerate(filtered_keywords[:10], 1):
        if isinstance(kw, dict):
            html += f"""
                        <div class="keyword-card">
                            <h4>{kw.get('word', f'Keyword {idx}')}</h4>
                            <span class="keyword-frequency">Freq: {kw.get('frequency', 1)}</span>
                            <p class="keyword-text">{kw.get('explanation', '')}</p>
                        </div>
"""
    
    html += """
                    </div>
                </div>
                
                <!-- Questions Section (2/5 width) -->
                <div class="questions-section">
                    <div class="section-title">❓ Questions</div>
                    <div style="margin-top: 20px;">
"""
    
    # Add questions
    for idx, q in enumerate(selected_questions, 1):
        # Convert sqlite3.Row to dict for easier access
        q_dict = dict(q) if hasattr(q, 'keys') else q
        
        question_type = q_dict.get('question_type', 'general').upper() if isinstance(q_dict, dict) else 'GENERAL'
        
        html += f"""
                        <div class="question-card">
                            <div class="question-text">
                                <span class="question-number">{idx}</span>
                                <div>
                                    <strong>{q_dict['question_text']}</strong>
                                    <span class="question-type">{question_type}</span>
                                </div>
                            </div>
                            <button class="expand-btn" onclick="toggleOptions(this)">Show Options ▼</button>
                            <div class="options">
"""
        
        html += f"""
                                <div class="option">
                                    <strong>A:</strong> {q_dict.get('option_a', 'N/A')}
                                </div>
                                <div class="option">
                                    <strong>B:</strong> {q_dict.get('option_b', 'N/A')}
                                </div>
                                <div class="option">
                                    <strong>C:</strong> {q_dict.get('option_c', 'N/A')}
                                </div>
                                <div class="option">
                                    <strong>D:</strong> {q_dict.get('option_d', 'N/A')}
                                </div>
                                <div class="option correct">
                                    <strong>✓ Correct:</strong> {q_dict.get('correct_answer', 'N/A')}
                                </div>
"""
        
        if q_dict.get('explanation'):
            html += f"""
                                <div style="margin-top: 12px; padding: 12px; background: #e3f2fd; border-radius: 6px;">
                                    <strong>💡 Explanation:</strong> {q_dict['explanation']}
                                </div>
"""
        
        html += """
                            </div>
                        </div>
"""
    
    html += """
                    </div>
                </div>
            </div>
            
            <!-- Below Section -->
            <div class="below-section">
                <!-- Background Reading -->
                <div class="background-section" id="background">
                    <div class="section-title">📚 Background Reading</div>
                    <p style="margin-top: 20px; color: #555; line-height: 1.8;">
"""
    
    if article['background_reading']:
        html += article['background_reading']
    else:
        html += "Background information will be added soon."
    
    html += """
                    </p>
                </div>
                
                <!-- Two-Sided Discussion -->
                <div class="discussion-section" id="discussion">
                    <div class="section-title">💬 Two-Sided Discussion</div>
"""
    
    if discussion_data and isinstance(discussion_data, dict):
        # Handle both old and new format
        if 'perspective_1' in discussion_data:
            p1 = discussion_data['perspective_1']
            p2 = discussion_data['perspective_2']
            
            html += f"""
                    <div class="perspective">
                        <h4>👁️ {p1.get('title', 'Perspective A')}</h4>
                        <p>{' '.join(p1.get('arguments', []))}</p>
                    </div>
                    
                    <div class="perspective">
                        <h4>👁️ {p2.get('title', 'Perspective B')}</h4>
                        <p>{' '.join(p2.get('arguments', []))}</p>
                    </div>
"""
            
            if 'synthesis' in discussion_data:
                html += f"""
                    <div class="synthesis">
                        <h4>🔄 Synthesis</h4>
                        <p>{discussion_data['synthesis']}</p>
                    </div>
"""
        else:
            html += "<p style='color: #999;'>Discussion content will be added soon.</p>"
    else:
        html += "<p style='color: #999;'>Discussion content will be added soon.</p>"
    
    html += """
                </div>
                
                <!-- Links Section -->
                <div class="links-section" style="margin-top: 30px;">
                    <h4>🔗 Related Resources</h4>
"""
    
    if article['link']:
        html += f"""
                    <a href="{article['link']}" target="_blank">📰 Read Original Article</a>
"""
    
    html += f"""
                    <a href="#summary" onclick="document.querySelector('.summary-section').scrollIntoView({{behavior: 'smooth'}})">📋 Back to Summary</a>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Article #{article_id} | Enhanced Learning Platform</p>
        </div>
    </div>
    
    <script>
        function setLanguage(lang, btn) {{
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.getElementById('summary-en').classList.toggle('active', lang === 'en');
            document.getElementById('summary-zh').classList.toggle('active', lang === 'zh');
        }}
        
        function toggleOptions(btn) {{
            const options = btn.nextElementSibling;
            options.classList.toggle('visible');
            btn.textContent = options.classList.contains('visible') ? 'Hide Options ▲' : 'Show Options ▼';
        }}
        
        function scrollToSection(id) {{
            const element = document.getElementById(id);
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}
    </script>
</body>
</html>
"""
    
    # Write file
    output_path = Path(output_dir) / f'article_{article_id}.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test with article 6
        success = generate_article_page(6)
        if success:
            print("\n✅ Test complete! Open: http://localhost:8000/article_pages/article_6.html")
    else:
        # Generate for all processed articles
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM articles WHERE deepseek_processed = 1')
        processed_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if processed_ids:
            for article_id in processed_ids:
                generate_article_page(article_id)
            print(f"\n✅ Generated {len(processed_ids)} article pages!")
        else:
            print("⚠️  No processed articles found.")
