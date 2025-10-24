# ✅ Single Conditional Template Setup Guide

## What Changed

**OLD APPROACH:** 4 separate HTML files, 4 separate campaigns
**NEW APPROACH:** 1 HTML template with Jinja2 conditional logic

```
One Email Template + Subscriber Tags
         ↓
Buttondown renders different content per subscriber
         ↓
Each subscriber sees their own difficulty level
```

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `email_template_conditional.html` | Main template with Jinja2 logic | ✅ Ready |
| `verify_subscriber_tags.py` | Verify tags in Buttondown | ✅ Ready |
| `extract_template_variables.py` | Extract article content | ✅ Ready |
| `CONDITIONAL_TEMPLATE_GUIDE.md` | Detailed usage guide | ✅ Ready |

---

## How It Works

### The Template Uses Jinja2 Conditions:

```jinja2
{% if "level_easy" in subscriber.tags %}
    <!-- Shows easy content -->
    {{ article_body_easy }}
{% elif "level_mid" in subscriber.tags %}
    <!-- Shows middle content -->
    {{ article_body_mid }}
{% elif "level_hard" in subscriber.tags %}
    <!-- Shows hard content -->
    {{ article_body_hard }}
{% elif "level_CN" in subscriber.tags %}
    <!-- Shows Chinese content -->
    {{ article_body_CN }}
{% else %}
    <!-- Fallback for no tags -->
    <p>Please select a reading level</p>
{% endif %}
```

### Subscriber Tags Must Be Set:

```
easy@daijiong.com   → Tag: level_easy
mid@daijiong.com    → Tag: level_mid
diff@daijiong.com   → Tag: level_hard
cn@daijiong.com     → Tag: level_CN
```

---

## Step-by-Step Setup

### Step 1️⃣: Set Your API Token
```bash
export BUTTONDOWN_API_TOKEN='your_token_here'
```

Get token from: https://buttondown.email/settings/api

### Step 2️⃣: Verify Subscriber Tags
```bash
python3 verify_subscriber_tags.py
```

This will:
- ✅ Check if all 4 subscribers exist
- ✅ Check if they have correct tags
- ✅ Fix tags automatically if wrong
- ✅ Show Jinja2 condition format

Output should look like:
```
✅ CORRECT: easy@daijiong.com
   Level: easy
   Expected tags: ['level_easy']
   Actual tags: ['level_easy']
   Status: ✅ OK
```

### Step 3️⃣: Extract Template Variables
```bash
python3 extract_template_variables.py
```

This creates:
- `template_variables.py` - Article HTML in Python
- `template_variables.json` - Article HTML in JSON
- `CONDITIONAL_TEMPLATE_GUIDE.md` - Full instructions

### Step 4️⃣: Use the Template in Buttondown

1. Go to: https://buttondown.email/dashboard
2. Click **"New Email"**
3. Open `email_template_conditional.html`
4. Copy all the HTML
5. Paste into Buttondown editor
6. Replace `{{ article_body_easy }}` with actual article HTML

### Step 5️⃣: Add Article Content

In the template, you'll see:
```jinja2
{% if "level_easy" in subscriber.tags %}
    {{ article_body_easy }}
{% endif %}
```

Replace `{{ article_body_easy }}` with the actual article HTML:

```bash
# View what to insert:
cat template_variables.json
```

Copy the HTML from:
- `template_variables.json` → look in `variables.article_body_easy`

Or use Python:
```python
from template_variables import article_body_easy, article_body_mid, article_body_hard, article_body_CN

print(article_body_easy)  # See the exact HTML
```

### Step 6️⃣: Test in Buttondown

Before sending:
1. In Buttondown, click **"Preview"**
2. Select each test subscriber
3. Verify correct content shows:
   - easy@daijiong.com → shows easy content
   - mid@daijiong.com → shows mid content
   - diff@daijiong.com → shows hard content
   - cn@daijiong.com → shows Chinese content

### Step 7️⃣: Send

1. In Buttondown, click **"Send"**
2. Choose **"Subscribers"** or **"All Subscribers"**
3. Click **"Send"**

Buttondown will:
- Evaluate Jinja2 conditions for each subscriber
- Render appropriate article content
- Send personalized email to each subscriber

---

## Testing Checklist

Before sending, verify:

- [ ] API token is set: `echo $BUTTONDOWN_API_TOKEN`
- [ ] Tags verified: `python3 verify_subscriber_tags.py` shows all ✅
- [ ] Template variables extracted: `python3 extract_template_variables.py` succeeds
- [ ] Template copied to Buttondown
- [ ] Article content inserted (not the `{{ }}` placeholders)
- [ ] Preview shows different content for each subscriber
- [ ] Images show in preview
- [ ] Text formatting looks good

