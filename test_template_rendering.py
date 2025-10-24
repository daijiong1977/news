#!/usr/bin/env python3
"""
Step 4: Test conditional template rendering with mock subscriber data
This script simulates what Buttondown will do - render template for each subscriber
"""

import json
import re
from jinja2 import Template

# Read the template with content
with open('/Users/jidai/news/email_template_with_content.html', 'r', encoding='utf-8') as f:
    template_text = f.read()

# Mock subscriber data (what Buttondown has in database)
mock_subscribers = [
    {
        "email_address": "easyread@daijiong.com",
        "metadata": {"read_level": "easy"},
        "tags": []
    },
    {
        "email_address": "middl@daijiong.com",
        "metadata": {"read_level": "middle"},
        "tags": []
    },
    {
        "email_address": "difficult@daijiong.com",
        "metadata": {"read_level": "diff"},
        "tags": []
    },
    {
        "email_address": "cn@daijiong.com",
        "metadata": {"read_level": "CN"},
        "tags": []
    }
]

# Create Jinja2 template
jinja_template = Template(template_text)

print("\n" + "=" * 80)
print("✅ STEP 4: Testing template rendering for each subscriber")
print("=" * 80 + "\n")

# Test render for each subscriber
for i, subscriber in enumerate(mock_subscribers, 1):
    print(f"\n--- Test {i}: {subscriber['email_address']} ---")
    print(f"    read_level: {subscriber['metadata']['read_level']}")
    
    try:
        # Render template with subscriber data
        rendered = jinja_template.render(subscriber=subscriber)
        
        # Check which article level was rendered
        if 'article_body_easy' in rendered or 'Beginner-friendly' in rendered or 'Easy to understand' in rendered:
            level_detected = "Easy (🟢)"
        elif 'article_body_mid' in rendered or 'Intermediate-level' in rendered or 'More detail' in rendered:
            level_detected = "Middle (🔵)"
        elif 'article_body_hard' in rendered or 'Expert-level' in rendered or 'technical insights' in rendered:
            level_detected = "Hard (🟠)"
        elif 'article_body_CN' in rendered or '中文版本' in rendered or 'Chinese' in rendered:
            level_detected = "Chinese (🔴)"
        else:
            level_detected = "Unknown"
        
        # Save rendered output for inspection
        output_file = f'/Users/jidai/news/test_render_{subscriber["email_address"].split("@")[0]}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rendered)
        
        print(f"    ✅ Rendered successfully")
        print(f"    📧 Output: {output_file}")
        print(f"    🎯 Detected level: {level_detected}")
        print(f"    📏 Size: {len(rendered):,} bytes")
        
    except Exception as e:
        print(f"    ❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
print("✅ STEP 4 COMPLETE: All 4 test renders generated")
print("=" * 80)
print("\nVerify each output file to ensure correct content per level:")
print("  1. test_render_easyread.html (should have Easy content)")
print("  2. test_render_middl.html (should have Middle content)")
print("  3. test_render_difficult.html (should have Hard content)")
print("  4. test_render_cn.html (should have Chinese content)")

print("\n" + "=" * 80)
print("NEXT: Copy template to Buttondown and send to test subscribers")
print("=" * 80 + "\n")
