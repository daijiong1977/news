# Using Conditional Email Template with Buttondown

## Overview
This approach uses a SINGLE HTML template with Jinja2 conditional logic.
Each subscriber receives the SAME email HTML, but Buttondown renders
different content based on their tags.

## Setup Steps

### 1. Verify Subscriber Tags
Make sure each subscriber has the correct tag:
```
easy@daijiong.com     → Tag: level_easy
mid@daijiong.com      → Tag: level_mid
diff@daijiong.com     → Tag: level_hard
cn@daijiong.com       → Tag: level_CN
```

Run to verify:
```bash
python3 verify_subscriber_tags.py
```

### 2. Copy Template to Buttondown
1. Go to Buttondown Dashboard
2. Create new Email Draft
3. Copy entire content of `email_template_conditional.html`
4. Paste into Buttondown editor
5. Click "Save as Draft"

### 3. Add Template Variables
In Buttondown email editor:

Find this section:
```
{% if "level_easy" in subscriber.tags %}
    {{ article_body_easy }}
```

Replace with the article HTML from template_variables.json or template_variables.py

### 4. Test Template
Buttondown has a template preview feature:
1. In email editor, click "Preview"
2. Select each test subscriber
3. Verify correct content shows for each level

### 5. Send
- Select "Send to specific subscribers" or schedule
- Buttondown will automatically:
  - Check subscriber tags
  - Render appropriate {% if %} block
  - Show correct article_body_* variable
  - Send personalized HTML to each subscriber

## How It Works

```
Buttondown Email Template (Single File)
├─ {% if "level_easy" in subscriber.tags %}
│  └─ Shows: article_body_easy (beginner content)
├─ {% elif "level_mid" in subscriber.tags %}
│  └─ Shows: article_body_mid (intermediate content)
├─ {% elif "level_hard" in subscriber.tags %}
│  └─ Shows: article_body_hard (expert content)
├─ {% elif "level_CN" in subscriber.tags %}
│  └─ Shows: article_body_CN (Chinese content)
└─ {% else %}
   └─ Shows: Warning message

When sending:
1. Buttondown checks each subscriber's tags
2. Evaluates the Jinja2 conditions
3. Renders the matching {{ article_body_* }} block
4. Sends personalized HTML to subscriber
```

## Subscriber Receives

```
easy@daijiong.com:
  ├─ Header: 🟢 Easy Level (green)
  ├─ Content: article_body_easy (beginner version)
  └─ Footer: Standard

mid@daijiong.com:
  ├─ Header: 🔵 Middle Level (blue)
  ├─ Content: article_body_mid (intermediate version)
  └─ Footer: Standard

diff@daijiong.com:
  ├─ Header: 🟠 Hard Level (orange)
  ├─ Content: article_body_hard (expert version)
  └─ Footer: Standard

cn@daijiong.com:
  ├─ Header: 🔴 中文版本 (red, Chinese)
  ├─ Content: article_body_CN (Chinese version)
  └─ Footer: Standard
```

## Files Used

| File | Purpose |
|------|---------|
| `email_template_conditional.html` | Main template with Jinja2 logic |
| `template_variables.json` | Article content as JSON |
| `template_variables.py` | Article content as Python variables |
| `verify_subscriber_tags.py` | Verify tags are set correctly |

## Testing

### Before Sending
1. Verify tags: `python3 verify_subscriber_tags.py`
2. Preview in Buttondown with each test subscriber
3. Confirm correct content shows for each level

### After Sending
1. Check test email accounts
2. Verify each gets correct difficulty level
3. Verify images load
4. Verify formatting looks good

## Advantages of This Approach

✅ Single template to manage
✅ Automatic level detection based on tags
✅ Easy to update (change once, applies to all)
✅ Scales to thousands of subscribers
✅ No manual campaign per level needed
✅ Built-in preview/testing in Buttondown

## Next Steps

1. Run: `python3 verify_subscriber_tags.py`
2. Copy `email_template_conditional.html` to Buttondown
3. Replace `{{ article_body_* }}` placeholders with actual HTML
4. Test in Buttondown preview
5. Send to test subscribers
6. Verify correct levels received

