#!/usr/bin/env python3
"""Generate individual HTML pages for each analyzed article."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_FILE = "articles.db"

def get_article_data(article_id: int) -> dict:
    """Get article and analysis data."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get article base data
    cursor.execute("SELECT id, title, date_iso, image_file, snippet, link, source FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    # Gather summaries (grouped by language, difficulty)
    cursor.execute("SELECT language_id, difficulty_id, title, summary FROM article_summaries WHERE article_id = ?", (article_id,))
    summaries = cursor.fetchall()
    # Build simplified summary object (choose English summary for summary_en, Chinese for summary_zh when available)
    summary_en = None
    summary_zh = None
    summaries_list = []
    for s in summaries:
        summaries_list.append(dict(s))
        if s['language_id'] == 1 and not summary_en:
            summary_en = s['summary']
        if s['language_id'] == 2 and not summary_zh:
            summary_zh = s['summary']

    # Keywords
    cursor.execute("SELECT word, explanation FROM keywords WHERE article_id = ?", (article_id,))
    keywords = [dict(row) for row in cursor.fetchall()]

    # Background reading (concatenate per difficulty)
    cursor.execute("SELECT background_text FROM background_read WHERE article_id = ?", (article_id,))
    background_texts = [r[0] for r in cursor.fetchall()]
    background_reading = "\n\n".join(background_texts) if background_texts else None

    # Quiz questions - read from normalized questions + choices
    cursor.execute("SELECT question_id, question_text, difficulty_id FROM questions WHERE article_id = ? ORDER BY question_id", (article_id,))
    qrows = cursor.fetchall()
    quiz_questions = []
    for q in qrows:
        qid = q[0]
        qtext = q[1]
        # fetch choices
        cursor.execute("SELECT choice_text, is_correct, explanation FROM choices WHERE question_id = ? ORDER BY choice_id", (qid,))
        choices = cursor.fetchall()
        options = [c[0] for c in choices]
        correct = None
        explanation = None
        for c in choices:
            if c[1]:
                correct = chr(65 + choices.index(c))
                explanation = c[2]
                break

        quiz_questions.append(json.dumps({
            'id': qid,
            'question': qtext,
            'type': None,
            'options': options,
            'correct_answer': correct,
            'explanation': explanation
        }))

    # Discussion/perspectives (comments table)
    cursor.execute("SELECT attitude, com_content, who_comment FROM comments WHERE article_id = ? ORDER BY comment_id", (article_id,))
    comments = [dict(r) for r in cursor.fetchall()]

    conn.close()

    data = {
        'id': row['id'],
        'title': row['title'],
        'date': row['date_iso'],
        'image': row['image_file'],
        'snippet': row['snippet'],
        'link': row['link'],
        'source': row['source'],
        'summary_en': summary_en,
        'summary_zh': summary_zh,
        'key_words': keywords,
        'background_reading': background_reading,
        'questions_all': [json.loads(q) for q in quiz_questions],
        'discussion': {'comments': comments},
    }
    
    return data

def filter_high_frequency_keywords(keywords: list) -> list:
    """Filter keywords to only show frequency >= 3."""
    return [kw for kw in keywords if kw.get('frequency', 1) >= 3]

def generate_article_page(article_id: int) -> str:
    """Generate HTML page for an article with full AI analysis."""
    
    data = get_article_data(article_id)
    if not data:
        return f"<h1>Article {article_id} not found</h1>"
    
    # Filter keywords - only frequency 3+
    keywords = filter_high_frequency_keywords(data['key_words'])
    if not keywords:
        keywords = data['key_words'][:3]  # Fallback to top 3
    
    # Select 5 random questions from 10
    import random
    questions_selected = random.sample(data['questions_all'], min(5, len(data['questions_all'])))
    
    # Build keyword cards HTML
    keywords_html = ""
    for kw in keywords:
        keywords_html += f'''
                <div class="keyword-card">
                    <div class="keyword-word">{kw.get('word', 'N/A')}</div>
                    <div class="keyword-explanation">{kw.get('explanation', '')}</div>
                </div>
        '''
    
    # Build quiz questions HTML
    questions_html = ""
    for i, q in enumerate(questions_selected, 1):
        options = q.get('options', ['', '', '', ''])
        options_html = ""
        for j, option in enumerate(options):
            letter = chr(65 + j)  # A, B, C, D
            options_html += f'''
                            <div class="quiz-option">
                                <input type="radio" id="q{i}{letter}" name="q{i}" value="{letter}">
                                <label for="q{i}{letter}">{option}</label>
                            </div>
            '''
        
        questions_html += f'''
                    <div class="quiz-question">
                        <div class="quiz-question-number">Question {i} of 5</div>
                        <div class="quiz-question-text">{q.get('question', '')}</div>
                        <div class="quiz-options">
                            {options_html}
                        </div>
                    </div>
        '''
    
    # Build discussion HTML
    discussion = data['discussion']
    p1 = discussion.get('perspective_1', {})
    p2 = discussion.get('perspective_2', {})
    synthesis = discussion.get('synthesis', '')
    
    perspective_html = f'''
                    <div class="perspective">
                        <h3>✅ {p1.get('title', 'Perspective 1')}</h3>
                        <ul>
    '''
    for arg in p1.get('arguments', []):
        perspective_html += f'<li>{arg}</li>'
    
    perspective_html += '''
                        </ul>
                    </div>

                    <div class="perspective">
                        <h3>🤔 {title}</h3>
                        <ul>
    '''.replace('{title}', p2.get('title', 'Perspective 2'))
    
    for arg in p2.get('arguments', []):
        perspective_html += f'<li>{arg}</li>'
    
    perspective_html += '''
                        </ul>
                    </div>
    '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']} - Article Analysis</title>
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
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .header-content {{
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 30px;
            align-items: start;
        }}

        .header h1 {{
            font-size: 2.2em;
            color: #2c3e50;
            margin-bottom: 15px;
            line-height: 1.3;
        }}

        .header-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            font-size: 0.95em;
            color: #7f8c8d;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .header-image {{
            width: 300px;
            height: 200px;
            border-radius: 8px;
            object-fit: cover;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .header-snippet {{
            color: #555;
            line-height: 1.6;
            font-style: italic;
            padding: 15px;
            background: rgba(0,0,0,0.02);
            border-left: 4px solid #667eea;
            border-radius: 4px;
            margin-bottom: 20px;
        }}

        .lang-toggle {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}

        .lang-btn {{
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .lang-btn.active {{
            background: #667eea;
            color: white;
        }}

        .section {{
            background: white;
            padding: 40px;
            margin-bottom: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .section-title {{
            font-size: 1.5em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title::before {{
            content: '';
            width: 8px;
            height: 30px;
            background: #667eea;
            border-radius: 4px;
        }}

        .summary-text {{
            line-height: 2;
            color: #333;
            font-size: 1.15em;
            text-align: justify;
            font-weight: 500;
        }}

        .keywords-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }}

        .keyword-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}

        .keyword-word {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .keyword-explanation {{
            font-size: 0.9em;
            line-height: 1.4;
            opacity: 0.95;
        }}

        .background-box {{
            background: #f8f9ff;
            padding: 25px;
            border-left: 5px solid #667eea;
            border-radius: 8px;
            line-height: 1.9;
            color: #333;
            font-size: 1.1em;
            font-weight: 500;
        }}

        .quiz-question {{
            background: #f8f9ff;
            padding: 25px;
            border-radius: 8px;
            border-left: 5px solid #667eea;
            margin-bottom: 30px;
        }}

        .quiz-question-number {{
            font-size: 0.9em;
            color: #667eea;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .quiz-question-text {{
            font-size: 1.1em;
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        .quiz-options {{
            display: grid;
            gap: 12px;
        }}

        .quiz-option {{
            display: flex;
            align-items: center;
            padding: 12px;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .quiz-option:hover {{
            background: #f0f4ff;
            border-color: #667eea;
        }}

        .quiz-option input[type="radio"] {{
            margin-right: 15px;
            cursor: pointer;
            accent-color: #667eea;
        }}

        .quiz-option label {{
            flex: 1;
            cursor: pointer;
        }}

        .discussion-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .perspective {{
            background: #f8f9ff;
            padding: 25px;
            border-radius: 8px;
            border-top: 4px solid #667eea;
        }}

        .perspective h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}

        .perspective ul {{
            margin-left: 20px;
            line-height: 1.8;
            color: #555;
        }}

        .perspective li {{
            margin-bottom: 10px;
        }}

        .synthesis-box {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 25px;
            border-radius: 8px;
            border-left: 5px solid #667eea;
            line-height: 1.8;
            color: #555;
        }}

        .btn {{
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .btn-submit {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}

        .btn-submit:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}

        @media (max-width: 768px) {{
            .header-content {{
                grid-template-columns: 1fr;
            }}
            .header-image {{
                width: 100%;
            }}
            .discussion-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER WITH AI SUMMARY ON TOP -->
        <div class="header">
            <h1>{data['title']}</h1>
            <div class="header-meta">
                <div class="meta-item">📅 {data['date'][:10]}</div>
                <div class="meta-item">📰 {data['source']}</div>
                <div class="meta-item"><a href="{data['link']}" target="_blank" style="color: #667eea;">🔗 Read Original</a></div>
            </div>
            <p class="header-snippet">{data['snippet']}</p>
            <div class="lang-toggle">
                <button class="lang-btn active" onclick="showLanguage('en')">English Summary</button>
                <button class="lang-btn" onclick="showLanguage('zh')">中文摘要</button>
            </div>
        </div>

        <!-- SUMMARY SECTION -->
        <div class="section">
            <div class="section-title">📖 AI-Generated Summary</div>
            <div id="summary-en" class="summary-text">
                {data['summary_en']}
            </div>
            <div id="summary-zh" class="summary-text" style="display: none;">
                {data['summary_zh']}
            </div>
        </div>

        <!-- KEYWORDS SECTION -->
        <div class="section">
            <div class="section-title">🔑 Key Terms & Concepts</div>
            <div class="keywords-grid">
                {keywords_html}
            </div>
        </div>

        <!-- BACKGROUND READING -->
        <div class="section">
            <div class="section-title">📚 Background Reading</div>
            <div class="background-box">
                {data['background_reading']}
            </div>
        </div>

        <!-- QUIZ SECTION -->
        <div class="section">
            <div class="section-title">❓ Test Your Understanding</div>
            <form id="quiz-form">
                {questions_html}
                <div style="text-align: center; margin-top: 40px;">
                    <button type="button" class="btn btn-submit" onclick="submitQuiz()">Check Answers</button>
                </div>
            </form>
            <div id="results-section" style="display: none; margin-top: 30px; background: #f8f9ff; padding: 25px; border-radius: 8px; border-left: 5px solid #667eea;">
                <h3 style="color: #2c3e50; margin-bottom: 15px;">📊 Your Score</h3>
                <div id="score-display"></div>
            </div>
        </div>

        <!-- DISCUSSION SECTION -->
        <div class="section">
            <div class="section-title">⚖️ Two-Sided Discussion</div>
            <div class="discussion-grid">
                {perspective_html}
            </div>
            <div class="synthesis-box">
                <strong>🔄 Synthesis:</strong><br><br>
                {synthesis}
            </div>
        </div>
    </div>

    <script>
        const correctAnswers = {{
            {', '.join([f'"q{i}": "{q.get("correct_answer", "A")}"' for i, q in enumerate(questions_selected, 1)])}
        }};

        function showLanguage(lang) {{
            document.getElementById('summary-en').style.display = lang === 'en' ? 'block' : 'none';
            document.getElementById('summary-zh').style.display = lang === 'zh' ? 'block' : 'none';
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}

        function submitQuiz() {{
            let correct = 0;
            let answered = 0;
            const results = [];

            for (let i = 1; i <= 5; i++) {{
                const selected = document.querySelector(`input[name="q${{i}}"]:checked`);
                if (selected) {{
                    answered++;
                    const isCorrect = selected.value === correctAnswers[`q${{i}}`];
                    if (isCorrect) correct++;
                    results.push({{
                        question: i,
                        selected: selected.value,
                        correct: correctAnswers[`q${{i}}`],
                        isCorrect: isCorrect
                    }});
                }}
            }}

            if (answered < 5) {{
                alert('Please answer all questions first!');
                return;
            }}

            const percentage = (correct / 5) * 100;
            let resultHTML = `<strong>Score: ${{Math.round(percentage)}}%</strong>`;
            
            if (percentage === 100) {{
                resultHTML += ' 🎉 Perfect!';
            }} else if (percentage >= 80) {{
                resultHTML += ' 👍 Good Job!';
            }} else {{
                resultHTML += ' 📚 Keep Learning!';
            }}

            resultHTML += '<div style="margin-top: 15px;">';
            results.forEach(r => {{
                resultHTML += `<div style="padding: 10px; margin: 10px 0; background: ${{r.isCorrect ? '#d4edda' : '#f8d7da'}}; border-radius: 4px;">
                    Q${{r.question}}: ${{r.isCorrect ? '✅' : '❌'}}
                </div>`;
            }});
            resultHTML += '</div>';

            document.getElementById('score-display').innerHTML = resultHTML;
            document.getElementById('results-section').style.display = 'block';
        }}
    </script>
</body>
</html>
'''
    
    return html

def generate_all_article_pages():
    """Generate HTML pages for all analyzed articles."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE deepseek_processed = 1 ORDER BY id")
    article_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    pages_dir = Path("article_pages")
    pages_dir.mkdir(exist_ok=True)
    
    for article_id in article_ids:
        html = generate_article_page(article_id)
        output_file = pages_dir / f"article_{article_id}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ Generated: {output_file}")
    
    print(f"\n✓ Generated {len(article_ids)} article pages in 'article_pages/' directory")

if __name__ == "__main__":
    generate_all_article_pages()
