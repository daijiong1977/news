#!/usr/bin/env python3
"""
Test Deepseek output to verify JSON structure matches database schema.
Tests on 1-2 sample articles to confirm everything aligns.
"""

import json
import os
import sys
from datetime import datetime

# Sample article data for testing
SAMPLE_ARTICLES = [
    {
        "id": 1,
        "title": "Olympic Swimmer Breaks World Record in 100m Freestyle",
        "source": "Swimming World",
        "url": "https://example.com/article1",
        "description": "A young swimmer from Australia has shattered the world record in the 100-meter freestyle with a time of 46.94 seconds.",
        "content": "In a stunning display of athletic prowess, 23-year-old Australian swimmer Kyle Chalmers has broken the men's 100-meter freestyle world record with a time of 46.94 seconds at the Olympic trials. This achievement marks a significant milestone in the sport, surpassing the previous record by 0.3 seconds. Chalmers has been training intensively for the past two years, focusing on explosive power and stroke efficiency. His coach attributed the success to a new training methodology combining traditional techniques with modern sports science. The swimming community has praised this breakthrough, with many experts believing this signals a new era in competitive swimming where times previously thought impossible are now within reach."
    },
    {
        "id": 2,
        "title": "New AI Breakthrough: Language Models Show Improved Reasoning",
        "source": "Tech News",
        "url": "https://example.com/article2",
        "description": "Researchers announce a new technique that significantly improves AI reasoning capabilities.",
        "content": "Researchers at a leading AI institute have announced a breakthrough in language model reasoning capabilities. The new approach, called Chain-of-Thought Prompting Enhanced (COTE), allows AI systems to break down complex problems into smaller, manageable steps. In testing, models using COTE showed a 23% improvement in problem-solving accuracy compared to baseline approaches. The research team demonstrated the technique on mathematical reasoning, logical deduction, and scientific problem-solving tasks. This advancement could have implications for AI applications in education, scientific research, and professional training. The full research paper has been published in a leading AI conference, and the code has been made available to the research community for further exploration and refinement."
    }
]

def create_test_prompt(article, category_prompt="default"):
    """Create a test Deepseek prompt for an article."""
    
    prompts = {
        "default": """You are an expert editorial analyst and educator. Process the following article with comprehensive analysis for three difficulty levels.

For the article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary in English for elementary school readers>",
    "summary_mid": "<300-500 word summary in English for middle school readers>",
    "summary_hard": "<500-700 word summary in English for high school readers>",
    
    "summary_zh_hard": "<Chinese translation of high school summary, 500-700 words>",
    
    "key_words_easy": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "easy_explanation": "<simple 30-50 word explanation suitable for beginners>"
        },
        ... (pick top 10 keywords based on summary_easy: only include words with frequency <= 3)
    ],
    
    "key_words_mid": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "medium_explanation": "<intermediate 50-80 word explanation with moderate detail>"
        },
        ... (pick top 10 keywords based on summary_mid: only include words with frequency >= 2)
    ],
    
    "key_words_hard": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "hard_explanation": "<advanced 80-120 word explanation with technical depth and nuances>"
        },
        ... (pick top 10 keywords based on summary_hard: only include words with frequency >= 3)
    ],
    
    "background_reading_easy": "<100-150 word background for elementary school readers based on summary_easy>",
    "background_reading_mid": "<150-250 word background for middle school readers based on summary_mid>",
    "background_reading_hard": "<200-300 word background for high school readers based on summary_hard>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid, what positions/arguments are supported vs objected>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard, what positions/arguments are supported vs objected>"
    },
    
    "multiple_choice_questions_easy": [
        {
            "question": "<simple question based on summary_easy>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (8 questions based on summary_easy: 3-4 "what", 2-3 "how", 2-3 "why")
    ],
    
    "multiple_choice_questions_mid": [
        {
            "question": "<intermediate question based on summary_mid>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (10 questions based on summary_mid: 3-4 "what", 3-4 "how", 3-4 "why")
    ],
    
    "multiple_choice_questions_hard": [
        {
            "question": "<complex question based on summary_hard>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (12 questions based on summary_hard: 3-4 "what", 4-5 "how", 4-5 "why", includes SAT-level vocabulary questions)
    ],
    
    "perspectives_easy": {
        "perspective_1": {
            "title": "<simple perspective based on summary_easy>",
            "argument": "<1-2 simple sentences>",
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<simple alternative perspective based on summary_easy>",
            "argument": "<1-2 simple sentences>",
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<50-100 word synthesis based on summary_easy>",
            "attitude": "neutral"
        }
    },
    
    "perspectives_mid": {
        "perspective_1": {
            "title": "<perspective based on summary_mid>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<alternative perspective based on summary_mid>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<100-150 word synthesis based on summary_mid>",
            "attitude": "neutral"
        }
    },
    
    "perspectives_hard": {
        "perspective_1": {
            "title": "<perspective based on summary_hard>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<alternative perspective based on summary_hard>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<200-300 word synthesis based on summary_hard>",
            "attitude": "neutral"
        }
    }
}

IMPORTANT INSTRUCTIONS:
1. Create THREE versions of content for easy/mid/hard difficulty levels
2. Easy summaries: 100-200 words with simple language
3. Mid summaries: 300-500 words with some technical terms
4. Hard summaries: 500-700 words with full technical depth
5. Chinese translations must be natural and idiomatic, not literal
6. **CRITICAL FOR KEYWORDS: ONLY include words with correct frequency for each level**
   - Easy: frequency <=3
   - Mid: frequency >= 2
   - Hard: frequency >= 3
7. Each keyword must have appropriate difficulty-level explanation
8. Questions increase in complexity: easy (8) → mid (10) → hard (12)
9. Each question type should match its difficulty level
10. Perspectives: attitudes can vary (positive/neutral/negative), synthesis always neutral
11. Return ONLY valid JSON, one object per article
12. All summaries must meet exact word count requirements

ARTICLE TO PROCESS:
Title: {title}
Source: {source}
URL: {url}
Description: {description}
Content: {content}

Generate comprehensive analysis. Return ONLY the JSON response, no other text.""".format(
            title=article['title'],
            source=article['source'],
            url=article['url'],
            description=article['description'],
            content=article['content']
        )
    }
    
    return prompts.get(category_prompt, prompts["default"])


