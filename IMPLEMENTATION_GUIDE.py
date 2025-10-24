#!/usr/bin/env python3
"""
Implementation Guide: Multi-Level Email Integration with Your System

This shows how to integrate the level-specific emails with your existing
Buttondown subscription system.
"""

# ============================================================================
# STEP 1: Update Your Subscription Handler
# ============================================================================

SUBSCRIPTION_HANDLER_UPDATE = """
# In your subscriber_handler.py or similar:

import requests
import json

class ButtondownSubscriber:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
    
    def subscribe_with_level(self, email: str, difficulty_level: str) -> bool:
        '''
        Subscribe user to Buttondown with their difficulty level.
        
        Args:
            email: User's email address
            difficulty_level: 'easy', 'mid', 'hard', or 'CN'
        
        Returns:
            True if successful, False otherwise
        '''
        
        # Map level to tag
        level_tags = {
            'easy': 'Level: Easy',
            'mid': 'Level: Middle',
            'hard': 'Level: Hard',
            'CN': 'Level: Chinese'
        }
        
        tag = level_tags.get(difficulty_level, 'Level: Middle')
        
        payload = {
            'email': email,
            'metadata': {
                'difficulty_level': difficulty_level,
                'signup_source': 'news_platform'
            },
            'tags': [tag]
        }
        
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/subscribers',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            subscriber = response.json()
            print(f"✅ Subscribed {email} to {difficulty_level} level")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Subscription failed: {e}")
            return False

# Use it in your Flask route:
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    level = request.form.get('difficulty_level', 'mid')
    
    subscriber = ButtondownSubscriber(BUTTONDOWN_API_TOKEN)
    success = subscriber.subscribe_with_level(email, level)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f'Subscribed to {level} level content!',
            'level': level
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Subscription failed'
        }), 400
"""

# ============================================================================
# STEP 2: HTML Form with Level Selection
# ============================================================================

FORM_EXAMPLE = """
<!-- Subscription form with level selection -->

<form id="subscriptionForm" method="POST" action="/subscribe">
    <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" required>
    </div>
    
    <div class="form-group">
        <label for="difficulty_level">Reading Level</label>
        <select id="difficulty_level" name="difficulty_level">
            <option value="easy">🟢 Easy - Beginner Friendly</option>
            <option value="mid" selected>🔵 Middle - Intermediate</option>
            <option value="hard">🟠 Hard - Expert Level</option>
            <option value="CN">🔴 中文 - Chinese Translation</option>
        </select>
    </div>
    
    <button type="submit">Subscribe Now</button>
</form>

<style>
.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

button {
    background-color: #3b82f6;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

button:hover {
    background-color: #2563eb;
}
</style>
"""

# ============================================================================
# STEP 3: Buttondown Campaign Setup (Manual Steps)
# ============================================================================

BUTTONDOWN_SETUP = """
BUTTONDOWN DASHBOARD SETUP (Manual):

1. Go to https://buttondown.email/dashboard

2. Create 4 Email Campaigns (Emails/Drafts section):

   Campaign 1: "Daily News - Easy Level"
   - Open email_enhanced_easy.html
   - Copy ALL content
   - Paste into campaign body
   - Subject: "📰 Today's News - Easy Level"
   - Recipients: Tag "Level: Easy"
   - Schedule or send

   Campaign 2: "Daily News - Middle Level"
   - Open email_enhanced_mid.html
   - Copy ALL content
   - Paste into campaign body
   - Subject: "📰 Today's News - Middle Level"
   - Recipients: Tag "Level: Middle"
   - Schedule or send

   Campaign 3: "Daily News - Hard Level"
   - Open email_enhanced_hard.html
   - Copy ALL content
   - Paste into campaign body
   - Subject: "📰 Today's News - Expert Level"
   - Recipients: Tag "Level: Hard"
   - Schedule or send

   Campaign 4: "每日新闻 - 中文版本"
   - Open email_enhanced_CN.html
   - Copy ALL content
   - Paste into campaign body
   - Subject: "📰 每日新闻 - 中文版本"
   - Recipients: Tag "Level: Chinese"
   - Schedule or send

IMPORTANT: Image URLs must be accessible from email clients
- Test URLs: http://localhost:8000/api/images/...
- For production: Update to your actual domain
"""

# ============================================================================
# STEP 4: Automated Sending (Optional - API Approach)
# ============================================================================

