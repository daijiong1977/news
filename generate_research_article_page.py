#!/usr/bin/env python3
"""
Generate enhanced article detail pages based on research feedback.
Incorporates academic context, research keywords, cognitive levels, and critical analysis.
"""

import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime

def get_article_and_research_data(article_id):
    """Get article data along with research feedback."""
    try:
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get article data
        cursor.execute('''
            SELECT a.*, df.summary_en, df.summary_zh, df.key_words, 
                   df.background_reading, df.multiple_choice_questions,
                   df.discussion_both_sides
            FROM articles a
            LEFT JOIN deepseek_feedback df ON a.id = df.article_id
            WHERE a.id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        if not article:
            print(f"❌ Article {article_id} not found")
            return None
        
        # Get quiz questions with cognitive levels if available
        cursor.execute('''
            SELECT * FROM quiz_questions 
            WHERE article_id = ?
            ORDER BY question_number
        ''', (article_id,))
        
        questions = cursor.fetchall()
        conn.close()
        
        return {
            'article': article,
            'questions': questions
        }
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def load_research_feedback():
    """Load research feedback from JSON file."""
    try:
        with open('/Users/jidai/news/deepseek_research_batch_1.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load research feedback: {e}")
        return None

def get_cognitive_level_badge(level):
    """Return HTML badge for cognitive level."""
    badges = {
        'remember': '#E8F4F8',
        'understand': '#D0E8F2',
        'comprehension': '#D0E8F2',
        'apply': '#B8DCEB',
        'application': '#B8DCEB',
        'analyze': '#9FC9E0',
        'analysis': '#9FC9E0',
        'evaluate': '#86B5D5',
        'evaluation': '#86B5D5',
        'create': '#6DA0C9',
        'synthesis': '#6DA0C9',
    }
    
    level_lower = level.lower() if level else 'understand'
    color = badges.get(level_lower, '#90C9E1')
    
    return f'<span class="cognitive-badge" style="background-color: {color}">{level}</span>'

def generate_research_page(article_id, output_dir='article_pages'):
    """Generate an enhanced research-focused article page."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Get data
    data = get_article_and_research_data(article_id)
    if not data:
        return False
    
    research_feedback = load_research_feedback()
    article = data['article']
    questions = data['questions']
    
    # Parse stored data
    summary_en = article['summary_en'] or "Summary not available"
    summary_zh = article['summary_zh'] or "摘要不可用"
    
    try:
        keywords_data = json.loads(article['key_words']) if article['key_words'] else []
    except:
        keywords_data = []
    
    # Filter keywords by frequency >= 3
    filtered_keywords = [kw for kw in keywords_data if isinstance(kw, dict) and kw.get('frequency', 1) >= 3]
    if not filtered_keywords and keywords_data:
        filtered_keywords = keywords_data[:3]
    
    # Select 5 random questions from available questions
    selected_questions = random.sample(list(questions), min(5, len(questions))) if questions else []
    selected_questions.sort(key=lambda q: q['question_number'])
    
    try:
        discussion_data = json.loads(article['discussion_both_sides']) if article['discussion_both_sides'] else {}
    except:
        discussion_data = {}
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']} - Research Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.2em;
            margin-bottom: 10px;
            line-height: 1.2;
        }}
        
        .meta {{
            font-size: 0.95em;
            opacity: 0.9;
            margin-top: 15px;
        }}
        
        .meta span {{
            margin: 0 15px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.6em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: inline-block;
        }}
        
        .language-toggle {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .toggle-btn {{
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .toggle-btn.active {{
            background: #667eea;
            color: white;
        }}
        
        .summary-box {{
            background: #f8f9ff;
            padding: 25px;
            border-left: 5px solid #667eea;
            border-radius: 8px;
            line-height: 1.8;
            font-size: 1.05em;
            color: #333;
        }}
        
        .summary-box.hidden {{
            display: none;
        }}
        
        .research-keywords {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .keyword-card {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border: 2px solid #667eea40;
            padding: 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }}
        
        .keyword-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
            border-color: #667eea;
        }}
        
        .keyword-card h4 {{
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 8px;
        }}
        
        .keyword-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: #667eea;
            color: white;
            border-radius: 12px;
            font-size: 0.85em;
            margin-bottom: 10px;
        }}
        
        .keyword-card p {{
            font-size: 0.95em;
            color: #555;
            line-height: 1.6;
        }}
        
        .research-context {{
            background: #f0f4ff;
            padding: 25px;
            border-left: 5px solid #764ba2;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .research-context h4 {{
            color: #764ba2;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .research-context p {{
            color: #555;
            line-height: 1.7;
            font-size: 0.95em;
        }}
        
        .critical-analysis {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .analysis-box {{
            background: #fff9f0;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ff9800;
        }}
        
        .analysis-box.limitations {{
            background: #fff3e0;
            border-left-color: #ff6f00;
        }}
        
        .analysis-box h4 {{
            color: #ff9800;
            margin-bottom: 12px;
            font-size: 1.1em;
        }}
        
        .analysis-box.limitations h4 {{
            color: #ff6f00;
        }}
        
        .analysis-box ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .analysis-box li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
            color: #555;
            font-size: 0.95em;
        }}
        
        .analysis-box li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #ff9800;
            font-weight: bold;
        }}
        
        .analysis-box.limitations li:before {{
            content: "⚠";
            color: #ff6f00;
        }}
        
        .questions-grid {{
            display: grid;
            gap: 20px;
        }}
        
        .question-card {{
            background: #f9f9f9;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 25px;
            transition: all 0.3s ease;
        }}
        
        .question-card:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }}
        
        .question-card h4 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .question-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .cognitive-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            color: white;
            font-weight: 600;
        }}
        
        .option {{
            padding: 12px;
            margin: 10px 0;
            background: #f0f0f0;
            border-radius: 6px;
            border-left: 4px solid #ddd;
        }}
        
        .option.correct {{
            background: #e8f5e9;
            border-left-color: #4caf50;
        }}
        
        .option-label {{
            font-weight: bold;
            color: #555;
        }}
        
        .discussion {{
            background: #f5f5f5;
            padding: 25px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        
        .discussion h4 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        
        .side {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 6px;
        }}
        
        .side h5 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1em;
        }}
        
        .side p {{
            color: #555;
            line-height: 1.6;
            font-size: 0.95em;
        }}
        
        .footer {{
            background: #f8f9f9;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}
        
        .back-button {{
            display: inline-block;
            margin-bottom: 20px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .back-button:hover {{
            background: #764ba2;
            transform: translateX(-5px);
        }}
        
        @media (max-width: 768px) {{
            .critical-analysis {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 1.6em;
            }}
            
            .section-title {{
                font-size: 1.3em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{article['title']}</h1>
            <div class="meta">
                <span>📅 {article['date_iso']}</span>
                <span>📰 {article['source']}</span>
            </div>
        </div>
        
        <div class="content">
            <button class="back-button" onclick="window.history.back()">← Back to Article List</button>
            
            <!-- Summary Section -->
            <div class="section">
                <div class="section-title">📋 Research Summary</div>
                <div class="language-toggle">
                    <button class="toggle-btn active" onclick="showLanguage('en')">English</button>
                    <button class="toggle-btn" onclick="showLanguage('zh')">中文</button>
                </div>
                <div class="summary-box" id="summary-en">
                    {summary_en}
                </div>
                <div class="summary-box hidden" id="summary-zh">
                    {summary_zh}
                </div>
            </div>
            
            <!-- Research Keywords Section -->
            <div class="section">
                <div class="section-title">🔬 Research Keywords</div>
                <div class="research-keywords">
"""
    
    # Add research keywords
    if research_feedback and 'research_keywords' in research_feedback:
        for kw in research_feedback['research_keywords'][:6]:
            html += f"""
                    <div class="keyword-card">
                        <h4>{kw['keyword']}</h4>
                        <span class="keyword-badge">Frequency: {kw['frequency']}</span>
                        <p>{kw['research_context']}</p>
                    </div>
"""
    elif filtered_keywords:
        for kw in filtered_keywords[:6]:
            kw_name = kw.get('word', kw) if isinstance(kw, dict) else kw
            html += f"""
                    <div class="keyword-card">
                        <h4>{kw_name}</h4>
                        <p><em>Frequency: {kw.get('frequency', 1)}</em></p>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <!-- Research Context Section -->
            <div class="section">
                <div class="section-title">🎓 Research Context</div>
"""
    
    if research_feedback and 'research_context' in research_feedback:
        html += f"""
                <div class="research-context">
                    <p>{research_feedback['research_context']}</p>
                </div>
"""
    elif article['background_reading']:
        html += f"""
                <div class="research-context">
                    <p>{article['background_reading']}</p>
                </div>
"""
    
    # Critical Analysis Section
    html += """
            </div>
            
            <div class="section">
                <div class="section-title">📊 Critical Analysis</div>
                <div class="critical-analysis">
"""
    
    if research_feedback and 'critical_analysis' in research_feedback:
        analysis = research_feedback['critical_analysis']
        
        html += """
                    <div class="analysis-box">
                        <h4>✓ Strengths</h4>
                        <ul>
"""
        for strength in analysis.get('strengths', []):
            html += f"                            <li>{strength}</li>\n"
        
        html += """
                        </ul>
                    </div>
                    
                    <div class="analysis-box limitations">
                        <h4>⚠ Limitations</h4>
                        <ul>
"""
        for limitation in analysis.get('limitations', []):
            html += f"                            <li>{limitation}</li>\n"
        
        html += """
                        </ul>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <!-- Questions Section -->
            <div class="section">
                <div class="section-title">❓ Key Discussion Questions</div>
                <div class="questions-grid">
"""
    
    if selected_questions:
        for idx, q in enumerate(selected_questions, 1):
            cognitive_level = q['cognitive_level'] if 'cognitive_level' in q[0:] else 'Analysis'
            question_type = q['question_type'] if 'question_type' in q[0:] else 'general'
            
            html += f"""
                    <div class="question-card">
                        <h4>
                            <span class="question-number">{idx}</span>
                            {q['question_text']}
                        </h4>
                        <div style="margin-top: 15px;">
                            <strong>Question Type:</strong> {question_type.upper()}
                        </div>
"""
            
            if 'option_a' in q[0:]:
                html += f"""
                        <div style="margin-top: 15px;">
                            <strong>Options:</strong>
                            <div class="option">
                                <span class="option-label">A:</span> {q['option_a']}
                            </div>
                            <div class="option">
                                <span class="option-label">B:</span> {q['option_b']}
                            </div>
                            <div class="option">
                                <span class="option-label">C:</span> {q['option_c']}
                            </div>
                            <div class="option">
                                <span class="option-label">D:</span> {q['option_d']}
                            </div>
                            <div class="option correct">
                                <span class="option-label">Correct Answer:</span> {q.get('correct_answer', 'N/A')}
                            </div>
                        </div>
"""
            
            if 'explanation' in q[0:] and q['explanation']:
                html += f"""
                        <div style="margin-top: 15px; padding: 12px; background: #f0f8ff; border-radius: 6px; border-left: 4px solid #2196F3;">
                            <strong>💡 Explanation:</strong>
                            <p style="margin-top: 8px; color: #555;">{q['explanation']}</p>
                        </div>
"""
            
            html += """
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <!-- Two-Sided Discussion -->
            <div class="section">
                <div class="section-title">🤝 Two-Sided Discussion</div>
                <div class="discussion">
"""
    
    if discussion_data:
        if 'perspective_a' in discussion_data:
            html += f"""
                    <div class="side">
                        <h5>👁️ Perspective A</h5>
                        <p>{discussion_data['perspective_a']}</p>
                    </div>
"""
        if 'perspective_b' in discussion_data:
            html += f"""
                    <div class="side">
                        <h5>👁️ Perspective B</h5>
                        <p>{discussion_data['perspective_b']}</p>
                    </div>
"""
    else:
        html += """
                    <p style="color: #999;">No discussion perspectives available yet.</p>
"""
    
    html += """
                </div>
            </div>
            
            <!-- User Feedback Section -->
            <div class="section">
                <div class="section-title">💬 Your Analysis</div>
                <div style="background: #f5f5f5; padding: 25px; border-radius: 10px;">
                    <p style="margin-bottom: 15px; color: #666;">Share your own perspective or argument:</p>
                    <textarea id="userAnalysis" style="width: 100%; min-height: 120px; padding: 15px; border: 2px solid #ddd; border-radius: 6px; font-family: inherit; font-size: 0.95em; resize: vertical;"></textarea>
                    <button onclick="submitAnalysis()" style="margin-top: 15px; padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 1em;">Submit Your Analysis</button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>📄 Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Article ID: {article_id} | Research-Enhanced Version</p>
        </div>
    </div>
    
    <script>
        function showLanguage(lang) {{
            document.getElementById('summary-en').classList.toggle('hidden', lang !== 'en');
            document.getElementById('summary-zh').classList.toggle('hidden', lang !== 'zh');
            
            document.querySelectorAll('.toggle-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
        }}
        
        function submitAnalysis() {{
            const analysis = document.getElementById('userAnalysis').value;
            if (!analysis.trim()) {{
                alert('Please enter your analysis');
                return;
            }}
            alert('Your analysis has been recorded!\\nSubmitted: ' + analysis.substring(0, 50) + '...');
            document.getElementById('userAnalysis').value = '';
        }}
    </script>
</body>
</html>
"""
    
    # Write file
    output_path = Path(output_dir) / f'article_{article_id}_research.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test with article 7 (has research data)
        success = generate_research_page(7)
        if success:
            print(f"\n✅ Test complete! Open: http://localhost:8000/article_pages/article_7_research.html")
    else:
        # Generate for all processed articles
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM articles WHERE deepseek_processed = 1')
        processed_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if processed_ids:
            for article_id in processed_ids:
                generate_research_page(article_id)
            print(f"\n✅ Generated {len(processed_ids)} research pages!")
        else:
            print("⚠️  No processed articles found. Run deepseek_processor.py first.")
