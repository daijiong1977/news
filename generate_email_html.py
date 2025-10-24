#!/usr/bin/env python3
"""
Generate HTML email from combined email payload.
Creates separate sections for each difficulty level with articles and images.
"""

import json
from pathlib import Path
from datetime import datetime

def generate_email_html(payload_file: str, output_file: str = None):
    """Generate HTML email from payload."""
    
    with open(payload_file) as f:
        payload = json.load(f)
    
    if not output_file:
        output_file = payload_file.replace('.json', '.html')
    
    server_domain = payload.get('server_domain', 'http://localhost:8000')
    image_base_path = payload.get('image_base_path', '/api/images')
    levels = payload.get('levels', {})
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Digest - Multi-Level Educational Content</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .email-container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .level-section {{
            padding: 30px 20px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .level-section:last-child {{
            border-bottom: none;
        }}
        
        .level-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 25px;
            font-size: 22px;
            font-weight: bold;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 0 0 25px 0;
        }}
        
        .level-easy .level-title {{
            background-color: #10b981;
        }}
        
        .level-mid .level-title {{
            background-color: #3b82f6;
        }}
        
        .level-hard .level-title {{
            background-color: #f59e0b;
        }}
        
        .level-cn .level-title {{
            background-color: #ef4444;
        }}
        
        .article {{
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .article-header {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }}
        
        .article-image {{
            flex-shrink: 0;
        }}
        
        .article-image img {{
            width: 150px;
            height: 150px;
            object-fit: cover;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .article-content {{
            flex: 1;
        }}
        
        .article-title {{
            font-size: 18px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        
        .article-id {{
            display: inline-block;
            background-color: #e5e7eb;
            color: #4b5563;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        
        .article-summary {{
            color: #4b5563;
            font-size: 14px;
            line-height: 1.6;
            text-align: justify;
        }}
        
        .footer {{
            background-color: #f3f4f6;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        .generated-time {{
            font-size: 12px;
            color: #9ca3af;
        }}
        
        @media (max-width: 600px) {{
            .article-header {{
                flex-direction: column;
            }}
            
            .article-image img {{
                width: 100%;
                height: auto;
            }}
            
            .level-section {{
                padding: 20px 15px;
            }}
            
            .header h1 {{
                font-size: 22px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>📚 News Digest</h1>
            <p>Multi-Level Educational Content</p>
        </div>
"""
    
    # Generate sections for each level
    level_info = {
        'easy': ('🟢 Easy Level', 'Beginner-Friendly Content', 'level-easy'),
        'mid': ('🔵 Mid Level', 'Intermediate Content', 'level-mid'),
        'hard': ('🟠 Hard Level', 'Expert-Level Content', 'level-hard'),
        'CN': ('🔴 中文版本', 'Chinese Translation', 'level-cn')
    }
    
    for level_key, (emoji_title, description, css_class) in level_info.items():
        articles = levels.get(level_key, [])
        
        if not articles:
            continue
        
        html += f"""        <div class="level-section {css_class}">
            <div class="level-title">{emoji_title}</div>
            <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">{description}</p>
"""
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No Title')
            summary = article.get('summary', 'No Summary')
            article_id = article.get('article_id', 'N/A')
            image = article.get('image', {})
            image_name = image.get('image_name', '')
            server_url = image.get('server_url', '')
            
            # Truncate summary for preview (max 300 chars)
            summary_preview = summary[:300] + '...' if len(summary) > 300 else summary
            
            html += f"""            <div class="article">
                <div class="article-id">Article #{article_id}</div>
"""
            
            if image_name and server_url:
                html += f"""                <div class="article-header">
                    <div class="article-image">
                        <img src="{server_url}" alt="{title}" loading="lazy">
                    </div>
                    <div class="article-content">
                        <div class="article-title">{title}</div>
                        <div class="article-summary">{summary_preview}</div>
                    </div>
                </div>
"""
            else:
                html += f"""                <div class="article-content">
                    <div class="article-title">{title}</div>
                    <div class="article-summary">{summary_preview}</div>
                </div>
"""
            
            html += """            </div>
"""
        
        html += """        </div>
"""
    
    # Footer
    generated_at = payload.get('generated_at', datetime.now().isoformat())
    html += f"""        <div class="footer">
            <p><strong>📧 News Digest - Multi-Level Content</strong></p>
            <p>This email contains articles at different complexity levels (Easy, Mid, Hard) and Chinese translation.</p>
            <p>Use the level that matches your reading preference or language.</p>
            <p class="generated-time">Generated: {generated_at}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Email HTML generated: {output_file}")
    
    # Count statistics
    total_articles = 0
    for level in ['easy', 'mid', 'hard', 'CN']:
        count = len(levels.get(level, []))
        if count > 0:
            total_articles += count
            print(f"  {level}: {count} articles")
    
    return output_file

if __name__ == "__main__":
    import sys
    
    payload_file = "payloads/email_combined_payload.json"
    output_file = "email_output.html"
    
    if len(sys.argv) > 1:
        payload_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    generate_email_html(payload_file, output_file)
