#!/usr/bin/env python3
"""
Generate original article view pages (article page 2).
Display the original article content with image, title, and formatted text.
"""

import sqlite3
import pathlib
from datetime import datetime

def get_article_data(article_id):
    """Get article data."""
    try:
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM articles WHERE id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        conn.close()
        
        return article
    except Exception as e:
        print(f"Error: {e}")
        return None

def read_article_content(content_file):
    """Read article content from file."""
    try:
        content_path = pathlib.Path(content_file)
        if content_path.exists():
            with open(content_path, 'r', encoding='utf-8') as f:
                return f.read()
    except:
        pass
    return None

def generate_original_page(article_id, output_dir='article_pages'):
    """Generate original article view page."""
    
    pathlib.Path(output_dir).mkdir(exist_ok=True)
    
    article = get_article_data(article_id)
    if not article:
        print(f"❌ Article {article_id} not found")
        return False
    
    # Read content
    content = ""
    if article['content_file']:
        content = read_article_content(article['content_file'])
        if not content:
            content = article['snippet'] or "Content not available"
    else:
        content = article['snippet'] or "Content not available"
    
    # Format content - split into paragraphs
    paragraphs = content.split('\n\n') if content else ["Content not available"]
    formatted_content = ""
    for para in paragraphs:
        if para.strip():
            formatted_content += f"<p>{para.strip()}</p>\n"
    
    # Determine image path
    image_path = ""
    if article['image_file']:
        # Try to use the image file
        image_file = pathlib.Path(article['image_file'])
        if image_file.exists():
            image_path = f"../{article['image_file']}"  # Relative path from article_pages folder
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']} - Original Article</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Georgia', 'Segoe UI', serif;
            background: #f5f5f5;
            line-height: 1.8;
            color: #333;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
        }}
        
        .breadcrumb {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        .breadcrumb a {{
            color: white;
            text-decoration: none;
            transition: opacity 0.2s ease;
        }}
        
        .breadcrumb a:hover {{
            opacity: 0.7;
        }}
        
        .title {{
            font-size: 2.2em;
            margin-bottom: 15px;
            line-height: 1.3;
            font-weight: 700;
        }}
        
        .meta {{
            font-size: 0.95em;
            opacity: 0.9;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .meta span {{
            display: inline-block;
        }}
        
        .featured-image {{
            width: 100%;
            max-height: 400px;
            object-fit: cover;
        }}
        
        .article-content {{
            padding: 40px 30px;
        }}
        
        .article-content p {{
            margin-bottom: 20px;
            text-align: justify;
            line-height: 1.9;
            font-size: 1.05em;
        }}
        
        .article-content p:first-letter {{
            font-weight: bold;
        }}
        
        .nav-buttons {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        
        .nav-btn {{
            padding: 12px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .nav-btn:hover {{
            background: #764ba2;
            transform: translateY(-2px);
        }}
        
        .nav-btn.secondary {{
            background: #f0f0f0;
            color: #333;
            border: 1px solid #ddd;
        }}
        
        .nav-btn.secondary:hover {{
            background: #e0e0e0;
            color: #333;
        }}
        
        .info-box {{
            background: #f8f9ff;
            padding: 20px;
            border-left: 5px solid #667eea;
            border-radius: 4px;
            margin-bottom: 30px;
        }}
        
        .info-box strong {{
            color: #667eea;
        }}
        
        .info-box a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .info-box a:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            background: #f5f5f5;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
        }}
        
        .footer-nav {{
            margin-top: 20px;
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .footer-nav a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .footer-nav a:hover {{
            text-decoration: underline;
        }}
        
        .reading-time {{
            color: #999;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                padding: 30px 20px;
            }}
            
            .title {{
                font-size: 1.6em;
            }}
            
            .article-content {{
                padding: 20px;
            }}
            
            .article-content p {{
                font-size: 1em;
            }}
            
            .nav-buttons {{
                flex-direction: column;
            }}
            
            .nav-btn {{
                width: 100%;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="breadcrumb">
                <a href="article_{article_id}.html">← Back to Analysis</a>
                <span style="opacity: 0.7;">/ Original Article</span>
            </div>
            
            <h1 class="title">{article['title']}</h1>
            
            <div class="meta">
                <span>📅 {article['date_iso']}</span>
                <span>📰 {article['source']}</span>
                <span class="reading-time">⏱️ ~5 min read</span>
            </div>
        </div>
        
        """
    
    # Add featured image if available
    if image_path:
        html += f"""
        <img src="{image_path}" alt="{article['title']}" class="featured-image" onerror="this.style.display='none'">
        
        """
    
    html += f"""
        <div class="article-content">
            <div class="nav-buttons">
                <button class="nav-btn secondary" onclick="window.history.back()">← Back</button>
                <button class="nav-btn" onclick="window.open('article_{article_id}.html', '_blank')">
                    📊 View Analysis & Questions
                </button>
            </div>
            
            <div class="info-box">
                <strong>📰 Original Source:</strong> {article['source']}<br>
                <strong>🔗 Link:</strong> 
                {f'<a href="{article['link']}" target="_blank">Read on {article['source']}</a>' if article['link'] else 'Not available'}
            </div>
            
            <h2 style="color: #667eea; margin-bottom: 20px; font-size: 1.3em;">Full Article Content</h2>
            
            {formatted_content}
        </div>
        
        <div class="footer">
            <p><strong>📖 Reading Original Content</strong></p>
            <p style="margin: 15px 0;">This is the original article content displayed for reference. For enhanced learning with AI-generated analysis, questions, and discussion prompts, <a href="article_{article_id}.html" style="color: #667eea; font-weight: 600;">click here to view the analysis page</a>.</p>
            
            <div class="footer-nav">
                <a href="article_{article_id}.html">← Back to Analysis</a>
                <span style="color: #ccc;">|</span>
                <a href="../main_articles_interface.html">📰 All Articles</a>
            </div>
            
            <p style="margin-top: 20px; color: #999;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Article #{article_id}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write file
    output_path = pathlib.Path(output_dir) / f'article_{article_id}_original.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test with article 6
        success = generate_original_page(6)
        if success:
            print("\n✅ Test complete! Open: http://localhost:8000/article_pages/article_6_original.html")
    else:
        # Generate for all articles
        conn = sqlite3.connect('/Users/jidai/news/articles.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM articles')
        all_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if all_ids:
            for article_id in all_ids:
                generate_original_page(article_id)
            print(f"\n✅ Generated {len(all_ids)} original content pages!")
        else:
            print("⚠️  No articles found.")
