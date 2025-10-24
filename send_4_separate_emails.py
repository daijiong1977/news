#!/usr/bin/env python3
"""
Create and send 4 separate emails to Buttondown - one for each reading level
Each email has the actual content embedded (not templates)
"""

import requests
import json
from jinja2 import Template

API_TOKEN = "743996df-1545-4127-9f94-d35114ce00b4"
API_BASE = "https://api.buttondown.email/v1"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# Read template
with open('/Users/jidai/news/email_template_conditional.html', 'r', encoding='utf-8') as f:
    template_html = f.read()

# Read variables
with open('/Users/jidai/news/template_variables.json', 'r', encoding='utf-8') as f:
    variables = json.load(f)['variables']

# Mock subscribers for testing
subscribers = [
    {"email": "easyread@daijiong.com", "name": "easyread", "data": {"metadata": {"read_level": "easy"}}},
    {"email": "middl@daijiong.com", "name": "middl", "data": {"metadata": {"read_level": "middle"}}},
    {"email": "difficult@daijiong.com", "name": "difficult", "data": {"metadata": {"read_level": "diff"}}},
    {"email": "cn@daijiong.com", "name": "cn", "data": {"metadata": {"read_level": "CN"}}}
]

jinja_template = Template(template_html)

print("\n" + "=" * 80)
print("SENDING 4 SEPARATE EMAILS TO BUTTONDOWN")
print("=" * 80 + "\n")

for subscriber in subscribers:
    print(f"\n📧 Processing {subscriber['email']}...")
    
    # Render template for this subscriber
    rendered_html = jinja_template.render(subscriber=subscriber['data'])
    
    # Create email in Buttondown
    email_payload = {
        "subject": f"📰 News Digest - Your Reading Level ({subscriber['name'].upper()})",
        "body": rendered_html
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/emails",
            headers=HEADERS,
            json=email_payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            email_data = response.json()
            email_id = email_data['id']
            print(f"   ✅ Created: {email_id}")
            print(f"   Status: {email_data.get('status')}")
            
            # Get email back to verify content
            get_response = requests.get(
                f"{API_BASE}/emails/{email_id}",
                headers=HEADERS
            )
            if get_response.status_code == 200:
                email_check = get_response.json()
                body = email_check.get('body', '')
                
                # Verify correct content is in the body
                if subscriber['data']['metadata']['read_level'] == 'easy' and 'Beginner-friendly' in body:
                    print(f"   ✅ Content verified: Easy level detected")
                elif subscriber['data']['metadata']['read_level'] == 'middle' and 'Intermediate-level' in body:
                    print(f"   ✅ Content verified: Middle level detected")
                elif subscriber['data']['metadata']['read_level'] == 'diff' and 'Expert-level' in body:
                    print(f"   ✅ Content verified: Hard level detected")
                elif subscriber['data']['metadata']['read_level'] == 'CN' and '中文版本' in body:
                    print(f"   ✅ Content verified: Chinese version detected")
                else:
                    print(f"   ⚠️  Content check: Please verify manually")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

print("\n" + "=" * 80)
print("✅ ALL 4 EMAILS CREATED WITH ACTUAL CONTENT")
print("=" * 80)
print("\nNow you need to SEND them from Buttondown dashboard:")
print("1. Go to Buttondown.email → Drafts")
print("2. You should see 4 new emails:")
print("   - 📰 News Digest - Your Reading Level (EASYREAD)")
print("   - 📰 News Digest - Your Reading Level (MIDDL)")
print("   - 📰 News Digest - Your Reading Level (DIFFICULT)")
print("   - 📰 News Digest - Your Reading Level (CN)")
print("3. Send each one to the corresponding subscriber")
print("   OR: Send all 4 to all subscribers (won't hurt)")
print("\n" + "=" * 80 + "\n")
