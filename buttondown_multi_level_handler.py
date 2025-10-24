#!/usr/bin/env python3
"""
Buttondown Multi-Level Email Handler

Manages subscriber levels and sends appropriate content based on user difficulty level.
Two strategies:
1. Store level in Buttondown metadata
2. Send via separate campaigns per level
"""

import requests
import json
from typing import Optional, Dict, List
from pathlib import Path

class ButtondownMultiLevelManager:
    """Manage Buttondown subscribers with different difficulty levels."""
    
    def __init__(self, api_token: str):
        """Initialize with Buttondown API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_level_tags(self) -> Dict[str, str]:
        """Create tags in Buttondown for each difficulty level."""
        tags = {
            'easy': 'Level: Easy',
            'mid': 'Level: Middle',
            'hard': 'Level: Hard',
            'CN': 'Level: Chinese'
        }
        
        print("📌 Tag Strategy (for subscriber organization):")
        for level, tag_name in tags.items():
            print(f"  - {tag_name}: {level}")
        
        return tags
    
    def subscribe_with_level(self, email: str, level: str) -> Dict:
        """
        Subscribe a user to Buttondown with their difficulty level.
        
        Store level in metadata or as a tag depending on preference.
        """
        payload = {
            "email": email,
            "metadata": {
                "difficulty_level": level,  # Store level in metadata
                "subscribed_at": "auto"
            },
            "tags": [f"Level: {level.title()}"],  # Also add as tag
            "utm_source": "news_platform",
            "utm_medium": "email_subscription"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/subscribers",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error subscribing user: {e}")
            return None
    
    def get_subscribers_by_level(self, level: str) -> List[Dict]:
        """Get all subscribers for a specific difficulty level."""
        try:
            # Query by tag or metadata
            response = requests.get(
                f"{self.base_url}/subscribers",
                headers=self.headers,
                params={"tag": f"Level: {level.title()}"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching subscribers: {e}")
            return []
    
    def send_level_specific_email(self, level: str, subject: str, 
                                  html_file: str, unsubscribe_url: str = None) -> Dict:
        """
        Send email to all subscribers of a specific level.
        
        This creates a draft email that can be sent to level-specific subscribers.
        """
        
        # Read HTML content
        html_path = Path(html_file)
        if not html_path.exists():
            print(f"❌ HTML file not found: {html_file}")
            return None
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        payload = {
            "subject": subject,
            "body": html_content,
            "metadata": {
                "level": level,
                "type": "level_specific",
                "template_version": "enhanced_v1"
            }
        }
        
        print(f"📧 Email prepared for {level} subscribers:")
        print(f"   Subject: {subject}")
        print(f"   HTML size: {len(html_content)} bytes")
        print(f"   Recipients: All subscribers tagged 'Level: {level.title()}'")
        
        return payload
    
    @staticmethod
    def generate_campaign_strategy() -> str:
        """Generate a strategy document for multi-level campaigns."""
        
        strategy = """
# Buttondown Multi-Level Email Campaign Strategy

## Overview
Send level-specific content to subscribers based on their difficulty preference.

## Implementation Options

### Option 1: Separate Campaigns (RECOMMENDED)
- Create 4 separate email campaigns in Buttondown
- One campaign per difficulty level (Easy, Middle, Hard, Chinese)
- Tag subscribers by level when they subscribe
- Use Buttondown's "Send to tagged subscribers" feature
- Pros: Simple, reliable, clear separation
- Cons: Requires manual campaign management

**Steps:**
1. Create campaign "Daily News - Easy Level"
   - Copy content from email_enhanced_easy.html
   - Set tag filter: "Level: Easy"
   
2. Create campaign "Daily News - Middle Level"
   - Copy content from email_enhanced_mid.html
   - Set tag filter: "Level: Middle"
   
3. Create campaign "Daily News - Hard Level"
   - Copy content from email_enhanced_hard.html
   - Set tag filter: "Level: Hard"
   
