#!/usr/bin/env python3
"""
Send Multi-Level Campaigns to Test Subscribers

Creates and sends 4 separate campaigns (one per difficulty level)
to the corresponding test subscribers.
"""

import requests
import json
from typing import Dict, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class ButtondownCampaignSender:
    """Send campaigns to test subscribers by level."""
    
    def __init__(self, api_token: str):
        """Initialize with API token."""
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        self.campaigns = {
            'easy': {
                'subject': '📰 Daily News - Easy Level 🟢',
                'html_file': 'email_enhanced_easy.html',
                'tag': 'Level: Easy',
                'description': 'Beginner-friendly news summary'
            },
            'mid': {
                'subject': '📰 Daily News - Middle Level 🔵',
                'html_file': 'email_enhanced_mid.html',
                'tag': 'Level: Middle',
                'description': 'Intermediate-level news analysis'
            },
            'hard': {
                'subject': '📰 Daily News - Hard Level 🟠',
                'html_file': 'email_enhanced_hard.html',
                'tag': 'Level: Hard',
                'description': 'Expert-level detailed analysis'
            },
            'CN': {
                'subject': '📰 每日新闻 - 中文版本 🔴',
                'html_file': 'email_enhanced_CN.html',
                'tag': 'Level: Chinese',
                'description': '完整的中文翻译和分析'
            }
        }
    
    def read_html_file(self, filename: str) -> Optional[str]:
        """Read HTML file content."""
        try:
            path = Path(filename)
            if not path.exists():
                print(f"❌ File not found: {filename}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return None
    
    def create_draft(self, level: str) -> Optional[str]:
        """
        Create an email draft for a level.
        
        Returns:
            Draft ID if successful, None otherwise
        """
        config = self.campaigns.get(level)
        if not config:
            print(f"❌ Unknown level: {level}")
            return None
        
        html_content = self.read_html_file(config['html_file'])
        if not html_content:
            return None
        
        payload = {
            'subject': config['subject'],
            'body_html': html_content,
            'metadata': {
                'level': level,
                'type': 'multi_level_campaign',
                'created_by': 'test_setup'
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/emails",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            draft = response.json()
            draft_id = draft.get('id')
            print(f"✅ Draft created for {level}: {draft_id}")
            return draft_id
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating draft for {level}: {e}")
            return None
    
    def get_subscriber_list(self, tag: str) -> Optional[str]:
        """
        Get subscriber list ID filtered by tag.
        
        Note: Buttondown doesn't have built-in subscriber lists by tag.
        This is for reference - sending will be manual or API-based filtering.
        """
        # In Buttondown, filtering is done at send time
        # This function documents the process
        print(f"📋 Subscribers with tag '{tag}' will receive this campaign")
        return tag
    
    def prepare_campaign(self, level: str) -> Dict:
        """
        Prepare a campaign for sending.
        
        Returns dict with campaign info for manual sending.
        """
        config = self.campaigns.get(level)
        if not config:
            return {}
        
        draft_id = self.create_draft(level)
        
        return {
            'level': level,
            'draft_id': draft_id,
            'subject': config['subject'],
            'tag': config['tag'],
            'description': config['description'],
            'html_file': config['html_file'],
            'status': 'ready_to_send' if draft_id else 'failed'
        }
    
    def prepare_all_campaigns(self) -> Dict:
        """Prepare all 4 campaigns."""
        print("\n📧 Preparing Campaigns...")
        print("-" * 60)
        
        campaigns = {}
        for level in ['easy', 'mid', 'hard', 'CN']:
            campaign = self.prepare_campaign(level)
            campaigns[level] = campaign
        
        return campaigns
    
    def send_instructions(self):
        """Print manual sending instructions."""
        print("\n" + "=" * 60)
        print("📧 CAMPAIGN SENDING INSTRUCTIONS")
        print("=" * 60)
        
        print("\nDrafts have been created! Now follow these steps:")
        print("\n1. Go to https://buttondown.email/dashboard")
        print("2. Go to 'Emails' section")
        print("\nFor EACH campaign:")
        print("-" * 60)
        print("\n📧 Campaign 1: Easy Level")
        print("   - Find draft with subject: '📰 Daily News - Easy Level 🟢'")
        print("   - Click 'Send'")
        print("   - Choose 'Send to specific subscribers'")
        print("   - Select subscribers with tag: 'Level: Easy'")
        print("   - Send!")
        
        print("\n📧 Campaign 2: Middle Level")
        print("   - Find draft with subject: '📰 Daily News - Middle Level 🔵'")
        print("   - Click 'Send'")
        print("   - Choose 'Send to specific subscribers'")
        print("   - Select subscribers with tag: 'Level: Middle'")
        print("   - Send!")
        
        print("\n📧 Campaign 3: Hard Level")
        print("   - Find draft with subject: '📰 Daily News - Hard Level 🟠'")
        print("   - Click 'Send'")
        print("   - Choose 'Send to specific subscribers'")
        print("   - Select subscribers with tag: 'Level: Hard'")
        print("   - Send!")
        
        print("\n📧 Campaign 4: Chinese Level")
        print("   - Find draft with subject: '📰 每日新闻 - 中文版本 🔴'")
        print("   - Click 'Send'")
        print("   - Choose 'Send to specific subscribers'")
        print("   - Select subscribers with tag: 'Level: Chinese'")
        print("   - Send!")
        
        print("\n" + "=" * 60)
        print("Expected Results:")
        print("  - easy@daijiong.com receives easy version")
        print("  - mid@daijiong.com receives middle version")
        print("  - diff@daijiong.com receives hard version")
        print("  - cn@daijiong.com receives Chinese version")
        print("=" * 60)

def main():
    """Main execution."""
    
    api_token = os.getenv('BUTTONDOWN_API_TOKEN')
    if not api_token:
        print("❌ BUTTONDOWN_API_TOKEN not set!")
        print("Run: export BUTTONDOWN_API_TOKEN='your_token'")
        return
    
    print("=" * 60)
    print("BUTTONDOWN CAMPAIGN SENDER")
    print("=" * 60)
    
    sender = ButtondownCampaignSender(api_token)
    
    # Prepare all campaigns
    campaigns = sender.prepare_all_campaigns()
    
    print("\n📊 Campaign Summary:")
    print("-" * 60)
    for level, campaign in campaigns.items():
        status = "✅" if campaign.get('status') == 'ready_to_send' else "❌"
        print(f"{status} {level.upper()}: {campaign.get('subject')}")
        if campaign.get('draft_id'):
            print(f"   Draft ID: {campaign['draft_id']}")
        print(f"   Tag: {campaign.get('tag')}")
        print()
    
    # Print sending instructions
    sender.send_instructions()
    
    print("\n✅ Campaign preparation complete!")

if __name__ == "__main__":
    main()
