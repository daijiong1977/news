#!/usr/bin/env python3
"""
Verify Test Subscriber Tags on Buttondown

Check that the 4 test subscribers have the correct tags set up.
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

class SubscriberVerifier:
    """Verify subscriber tags on Buttondown."""
    
    def __init__(self, api_token: str):
        """Initialize with API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        self.test_subscribers = {
            'easy@daijiong.com': {
                'expected_tags': ['level_easy'],
                'level': 'easy'
            },
            'mid@daijiong.com': {
                'expected_tags': ['level_mid'],
                'level': 'mid'
            },
            'diff@daijiong.com': {
                'expected_tags': ['level_hard'],
                'level': 'hard'
            },
            'cn@daijiong.com': {
                'expected_tags': ['level_CN'],
                'level': 'CN'
            }
        }
    
    def get_all_subscribers(self) -> List[Dict]:
        """Get all subscribers from Buttondown."""
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
    
    def verify_tags(self) -> Dict:
        """Verify all test subscribers have correct tags."""
        print("\n" + "=" * 70)
        print("VERIFYING SUBSCRIBER TAGS ON BUTTONDOWN")
        print("=" * 70)
        
        all_subs = self.get_all_subscribers()
        sub_dict = {sub['email']: sub for sub in all_subs}
        
        results = {}
        
        for email, config in self.test_subscribers.items():
            expected_tags = config['expected_tags']
            level = config['level']
            
            if email not in sub_dict:
                print(f"\n❌ MISSING: {email}")
                results[email] = {'status': 'missing', 'tags': []}
                continue
            
            subscriber = sub_dict[email]
            actual_tags = subscriber.get('tags', [])
            
            # Normalize tag names (lower case, remove spaces)
            normalized_actual = [tag.lower().replace(' ', '_') for tag in actual_tags]
            normalized_expected = [tag.lower().replace(' ', '_') for tag in expected_tags]
            
            # Check if tags match
            tags_match = all(tag in normalized_actual for tag in normalized_expected)
            
            if tags_match:
                status = '✅ OK'
                print(f"\n✅ CORRECT: {email}")
            else:
                status = '⚠️  WRONG'
                print(f"\n⚠️  INCORRECT: {email}")
            
            print(f"   Level: {level}")
            print(f"   Expected tags: {expected_tags}")
            print(f"   Actual tags: {actual_tags}")
            print(f"   Normalized actual: {normalized_actual}")
            print(f"   Normalized expected: {normalized_expected}")
            print(f"   Status: {status}")
            
            results[email] = {
                'status': 'correct' if tags_match else 'wrong',
                'tags': actual_tags,
                'expected': expected_tags
            }
        
        return results
    
    def fix_tags(self):
        """Fix subscriber tags if they're wrong."""
        print("\n" + "=" * 70)
        print("FIXING SUBSCRIBER TAGS")
        print("=" * 70)
        
        results = self.verify_tags()
        
        needs_fixing = [email for email, result in results.items() 
                       if result['status'] != 'correct']
        
        if not needs_fixing:
            print("\n✅ All subscribers have correct tags!")
            return
        
        print(f"\n⚠️  {len(needs_fixing)} subscriber(s) need tag fixes")
        
        for email in needs_fixing:
            config = self.test_subscribers[email]
            expected_tags = config['expected_tags']
            level = config['level']
            
            print(f"\n🔧 Fixing {email}...")
            
            # Delete and recreate with correct tags
            try:
                # Delete
                requests.delete(
                    f"{self.base_url}/subscribers/{email}",
                    headers=self.headers
                )
                print(f"   Deleted old subscriber")
                
                # Recreate with correct tags
                payload = {
                    'email': email,
                    'metadata': {
                        'difficulty_level': level,
                        'signup_source': 'test_setup',
                        'test_account': 'true'
                    },
                    'tags': expected_tags
                }
                
                response = requests.post(
                    f"{self.base_url}/subscribers",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                print(f"   ✅ Recreated with tags: {expected_tags}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    def generate_tag_format(self):
        """Generate recommended tag format for template."""
        print("\n" + "=" * 70)
        print("RECOMMENDED TAG FORMAT FOR JINJA2 TEMPLATE")
        print("=" * 70)
        
        print("\nUse these tags in Buttondown to match Jinja2 conditions:")
        print("\nTag names (lowercase, underscores):")
        print("  - level_easy")
        print("  - level_mid")
        print("  - level_hard")
        print("  - level_CN")
        
        print("\nIn your Jinja2 template, use:")
        print("""
{% if "level_easy" in subscriber.tags %}
    {{ article_body_easy }}
{% elif "level_mid" in subscriber.tags %}
    {{ article_body_mid }}
{% elif "level_hard" in subscriber.tags %}
    {{ article_body_hard }}
{% elif "level_CN" in subscriber.tags %}
    {{ article_body_CN }}
{% else %}
    <p>Please select a reading level on our website!</p>
{% endif %}
""")

def main():
    """Main execution."""
    
    api_token = os.getenv('BUTTONDOWN_API_TOKEN')
    if not api_token:
        print("❌ BUTTONDOWN_API_TOKEN not set!")
        print("\nSet it with:")
        print("  export BUTTONDOWN_API_TOKEN='your_token'")
        return
    
    verifier = SubscriberVerifier(api_token)
    
    # Show current tag status
    results = verifier.verify_tags()
    
    # Check if any need fixing
    needs_fixing = [email for email, result in results.items() 
                   if result['status'] != 'correct']
    
    if needs_fixing:
        print(f"\n⚠️  {len(needs_fixing)} subscriber(s) have incorrect tags")
        try:
            user_input = input("\nFix tags automatically? (yes/no): ").strip().lower()
            if user_input == 'yes':
                verifier.fix_tags()
            else:
                print("Skipped tag fixing.")
        except KeyboardInterrupt:
            print("\nCancelled.")
    else:
        print("\n✅ All subscribers have correct tags!")
    
    # Show recommended format
    verifier.generate_tag_format()
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
