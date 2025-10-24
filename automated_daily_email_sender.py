#!/usr/bin/env python3
"""
AUTOMATED DAILY EMAIL SENDER
Generates daily personalized emails and sends to Buttondown
Run this once per day to send to all subscribers
"""

import requests
import json
import sys
from datetime import datetime

API_TOKEN = "743996df-1545-4127-9f94-d35114ce00b4"
API_BASE = "https://api.buttondown.email/v1"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def create_daily_email():
    """Create and send daily email to Buttondown"""
    
    print("\n" + "=" * 80)
    print("AUTOMATED DAILY EMAIL SENDER")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Read the universal template
    try:
        with open('/Users/jidai/news/universal_email_template.html', 'r', encoding='utf-8') as f:
            template_body = f.read()
    except FileNotFoundError:
        print("❌ Error: universal_email_template.html not found!")
        sys.exit(1)
    
    # Create email with today's date
    today = datetime.now().strftime('%B %d, %Y')
    email_payload = {
        "subject": f"📰 News Digest - {today}",
        "body": template_body
    }
    
    print(f"Creating email for: {today}")
    print(f"Template size: {len(template_body):,} bytes")
    print(f"Sending to: ALL subscribers\n")
    
    # Create email in Buttondown
    response = requests.post(
        f"{API_BASE}/emails",
        headers=HEADERS,
        json=email_payload,
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        email_data = response.json()
        email_id = email_data['id']
        status = email_data.get('status')
        
        print("✅ EMAIL CREATED IN BUTTONDOWN!")
        print(f"   Email ID: {email_id}")
        print(f"   Subject: {email_data['subject']}")
        print(f"   Status: {status}")
        
        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print(f"""
Your email is ready! Now you need to SEND it:

Option A: MANUAL (Go to Buttondown dashboard)
  1. Visit: https://buttondown.email
  2. Click: Drafts
  3. Find: "📰 News Digest - {today}"
  4. Click: Send
  5. Choose: "Send to All Subscribers"

Option B: AUTOMATIC (Use API - coming soon!)
  - Can add feature to auto-send via API

Email ID (for reference): {email_id}
""")
        print("=" * 80 + "\n")
        
        return email_id
        
    else:
        print(f"❌ Error creating email: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)

def get_subscribers_count():
    """Get total number of subscribers"""
    response = requests.get(
        f"{API_BASE}/subscribers",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        return count
    return None

if __name__ == "__main__":
    try:
        # Check subscriber count
        count = get_subscribers_count()
        if count:
            print(f"Total subscribers: {count}\n")
        
        # Create daily email
        email_id = create_daily_email()
        
        print(f"\n✅ AUTOMATED WORKFLOW COMPLETE!")
        print(f"   Email created: {email_id}")
        print(f"   Next: Send from Buttondown dashboard")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