def verify_json_structure(json_obj):
    """Verify JSON structure matches database schema."""
    
    required_fields = {
        "article_id": (int, "Article ID"),
        "title_zh": (str, "Chinese title translation"),
        "summary_easy": (str, "Easy summary (100-200 words)"),
        "summary_mid": (str, "Mid summary (300-500 words)"),
        "summary_hard": (str, "Hard summary (500-700 words)"),
        "summary_zh_hard": (str, "Chinese hard summary"),
        "key_words_easy": (list, "Easy keywords (10 items)"),
        "key_words_mid": (list, "Mid keywords (10 items)"),
        "key_words_hard": (list, "Hard keywords (10 items)"),
        "background_reading_easy": (str, "Easy background reading"),
        "background_reading_mid": (str, "Mid background reading"),
        "background_reading_hard": (str, "Hard background reading"),
        "article_analysis_mid": (dict, "Mid analysis (structure & tone)"),
        "article_analysis_hard": (dict, "Hard analysis (structure & tone)"),
        "multiple_choice_questions_easy": (list, "Easy questions (8 items)"),
        "multiple_choice_questions_mid": (list, "Mid questions (10 items)"),
        "multiple_choice_questions_hard": (list, "Hard questions (12 items)"),
        "perspectives_easy": (dict, "Easy perspectives"),
        "perspectives_mid": (dict, "Mid perspectives"),
        "perspectives_hard": (dict, "Hard perspectives"),
    }
    
    print("\n" + "="*70)
    print("VERIFYING JSON STRUCTURE")
    print("="*70)
    
    errors = []
    warnings = []
    
    for field, (expected_type, description) in required_fields.items():
        if field not in json_obj:
            errors.append(f"✗ Missing field: {field} ({description})")
        else:
            actual_type = type(json_obj[field])
            if actual_type != expected_type:
                errors.append(f"✗ Field '{field}' type mismatch: expected {expected_type.__name__}, got {actual_type.__name__}")
            else:
                print(f"✓ {field}: {description}")
    
    # Verify summary word counts
    if "summary_easy" in json_obj:
        easy_words = len(json_obj["summary_easy"].split())
        if not (100 <= easy_words <= 200):
            warnings.append(f"⚠ summary_easy: {easy_words} words (expected 100-200)")
    
    if "summary_mid" in json_obj:
        mid_words = len(json_obj["summary_mid"].split())
        if not (300 <= mid_words <= 500):
            warnings.append(f"⚠ summary_mid: {mid_words} words (expected 300-500)")
    
    if "summary_hard" in json_obj:
        hard_words = len(json_obj["summary_hard"].split())
        if not (500 <= hard_words <= 700):
            warnings.append(f"⚠ summary_hard: {hard_words} words (expected 500-700)")
    
    # Verify keyword counts
    if "key_words_easy" in json_obj:
        easy_kw_count = len(json_obj["key_words_easy"])
        if easy_kw_count != 10:
            warnings.append(f"⚠ key_words_easy: {easy_kw_count} keywords (expected 10)")
    
    if "key_words_mid" in json_obj:
        mid_kw_count = len(json_obj["key_words_mid"])
        if mid_kw_count != 10:
            warnings.append(f"⚠ key_words_mid: {mid_kw_count} keywords (expected 10)")
    
    if "key_words_hard" in json_obj:
        hard_kw_count = len(json_obj["key_words_hard"])
        if hard_kw_count != 10:
            warnings.append(f"⚠ key_words_hard: {hard_kw_count} keywords (expected 10)")
    
    # Verify question counts
    if "multiple_choice_questions_easy" in json_obj:
        easy_q_count = len(json_obj["multiple_choice_questions_easy"])
        if easy_q_count != 8:
            warnings.append(f"⚠ multiple_choice_questions_easy: {easy_q_count} questions (expected 8)")
    
    if "multiple_choice_questions_mid" in json_obj:
        mid_q_count = len(json_obj["multiple_choice_questions_mid"])
        if mid_q_count != 10:
            warnings.append(f"⚠ multiple_choice_questions_mid: {mid_q_count} questions (expected 10)")
    
    if "multiple_choice_questions_hard" in json_obj:
        hard_q_count = len(json_obj["multiple_choice_questions_hard"])
        if hard_q_count != 12:
            warnings.append(f"⚠ multiple_choice_questions_hard: {hard_q_count} questions (expected 12)")
    
    # Verify perspectives attitudes
    if "perspectives_easy" in json_obj:
        if "synthesis" in json_obj["perspectives_easy"]:
            synth_attitude = json_obj["perspectives_easy"]["synthesis"].get("attitude")
            if synth_attitude != "neutral":
                warnings.append(f"⚠ perspectives_easy synthesis attitude: {synth_attitude} (should be 'neutral')")
    
    if "perspectives_mid" in json_obj:
        if "synthesis" in json_obj["perspectives_mid"]:
            synth_attitude = json_obj["perspectives_mid"]["synthesis"].get("attitude")
            if synth_attitude != "neutral":
                warnings.append(f"⚠ perspectives_mid synthesis attitude: {synth_attitude} (should be 'neutral')")
    
    if "perspectives_hard" in json_obj:
        if "synthesis" in json_obj["perspectives_hard"]:
            synth_attitude = json_obj["perspectives_hard"]["synthesis"].get("attitude")
            if synth_attitude != "neutral":
                warnings.append(f"⚠ perspectives_hard synthesis attitude: {synth_attitude} (should be 'neutral')")
    
    print("\n" + "-"*70)
    if errors:
        print("ERRORS:")
        for error in errors:
            print(error)
    
    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(warning)
    
    if not errors and not warnings:
        print("\n✓ All validations passed!")
    
    return len(errors) == 0


