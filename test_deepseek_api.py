#!/usr/bin/env python3
"""Test DeepSeek API connectivity and response time."""

import requests
import json
import time

DEEPSEEK_API_KEY = "sk-0ad0e8ca48544dd79ef790d17672eed2"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def test_api():
    """Test basic API connectivity."""
    print("Testing DeepSeek API connectivity...")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Simple test prompt
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Respond with exactly: WORKING"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        print("\n📤 Sending test request...")
        start = time.time()
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        elapsed = time.time() - start
        print(f"⏱️  Response time: {elapsed:.1f} seconds")
        
        if response.status_code == 200:
            print("✅ API is working!")
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"\n📝 Response: {content}")
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (60+ seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_api()
