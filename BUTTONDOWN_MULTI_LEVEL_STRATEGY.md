🔧 Buttondown Multi-Level Email Strategy


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


✅ Strategy document saved to: BUTTONDOWN_MULTI_LEVEL_STRATEGY.md

📋 Next Steps:
1. Review the strategy document
2. Choose implementation option (Recommended: Separate Campaigns)
3. Update subscription handler to store level in Buttondown
4. Create 4 campaigns in Buttondown dashboard (one per level)
5. Update email sending to route by subscriber level