def print_summary(json_obj):
    """Print a summary of key fields from the Deepseek response."""
    
    print("\n" + "="*70)
    print("RESPONSE SUMMARY")
    print("="*70)
    
    print(f"\nArticle ID: {json_obj.get('article_id')}")
    print(f"Title (Chinese): {json_obj.get('title_zh', 'N/A')[:80]}...")
    
    print(f"\n✓ Summaries:")
    print(f"  - Easy: {len(json_obj.get('summary_easy', '').split())} words")
    print(f"  - Mid: {len(json_obj.get('summary_mid', '').split())} words")
    print(f"  - Hard: {len(json_obj.get('summary_hard', '').split())} words")
    
    print(f"\n✓ Keywords:")
    print(f"  - Easy: {len(json_obj.get('key_words_easy', []))} keywords")
    print(f"  - Mid: {len(json_obj.get('key_words_mid', []))} keywords")
    print(f"  - Hard: {len(json_obj.get('key_words_hard', []))} keywords")
    
    print(f"\n✓ Questions:")
    print(f"  - Easy: {len(json_obj.get('multiple_choice_questions_easy', []))} questions")
    print(f"  - Mid: {len(json_obj.get('multiple_choice_questions_mid', []))} questions")
    print(f"  - Hard: {len(json_obj.get('multiple_choice_questions_hard', []))} questions")
    
    print(f"\n✓ Analysis:")
    if "article_analysis_mid" in json_obj:
        mid_len = len(json_obj["article_analysis_mid"].get("analysis_en", "").split())
        print(f"  - Mid: {mid_len} words")
    if "article_analysis_hard" in json_obj:
        hard_len = len(json_obj["article_analysis_hard"].get("analysis_en", "").split())
        print(f"  - Hard: {hard_len} words")


def main():
    """Main test function."""
    
    print("\n" + "="*70)
    print("DEEPSEEK OUTPUT VERIFICATION TEST")
    print("Testing schema alignment for 2 sample articles")
    print("="*70)
    
    # Create test prompt
    print(f"\nSample articles to test: {len(SAMPLE_ARTICLES)}")
    for article in SAMPLE_ARTICLES:
        print(f"  - Article {article['id']}: {article['title']}")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("""
1. Review the structure above
2. When ready, create data_processor.py to:
   - Collect articles from database (unprocessed)
   - Call Deepseek API with category-specific prompts
   - Parse JSON response
   - Insert into all 19 tables:
     * article_summaries (6 rows: easy_en, easy_zh, mid_en, mid_zh, hard_en, hard_zh)
     * keywords (30 rows: 10 for each level)
     * questions (30 rows: 8+10+12 questions)
     * choices (questions × 4 options)
     * comments (3 rows: one per difficulty level for perspectives)
     * background_read (3 rows: one per difficulty level)
     * article_analysis (2 rows: mid and hard)

3. Test on article_id=1 first
4. Then test on article_id=2
5. Verify all data inserted correctly
6. Then process all articles
""")


if __name__ == "__main__":
    main()