After sending:
- [ ] easy@daijiong.com received easy version
- [ ] mid@daijiong.com received mid version
- [ ] diff@daijiong.com received hard version
- [ ] cn@daijiong.com received Chinese version
- [ ] Images loaded correctly
- [ ] Header color matches level (green/blue/orange/red)

---

## Buttondown Tag Format

**Important:** Tags must use lowercase with underscores:

```
❌ WRONG:
  Level: Easy
  Level: Middle
  Level: Hard

✅ CORRECT:
  level_easy
  level_mid
  level_hard
  level_CN
```

The `verify_subscriber_tags.py` script will fix this automatically if wrong.

---

## Template Structure

```
email_template_conditional.html
├─ Header (changes color per level)
│  ├─ Green (🟢) for easy
│  ├─ Blue (🔵) for mid
│  ├─ Orange (🟠) for hard
│  └─ Red (🔴) for Chinese
├─ Featured Article Section
│  └─ {% if subscriber.tags %} conditional
│     ├─ {{ article_body_easy }}
│     ├─ {{ article_body_mid }}
│     ├─ {{ article_body_hard }}
│     └─ {{ article_body_CN }}
├─ Category Tags (News, Science, Sports)
└─ Footer (standard)
```

---

## Advantages

✅ **Single Template** - Manage one file instead of 4
✅ **Automatic** - Buttondown handles everything
✅ **Scalable** - Works with any number of subscribers
✅ **Flexible** - Easy to update content for all subscribers at once
✅ **Reliable** - Tag-based routing is very stable
✅ **Professional** - Looks consistent across all levels

---

## Common Issues & Solutions

**Issue:** "Tag not recognized"
**Solution:** Use lowercase with underscores: `level_easy` not `Level: Easy`
Run: `python3 verify_subscriber_tags.py` to auto-fix

**Issue:** "Variables not showing in template"
**Solution:** Make sure to replace `{{ article_body_* }}` with actual HTML
Don't leave the `{{ }}` placeholders

**Issue:** "Preview shows fallback message"
**Solution:** Check subscriber tags are correct
Run: `python3 verify_subscriber_tags.py`

**Issue:** "Images not loading"
**Solution:** Check image URLs in the article HTML
May need to update from `localhost:8000` to production domain

---

## Next Actions

### Immediate (Required):
1. Set API token: `export BUTTONDOWN_API_TOKEN='your_token'`
2. Verify tags: `python3 verify_subscriber_tags.py`
3. Extract variables: `python3 extract_template_variables.py`
4. Copy template to Buttondown: `email_template_conditional.html`
5. Insert article content from `template_variables.json`
6. Test preview
7. Send

### Optional (For Reference):
- Read `CONDITIONAL_TEMPLATE_GUIDE.md` for full details
- Review `template_variables.py` for Python variable access
- Check `template_variables.json` for JSON format

### After Testing:
- Verify all 4 test emails received
- Check each has correct difficulty level
- Update domain if going to production
- Start collecting real subscribers

---

## Comparison: Old vs New

### Old Approach (4 Campaigns):
```
4 HTML files created
  ├─ email_enhanced_easy.html
  ├─ email_enhanced_mid.html
  ├─ email_enhanced_hard.html
  └─ email_enhanced_CN.html
        ↓
4 separate campaigns in Buttondown
  ├─ Campaign 1: Send to "Level: Easy" tag
  ├─ Campaign 2: Send to "Level: Middle" tag
  ├─ Campaign 3: Send to "Level: Hard" tag
  └─ Campaign 4: Send to "Level: Chinese" tag
        ↓
Manual: Send each campaign separately
```

### New Approach (1 Template):
```
1 conditional HTML template
  └─ email_template_conditional.html
        ↓
1 campaign in Buttondown
  └─ Send to all subscribers
        ↓
Automatic: Buttondown renders correct content per subscriber
  ├─ Checks subscriber tags
  ├─ Evaluates Jinja2 conditions
  ├─ Shows appropriate content
  └─ Sends personalized email
```

---

## Summary

| Aspect | Old | New |
|--------|-----|-----|
| HTML files | 4 | 1 |
| Buttondown campaigns | 4 | 1 |
| Manual steps | High | Low |
| Scalability | Per-level | Automatic |
| Update effort | 4 files | 1 file |
| Management | Complex | Simple |

---

## You're Ready! 🚀

Everything is prepared. Just need to:

```bash
# 1. Set token
export BUTTONDOWN_API_TOKEN='your_token'

# 2. Verify tags
python3 verify_subscriber_tags.py

# 3. Extract variables
python3 extract_template_variables.py

# 4. Copy template to Buttondown and replace variables
# 5. Test and send!
```

Good luck! 🎉
