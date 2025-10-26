#!/usr/bin/env python3
"""
Generate unified article pages from Deepseek response JSON.
Combines all 4 article views (keywords, background, quiz, perspective) into single page.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def build_keywords_html(keywords: List[str]) -> str:
    """Build HTML for keywords section."""
    if not keywords:
        return "<p class='text-slate-600 dark:text-slate-400'>No keywords available.</p>"
    
    html_parts = []
    for keyword in keywords:
        if isinstance(keyword, dict):
            # Handle both 'title'/'description' and 'term'/'explanation' formats
            title = keyword.get('title', keyword.get('term', 'Keyword'))
            description = keyword.get('description', keyword.get('explanation', ''))
        else:
            title = str(keyword)
            description = ''
        
        html_parts.append(f"""            <div>
                <p class="font-bold text-slate-900 dark:text-white">{title}</p>
                <p class="text-sm text-slate-600 dark:text-slate-400">{description}</p>
            </div>""")
    
    return "\n".join(html_parts)


def build_quiz_html(questions: List[Dict[str, Any]]) -> str:
    """Build HTML for quiz section."""
    if not questions:
        return "<p class='text-slate-600 dark:text-slate-400'>No quiz questions available.</p>"
    
    html_parts = []
    for i, q in enumerate(questions, 1):
        question_text = q.get('question', f'Question {i}')
        options = q.get('options', [])
        
        html_parts.append(f"""            <div class="space-y-4">
                <p class="font-bold text-slate-900 dark:text-white">{i}. {question_text}</p>
                <div class="space-y-2">""")
        
        for option in options:
            option_text = option if isinstance(option, str) else str(option)
            html_parts.append(f"""                    <button class="w-full text-left p-3 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">{option_text}</button>""")
        
        html_parts.append("""                </div>
            </div>""")
    
    # Add score section
    html_parts.append("""            <div class="border-t border-slate-200 dark:border-white/10 pt-6 mt-6">
                <div class="flex items-center justify-between bg-slate-100 dark:bg-slate-800 p-4 rounded-lg">
                    <div>
                        <p class="font-bold text-slate-900 dark:text-white">Your Score</p>
                        <p class="text-2xl font-black text-positive">0/""" + str(len(questions)) + """ Correct</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <button class="flex items-center gap-2 cursor-pointer justify-center overflow-hidden rounded-lg h-10 px-4 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-bold leading-normal tracking-[0.015em] border border-slate-300 dark:border-slate-600 hover:bg-slate-50">
                            <span class="material-symbols-outlined text-base">refresh</span>
                            Retry
                        </button>
                        <button class="cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-5 bg-primary text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] flex hover:bg-primary/90">Submit</button>
                    </div>
                </div>
            </div>""")
    
    return "\n".join(html_parts)


def build_perspectives_html(perspectives: List[Dict[str, Any]]) -> str:
    """Build HTML for perspectives section."""
    if not perspectives:
        return "<p class='text-slate-600 dark:text-slate-400'>No perspectives available.</p>"
    
    html_parts = []
    
    for perspective in perspectives:
        # Handle both 'viewpoint'/'content' and 'perspective'/'description' formats
        viewpoint = perspective.get('viewpoint', perspective.get('perspective', 'Neutral'))
        content = perspective.get('content', perspective.get('description', ''))
        source = perspective.get('source', '')
        
        # Map viewpoint to icon and color
        icon_map = {
            'positive': ('thumb_up', 'positive'),
            'neutral': ('horizontal_rule', 'neutral'),
            'negative': ('thumb_down', 'negative'),
            'Positive': ('thumb_up', 'positive'),
            'Neutral': ('horizontal_rule', 'neutral'),
            'Negative': ('thumb_down', 'negative'),
            "Organizer's view": ('business', 'primary'),
            "Author's view": ('edit', 'primary'),
            "Children's view": ('child_care', 'primary'),
        }
        
        icon, color = icon_map.get(viewpoint, ('info', 'primary'))
        
        source_html = f"<p class='text-slate-500 dark:text-slate-400 text-xs font-normal leading-normal mt-auto pt-2'>Source: {source}</p>" if source else ""
        
        html_parts.append(f"""            <div class="flex flex-col gap-4 p-5 rounded-xl bg-white dark:bg-background-dark/50 shadow-sm border border-slate-200 dark:border-white/10">
                <div class="flex items-center gap-3">
                    <div class="flex items-center justify-center size-10 rounded-full bg-{color}/10 text-{color}">
                        <span class="material-symbols-outlined">{icon}</span>
                    </div>
                    <p class="text-slate-900 dark:text-white text-lg font-bold leading-normal font-display">{viewpoint}</p>
                </div>
                <p class="text-slate-600 dark:text-slate-300 text-sm font-normal leading-relaxed">
                    {content}
                </p>
                {source_html}
            </div>""")
    
    return "\n".join(html_parts)


def highlight_keywords_in_content(content: str, keywords: List[str]) -> str:
    """Add HTML highlighting for keywords found in article content."""
    if not keywords:
        return content
    
    for keyword in keywords:
        if isinstance(keyword, dict):
            keyword_text = keyword.get('title', '')
        else:
            keyword_text = str(keyword)
        
        if keyword_text:
            # Find and highlight (case-insensitive, whole words)
            import re
            pattern = r'\b' + re.escape(keyword_text) + r'\b'
            highlight = f'<mark class="bg-primary/20 text-primary-800 dark:text-primary-200 font-bold px-1 rounded">{keyword_text}</mark>'
            content = re.sub(pattern, highlight, content, flags=re.IGNORECASE)
    
    return content


def generate_article_page(deepseek_response: Dict[str, Any], level: str = 'middle', language: str = 'en') -> str:
    """
    Generate HTML article page from deepseek response.
    
    Args:
        deepseek_response: Deepseek analysis JSON response
        level: Difficulty level ('easy', 'middle', 'high')
        language: Language code ('en' or 'zh')
    
    Returns:
        Complete HTML page as string
    """
    
    # Read template
    template_path = Path(__file__).parent / 'article.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Extract data from response
    analysis = deepseek_response.get('article_analysis', {})
    level_data = analysis.get('levels', {}).get(level, {})
    
    # Get fields
    title = level_data.get('title', 'Article Title')
    summary = level_data.get('summary', '')
    keywords = level_data.get('keywords', [])
    questions = level_data.get('questions', [])
    background_read = level_data.get('background_read', [])
    article_structure = level_data.get('Article_Structure', [])
    perspectives = level_data.get('perspectives', [])
    
    # Build article content from summary with keyword highlighting
    article_content = ""
    if summary:
        # Split summary into paragraphs if it's a long string
        paragraphs = summary.split('\n') if isinstance(summary, str) else [str(summary)]
        article_content = "\n".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
        article_content = highlight_keywords_in_content(article_content, keywords)
    
    # Build background content from background_read
    background_content = ""
    if background_read:
        if isinstance(background_read, list):
            background_content = "\n".join(f"<p>{item}</p>" for item in background_read if item)
        else:
            background_content = f"<p>{background_read}</p>"
    
    # Build article structure content
    structure_content = ""
    if article_structure:
        if isinstance(article_structure, list):
            structure_content = "\n".join(f"<p>{item}</p>" for item in article_structure if item)
        else:
            structure_content = f"<p>{article_structure}</p>"
    
    # Build keywords HTML
    keywords_html = build_keywords_html(keywords)
    
    # Build quiz HTML
    quiz_html = build_quiz_html(questions)
    
    # Build perspectives HTML
    perspectives_html = build_perspectives_html(perspectives)
    
    # Replace template variables
    result = template.replace('${ARTICLE_TITLE}', title)
    result = result.replace('${ARTICLE_CONTENT}', article_content)
    result = result.replace('${KEYWORDS_HTML}', keywords_html)
    result = result.replace('${BACKGROUND_CONTENT}', background_content)
    result = result.replace('${ARTICLE_STRUCTURE}', structure_content)
    result = result.replace('${QUIZ_HTML}', quiz_html)
    result = result.replace('${PERSPECTIVES_HTML}', perspectives_html)
    
    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_article_page.py <deepseek_response.json> [level] [language]")
        print("  level: easy, middle, high (default: middle)")
        print("  language: en, zh (default: en)")
        sys.exit(1)
    
    response_file = sys.argv[1]
    level = sys.argv[2] if len(sys.argv) > 2 else 'middle'
    language = sys.argv[3] if len(sys.argv) > 3 else 'en'
    
    # Load deepseek response
    with open(response_file, 'r', encoding='utf-8') as f:
        response = json.load(f)
    
    # Generate page
    html = generate_article_page(response, level, language)
    
    # Output
    output_file = Path(response_file).stem + f'_{level}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated: {output_file}")


if __name__ == '__main__':
    main()
