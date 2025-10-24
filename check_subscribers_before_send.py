#!/usr/bin/env python3
"""
Check subscriber tags before sending

Display all 4 test subscribers and their tags from Buttondown.
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

class SubscriberChecker:
    """Check subscribers on Buttondown."""
    
    def __init__(self, api_token: str):
        """Initialize with API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def get_subscribers(self) -> List[Dict]:
        """Get all subscribers."""
        try:
            response = requests.get(
                f"{self.base_url}/subscribers",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return []
    
    def show_test_subscribers(self):
        """Display the 4 test subscribers and their tags."""
        
        test_emails = [
            'easy@daijiong.com',
            'mid@daijiong.com',
            'diff@daijiong.com',
            'cn@daijiong.com'
        ]
        
        subscribers = self.get_subscribers()
        sub_dict = {sub['email_address']: sub for sub in subscribers}
        
        print("\n" + "=" * 80)
        print("TEST SUBSCRIBERS & TAGS")
        print("=" * 80 + "\n")
        
        print(f"{'EMAIL':<25} {'TAGS':<40} {'STATUS':<15}")
        print("-" * 80)
        
        all_found = True
        for email in test_emails:
            if email in sub_dict:
                subscriber = sub_dict[email]
                tags = subscriber.get('tags', [])
                tags_str = ', '.join(tags) if tags else '(no tags)'
                print(f"{email:<25} {tags_str:<40} ✅ FOUND")
            else:
                print(f"{email:<25} {'(not found)':<40} ❌ MISSING")
                all_found = False
        
        print("\n" + "=" * 80)
        
        if all_found:
            print("✅ All 4 test subscribers found with tags")
        else:
            print("❌ Some subscribers missing")
        
        print("=" * 80)
        
        return sub_dict

def main():
    """Main execution."""
    
    api_token = os.getenv('BUTTONDOWN_API_TOKEN')
    if not api_token:
        print("❌ BUTTONDOWN_API_TOKEN not set")
        print("\nSet it with:")
        print("  export BUTTONDOWN_API_TOKEN='your_token'")
        return
    
    checker = SubscriberChecker(api_token)
    checker.show_test_subscribers()

if __name__ == "__main__":
    main()
