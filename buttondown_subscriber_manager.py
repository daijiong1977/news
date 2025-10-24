#!/usr/bin/env python3
"""
Buttondown Subscriber Manager

Manages 4 test subscribers:
- easy@daijiong.com (Level: Easy)
- mid@daijiong.com (Level: Middle)
- diff@daijiong.com (Level: Hard)
- cn@daijiong.com (Level: Chinese)

Functions:
1. Create 4 test subscribers with correct levels/tags
2. Clean up all other subscribers
3. Send campaigns to test subscribers
"""

import requests
import json
from typing import List, Dict, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ButtondownManager:
    """Manage Buttondown subscribers and campaigns."""
    
    def __init__(self, api_token: str):
        """Initialize with Buttondown API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        self.test_subscribers = {
            'easy@daijiong.com': 'easy',
            'mid@daijiong.com': 'mid',
            'diff@daijiong.com': 'hard',
            'cn@daijiong.com': 'CN'
        }
    
    def get_all_subscribers(self) -> List[Dict]:
        """Get all current subscribers."""
        try:
            response = requests.get(
                f"{self.base_url}/subscribers",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching subscribers: {e}")
            return []
    
    def delete_subscriber(self, email: str) -> bool:
        """Delete a subscriber by email."""
        try:
            response = requests.delete(
                f"{self.base_url}/subscribers/{email}",
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✓ Deleted: {email}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Error deleting {email}: {e}")
            return False
    
    def create_subscriber(self, email: str, level: str) -> bool:
        """
        Create a test subscriber with specified level.
        
        Args:
            email: Email address
            level: 'easy', 'mid', 'hard', or 'CN'
        
        Returns:
            True if successful
        """
        level_config = {
            'easy': ('🟢 Easy', 'Level: Easy'),
            'mid': ('🔵 Middle', 'Level: Middle'),
            'hard': ('🟠 Hard', 'Level: Hard'),
            'CN': ('🔴 Chinese', 'Level: Chinese')
        }
        
        level_name, tag = level_config.get(level, ('🔵 Middle', 'Level: Middle'))
        
        payload = {
            'email': email,
            'metadata': {
                'difficulty_level': level,
                'signup_source': 'test_setup',
                'test_account': 'true'
            },
            'tags': [tag]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/subscribers",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✅ Created: {email} ({level_name})")
            return True
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e):
                print(f"⚠️  Already exists: {email}")
                return True
            print(f"❌ Error creating {email}: {e}")
            return False
    
    def cleanup_subscribers(self) -> Dict:
        """
        Delete all subscribers except the 4 test accounts.
        
        Returns:
            Dict with deleted count
        """
        print("\n🧹 Cleaning up subscribers...")
        print("-" * 60)
        
        all_subs = self.get_all_subscribers()
        print(f"Total subscribers found: {len(all_subs)}")
        
        deleted_count = 0
        kept_count = 0
        
        for subscriber in all_subs:
            email = subscriber.get('email', '')
            
            if email in self.test_subscribers:
                print(f"  ✓ Keeping: {email} (test account)")
                kept_count += 1
            else:
                if self.delete_subscriber(email):
                    deleted_count += 1
        
        print(f"\n📊 Cleanup Summary:")
        print(f"  ✓ Kept: {kept_count} test accounts")
        print(f"  ✗ Deleted: {deleted_count} other accounts")
        
        return {'deleted': deleted_count, 'kept': kept_count}
    
    def create_test_subscribers(self) -> Dict:
        """
        Create the 4 test subscribers.
        
        Returns:
            Dict with creation results
        """
        print("\n📝 Creating test subscribers...")
        print("-" * 60)
        
        results = {}
        for email, level in self.test_subscribers.items():
            success = self.create_subscriber(email, level)
            results[email] = success
        
        print(f"\n📊 Subscriber Creation Summary:")
        success_count = sum(1 for v in results.values() if v)
        print(f"  ✅ Created: {success_count}/{len(self.test_subscribers)}")
        
        return results
    
    def list_subscribers_by_level(self) -> Dict:
        """List all subscribers grouped by level."""
        print("\n📋 Current Subscribers by Level:")
        print("-" * 60)
        
        all_subs = self.get_all_subscribers()
        
        by_level = {
            'easy': [],
            'mid': [],
            'hard': [],
            'CN': [],
            'unknown': []
        }
        
        for sub in all_subs:
            email = sub.get('email', 'unknown')
            level = sub.get('metadata', {}).get('difficulty_level', 'unknown')
            tags = sub.get('tags', [])
            
            if level in by_level:
                by_level[level].append({'email': email, 'tags': tags})
            else:
                by_level['unknown'].append({'email': email, 'tags': tags})
        
        for level, subs in by_level.items():
            if subs:
                print(f"\n{level.upper()}:")
                for sub in subs:
                    print(f"  - {sub['email']}")
        
        return by_level
    
    def verify_test_setup(self) -> bool:
        """Verify all 4 test subscribers are set up correctly."""
        print("\n✅ Verifying test setup...")
        print("-" * 60)
        
        all_subs = self.get_all_subscribers()
        emails = {sub['email'] for sub in all_subs}
        
        all_found = True
        for email, level in self.test_subscribers.items():
            if email in emails:
                print(f"✓ {email} - Level {level}")
            else:
                print(f"✗ {email} - NOT FOUND")
                all_found = False
        
        if all_found:
            print("\n✅ All 4 test subscribers verified!")
        else:
            print("\n❌ Some test subscribers are missing!")
        
        return all_found

def main():
    """Main execution."""
    
    # Get API token from environment
    api_token = os.getenv('BUTTONDOWN_API_TOKEN')
    if not api_token:
        print("❌ BUTTONDOWN_API_TOKEN not set in environment!")
        print("\nTo set it:")
        print("  export BUTTONDOWN_API_TOKEN='your_token_here'")
        print("\nOr create a .env file with:")
        print("  BUTTONDOWN_API_TOKEN=your_token_here")
        return
    
    manager = ButtondownManager(api_token)
    
    print("=" * 60)
    print("BUTTONDOWN SUBSCRIBER MANAGER")
    print("=" * 60)
    
    # Step 1: List current subscribers
    print("\n📊 Step 1: Current Subscribers")
    by_level = manager.list_subscribers_by_level()
    
    # Step 2: Create test subscribers
    print("\n📝 Step 2: Create Test Subscribers")
    create_results = manager.create_test_subscribers()
    
    # Step 3: Clean up other subscribers
    print("\n🧹 Step 3: Clean up other subscribers")
    try:
        user_input = input("\nWARNING: This will DELETE all subscribers except the 4 test accounts.\nContinue? (yes/no): ").strip().lower()
        if user_input == 'yes':
            cleanup_results = manager.cleanup_subscribers()
        else:
            print("Cleanup skipped.")
            return
    except KeyboardInterrupt:
        print("\nCleanup cancelled.")
        return
    
    # Step 4: Verify final setup
    print("\n🔍 Step 4: Verify Final Setup")
    manager.verify_test_setup()
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n4 Test Subscribers Created:")
    print("  📧 easy@daijiong.com → Level: Easy")
    print("  📧 mid@daijiong.com → Level: Middle")
    print("  📧 diff@daijiong.com → Level: Hard")
    print("  📧 cn@daijiong.com → Level: Chinese")
    print("\nNext steps:")
    print("1. Create 4 campaigns in Buttondown (one per level)")
    print("2. Copy HTML content to each campaign")
    print("3. Set tag filter for each campaign")
    print("4. Send to test subscribers")

if __name__ == "__main__":
    main()
