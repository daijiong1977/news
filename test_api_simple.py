#!/usr/bin/env python3
"""
Test: Send article to Deepseek API and save response to disk
No database operations - just API test
"""

import json
import os
import requests
from datetime import datetime

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY:
    raise RuntimeError('DEEPSEEK_API_KEY not set')

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# Article data
article = {
    "id": 1,
    "title": "Other Brazen Art Heists Like the Louvre Jewelry Theft",
    "source": "US News",
    "link": "https://example.com/1",
    "content": "A major jewelry heist at the Louvre has sparked discussions about museum security and famous art thefts throughout history. This incident follows a series of brazen heists at prestigious institutions around the world. The Louvre, one of the most visited museums globally, has enhanced its security measures following this theft. Art theft remains a significant concern for museums worldwide, with thousands of pieces stolen annually. The investigation into this heist continues, with authorities working to recover the stolen items and identify the perpetrators."
}

# Create prompt
prompt = f"""You are an expert editorial analyst and educator. Process this article with comprehensive analysis.

For this article, provide a JSON response with the following structure:

{{
    "article_id": {article['id']},
    "summary_en": "<500-700 word summary in English>",
    "summary_zh": "<Chinese translation of the English summary, 500-700 words>",
    "key_words": [
        {{
            "word": "<keyword>",
            "frequency": <count>,
            "explanation": "<50-100 word explanation>",
            "easy_explanation": "<simple 30-50 word explanation>",
            "medium_explanation": "<intermediate 50-80 word explanation>",
            "hard_explanation": "<advanced 80-120 word explanation>"
        }}
    ],
    "background_reading": "<200-300 word background>",
    "multiple_choice_questions": [
        {{
            "question": "<question text>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why correct>",
            "word_type": "<what/how/why>"
        }}
    ],
    "discussion_both_sides": {{
        "perspective_1": {{
            "title": "<perspective name>",
            "arguments": ["<argument 1>", "<argument 2>"]
        }},
        "perspective_2": {{
            "title": "<alternative perspective>",
            "arguments": ["<argument 1>", "<argument 2>"]
        }},
        "synthesis": "<200 word synthesis>"
    }}
}}

ARTICLE:
Title: {article['title']}
Content: {article['content']}

Return ONLY valid JSON. No markdown formatting.
"""

print("="*70)
print("DEEPSEEK API TEST - Send Article and Save Response")
print("="*70)
print(f"Article ID: {article['id']}")
print(f"Title: {article['title'][:60]}...")
print(f"Prompt length: {len(prompt)} characters")
print()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
}

payload = {
    "model": "deepseek-chat",
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.7,
    "max_tokens": 6000
}

print("Sending to Deepseek API...")
print(f"Timeout: (30s connect, 300s read)")
print()

try:
    response = requests.post(
        DEEPSEEK_API_URL,
        json=payload,
        headers=headers,
        timeout=(30, 300)
    )
    
    print(f"✓ Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Strip markdown if present
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            
            print(f"✓ Response length: {len(content)} characters")
            print()
            
            # Save to disk
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"deepseek_response_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Response saved to: {filename}")
            print()
            
            # Try to parse and show structure
            try:
                data = json.loads(content)
                print("✓ Response is valid JSON")
                print(f"  Keys in response: {list(data.keys())}")
                
                if "article_id" in data:
                    print(f"  Article ID: {data['article_id']}")
                if "summary_en" in data:
                    print(f"  Summary EN: {len(data['summary_en'])} characters")
                if "key_words" in data:
                    print(f"  Keywords: {len(data['key_words'])} items")
                if "multiple_choice_questions" in data:
                    print(f"  Questions: {len(data['multiple_choice_questions'])} items")
                    
            except json.JSONDecodeError as e:
                print(f"✗ Response is not valid JSON: {e}")
                print(f"  First 200 chars: {content[:200]}")
        else:
            print("✗ No choices in response")
            print(f"Response: {result}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except requests.exceptions.Timeout as e:
    print(f"✗ Timeout: {e}")
except requests.RequestException as e:
    print(f"✗ Request error: {e}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

print()
print("="*70)
