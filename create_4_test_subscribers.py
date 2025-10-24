#!/usr/bin/env python3
"""
Create 4 test subscribers on Buttondown with correct tags
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class SubscriberCreator:
    """Create test subscribers."""
    
    def __init__(self, api_token: str):
        """Initialize with API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def create_subscriber(self, email: str, tag: str) -> bool:
        """Create a subscriber with a tag."""
        
        payload = {
            "email_address": email,
            "tags": [tag],
            "metadata": {
                "test_account": "true"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/subscribers",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✅ Created: {email} with tag '{tag}'")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating {email}: {e}")
            return False
    
    def create_all(self):
        """Create all 4 test subscribers."""
        
        subscribers = [
            ('easy@daijiong.com', 'level_easy'),
            ('mid@daijiong.com', 'level_mid'),
            ('diff@daijiong.com', 'level_hard'),
            ('cn@daijiong.com', 'level_CN')
        ]
        
        print("\n" + "=" * 80)
        print("CREATING 4 TEST SUBSCRIBERS")
        print("=" * 80 + "\n")
        
        for email, tag in subscribers:
            self.create_subscriber(email, tag)
        
        print("\n" + "=" * 80)
        print("✅ DONE")
        print("=" * 80)

def main():
    api_token = os.getenv('BUTTONDOWN_API_TOKEN')
    if not api_token:
        print("❌ BUTTONDOWN_API_TOKEN not set")
        return
    
    creator = SubscriberCreator(api_token)
    creator.create_all()

if __name__ == "__main__":
    main()