4. Create campaign "每日新闻 - 中文版本"
   - Copy content from email_enhanced_CN.html
   - Set tag filter: "Level: Chinese"

### Option 2: Metadata-Based Template Variables
- Store level in subscriber metadata
- Use Buttondown template variables in HTML email
- Use conditional CSS/display based on data attributes
- Pros: Single campaign, automatic
- Cons: Limited customization, may need server-side rendering

Template example:
```html
<div class="easy-only" style="display: {show_if_level_equals_easy};">
  Easy content here
</div>
<div class="mid-only" style="display: {show_if_level_equals_mid};">
  Middle content here
</div>
```

### Option 3: Automated Buttondown API
- Use Buttondown API to programmatically send per-level
- Create subscription event that triggers level detection
- Automatically route to correct campaign
- Pros: Fully automated
- Cons: Requires backend automation

## Recommended Workflow

1. **Subscription Flow:**
   ```
   User selects level → API stores in Buttondown metadata + tags
   → User added to "Level: Easy/Mid/Hard/CN" tag
   ```

2. **Email Sending Flow:**
   ```
   Article processed by Deepseek → Generate 4 HTML versions
   → Create/Update 4 Buttondown drafts → Send to tagged subscribers
   ```

3. **Subscriber Management:**
   - Level stored in Buttondown metadata (difficulty_level)
   - Also tagged for easy filtering (Level: Easy, Level: Middle, etc.)
   - Can update level anytime by changing tag/metadata

## Implementation with Your System

### Current Setup:
- Article processing → JSON payloads per level
- 4 HTML files generated (easy/mid/hard/CN)
- Image server provides URLs

### What Needs to Change:
1. Update subscription handler to store level in Buttondown
2. Create function to send different content per level
3. Setup Buttondown campaigns (or use API to send programmatically)

### Example Code Flow:

```python
# When user subscribes
user_level = request.form.get('level', 'mid')
email = request.form.get('email')

manager = ButtondownMultiLevelManager(api_token)
manager.subscribe_with_level(email, user_level)
# → Stores in Buttondown with tag + metadata

# When sending newsletter
for level in ['easy', 'mid', 'hard', 'CN']:
    html_file = f'email_enhanced_{level}.html'
    subject = get_subject_for_level(level)
    
    manager.send_level_specific_email(
        level=level,
        subject=subject,
        html_file=html_file
    )
    # → Sends to all subscribers with "Level: {level}" tag
```

## Buttondown Tags Needed:
- `Level: Easy`
- `Level: Middle`
- `Level: Hard`
- `Level: Chinese`

## Testing:
1. Subscribe test account with each level
2. Verify tags appear in Buttondown dashboard
3. Send manual campaigns to each tag group
4. Verify content arrives correctly per level

## Future Enhancement:
- Per-user level preference update endpoint
- Analytics tracking by level
- A/B testing different level combinations
- Automatic level suggestions based on reading time
"""
        
        return strategy

def main():
    """Demonstrate the multi-level email strategy."""
    
    print("🔧 Buttondown Multi-Level Email Strategy\n")
    
    # Show strategy
    strategy = ButtondownMultiLevelManager.generate_campaign_strategy()
    
    # Save strategy document
    with open('BUTTONDOWN_MULTI_LEVEL_STRATEGY.md', 'w') as f:
        f.write(strategy)
    
    print(strategy)
    
    print("\n✅ Strategy document saved to: BUTTONDOWN_MULTI_LEVEL_STRATEGY.md")
    print("\n📋 Next Steps:")
    print("1. Review the strategy document")
    print("2. Choose implementation option (Recommended: Separate Campaigns)")
    print("3. Update subscription handler to store level in Buttondown")
    print("4. Create 4 campaigns in Buttondown dashboard (one per level)")
    print("5. Update email sending to route by subscriber level")

if __name__ == "__main__":
    main()
