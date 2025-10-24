#!/usr/bin/env python3
"""
Simple test script to verify Buttondown API connectivity.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
print(f"API Key loaded: {BUTTONDOWN_API_KEY[:20]}..." if BUTTONDOWN_API_KEY else "No API key found")

# Test subscriber creation
test_payload = {
    'email_address': 'test.subscriber@example.com',
    'tags': ['easy', '3-5', 'science'],
    'metadata': {
        'name': 'Test Subscriber',
        'read_level': 'easy',
        'grade': '3-5',
        'categories': 'science'
    }
}

headers = {
    'Authorization': f'Token {BUTTONDOWN_API_KEY}',
    'Content-Type': 'application/json'
}

print("\nTesting Buttondown API connection...")
print(f"Payload: {test_payload}")

try:
    response = requests.post(
        'https://api.buttondown.email/v1/subscribers',
        json=test_payload,
        headers=headers,
        timeout=10
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("\n✅ Successfully created subscriber in Buttondown!")
        print(f"Subscriber ID: {response.json().get('id')}")
    elif response.status_code == 409:
        print("\n⚠️  Subscriber already exists in Buttondown")
    else:
        print(f"\n❌ Error: {response.json()}")
        
except Exception as e:
    print(f"❌ Connection error: {str(e)}")