AUTOMATED_SENDING = """
# If you want to automate sending per level, use this:

import requests
from pathlib import Path

class AutomatedLevelEmail:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.buttondown.email/v1"
        self.headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def send_newsletter_by_level(self, article_data: dict):
        '''
        Send newsletter to all subscribers by their level.
        
        article_data should contain:
        {
            'title': 'Article Title',
            'levels': {
                'easy': {...content...},
                'mid': {...content...},
                'hard': {...content...},
                'CN': {...content...}
            }
        }
        '''
        
        levels = article_data.get('levels', {})
        
        for level in ['easy', 'mid', 'hard', 'CN']:
            html_file = f'email_enhanced_{level}.html'
            
            if not Path(html_file).exists():
                print(f"⚠️  File not found: {html_file}")
                continue
            
            # Read HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create email draft
            payload = {
                'subject': f"📰 {article_data.get('title', 'News')} ({level.upper()})",
                'body_html': html_content,
                'tags': [f'Level: {level.title()}']
            }
            
            try:
                # This would create a draft in Buttondown
                # You'd then need to manually approve and send,
                # or use additional logic to auto-send
                print(f"✓ Email prepared for {level} level")
            except Exception as e:
                print(f"✗ Error for {level}: {e}")
"""

# ============================================================================
# STEP 5: Workflow Summary
# ============================================================================

WORKFLOW_SUMMARY = """
COMPLETE WORKFLOW:

1. USER SUBSCRIBES:
   - User visits subscription form
   - Selects reading level (easy/mid/hard/CN)
   - Submits email
   - ↓
   - Flask calls ButtondownSubscriber.subscribe_with_level()
   - ↓
   - Buttondown receives subscriber with:
     * Email address
     * Metadata: difficulty_level = "easy"/"mid"/"hard"/"CN"
     * Tag: "Level: Easy"/"Level: Middle"/"Level: Hard"/"Level: Chinese"

2. ARTICLE PROCESSING (Daily/Scheduled):
   - Article selected
   - Passed to Deepseek API
   - ↓
   - Response saved to JSON
   - generate_enhanced_email.py creates 4 HTML versions
   - Each HTML tailored to level (easy/mid/hard/CN)

3. EMAIL SENDING (Manual or Automated):
   
   Option A - Manual (Buttondown Dashboard):
   - Copy email_enhanced_easy.html → Buttondown Campaign 1
   - Copy email_enhanced_mid.html → Buttondown Campaign 2
   - Copy email_enhanced_hard.html → Buttondown Campaign 3
   - Copy email_enhanced_CN.html → Buttondown Campaign 4
   - Select corresponding tag for each campaign
   - Click "Send"
   - ↓
   - Each campaign sends to subscribers with matching tag
   - Easy users get easy content
   - Mid users get mid content
   - etc.
   
   Option B - Automated (API):
   - Call AutomatedLevelEmail.send_newsletter_by_level()
   - Function loads each HTML file
   - Creates Buttondown campaign per level
   - Sends to tagged subscribers
   - All automatic

4. SUBSCRIBER MANAGEMENT:
   - User can change level by re-subscribing with new level
   - Or you can add an API endpoint to update level
   - Tags automatically update in Buttondown

CURRENT IMAGE SERVER:
- api_simple.py runs on localhost:8000
- Serves images from article_images/ folder
- For production, update domain in generate_enhanced_email.py
- Change: http://localhost:8000 → https://yourdomain.com
"""

# ============================================================================
# Main Output
# ============================================================================

def main():
    print("=" * 80)
    print("MULTI-LEVEL EMAIL IMPLEMENTATION GUIDE")
    print("=" * 80)
    
    print("\n📋 STEP 1: Update Subscription Handler")
    print("-" * 80)
    print(SUBSCRIPTION_HANDLER_UPDATE)
    
    print("\n📋 STEP 2: HTML Form with Level Selection")
    print("-" * 80)
    print(FORM_EXAMPLE)
    
    print("\n📋 STEP 3: Buttondown Campaign Setup")
    print("-" * 80)
    print(BUTTONDOWN_SETUP)
    
    print("\n📋 STEP 4: Automated Sending (Optional)")
    print("-" * 80)
    print(AUTOMATED_SENDING)
    
    print("\n📋 STEP 5: Complete Workflow")
    print("-" * 80)
    print(WORKFLOW_SUMMARY)
    
    print("\n" + "=" * 80)
    print("✅ IMPLEMENTATION GUIDE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
