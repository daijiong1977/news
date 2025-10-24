#!/usr/bin/env python3
"""
Debug script to test Buttondown API with detailed request/response logging.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
print(f"API Key loaded: {BUTTONDOWN_API_KEY}")
print(f"API Key length: {len(BUTTONDOWN_API_KEY) if BUTTONDOWN_API_KEY else 0}")

# Test with minimal payload first
test_payload = {
    'email_address': 'debug.test@example.com',
    'metadata': {
        'name': 'Debug Test'
    }
}

headers = {
    'Authorization': f'Token {BUTTONDOWN_API_KEY}',
    'Content-Type': 'application/json'
}

print("\n=== REQUEST DEBUG ===")
print(f"URL: https://api.buttondown.email/v1/subscribers")
print(f"Method: POST")
print(f"Headers: {headers}")
print(f"Payload: {test_payload}")

try:
    response = requests.post(
        'https://api.buttondown.email/v1/subscribers',
        json=test_payload,
        headers=headers,
        timeout=10
    )
    
    print(f"\n=== RESPONSE DEBUG ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 201:
        print("\n✅ SUCCESS!")
    elif response.status_code == 401:
        print("\n❌ AUTHENTICATION FAILED")
        print("Possible issues:")
        print("1. API key is invalid or expired")
        print("2. API key format is wrong")
        print("3. Token is not properly formatted with 'Token ' prefix")
    elif response.status_code == 409:
        print("\n⚠️  SUBSCRIBER ALREADY EXISTS")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
    import traceback
    traceback.print_exc()
