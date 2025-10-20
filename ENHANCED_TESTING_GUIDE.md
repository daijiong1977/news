# 🧪 Enhanced System Testing Guide

## Quick Test Sequence (5 minutes)

### Step 1: Verify HTTP Server (Serving HTML)
```bash
# Should return HTML page content
curl -s http://localhost:8000/main_articles_interface_v2.html | head -20
```

**Expected**: HTML document starting with `<!DOCTYPE html>`

---

### Step 2: Verify Subscription Service is Running
```bash
# Check if service is listening on port 5001
lsof -i :5001
```

**Expected**: Python process (`python3`) listening on port 5001

**If NOT running**:
```bash
cd /Users/jidai/news
python3 subscription_service_enhanced.py &
sleep 2
```

---

### Step 3: Test /health Endpoint
```bash
curl -s http://localhost:5001/health
```

**Expected Response**:
```json
{"status": "ok"}
```

---

### Step 4: Test /categories Endpoint
```bash
curl -s http://localhost:5001/categories | python3 -m json.tool
```

**Expected Response** (6 categories):
```json
[
  {
    "id": 1,
    "name": "World",
    "emoji": "🌍",
    "description": "International news",
    "color": "#3498db",
    "website": "world"
  },
  {
    "id": 2,
    "name": "Science",
    "emoji": "🔬",
    "description": "Science news",
    "color": "#2ecc71",
    "website": "science"
  },
  ...
]
```

**If this works ✅**: Categories table is initialized correctly

---

### Step 5: Test /subscribe-enhanced Endpoint
```bash
curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.user@example.com",
    "name": "Test User",
    "age_group": "middle",
    "interests": [1, 2, 3],
    "frequency": "daily"
  }' | python3 -m json.tool
```

**Expected Response**:
```json
{
  "message": "Subscription created successfully",
  "difficulty_level": "medium"
}
```

**If this works ✅**: Subscription endpoint works correctly

---

### Step 6: Verify Database Update
```bash
# Check if subscription was stored
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT email, name, age_group, difficulty_level, interests FROM subscriptions_enhanced WHERE email='test.user@example.com';"
```

**Expected Output**:
```
test.user@example.com|Test User|middle|medium|[1, 2, 3]
```

---

### Step 7: Test Form in Browser
1. Open: `http://localhost:8000/main_articles_interface_v2.html`
2. Scroll to subscription form
3. Verify:
   - ✅ Email input field visible
   - ✅ Name input field visible
   - ✅ Age Group dropdown visible with options
   - ✅ Interests checkboxes loading with category names
   - ✅ Frequency radio buttons present
   - ✅ "Subscribe" button visible
4. Fill form with test data
5. Click Subscribe
6. Should see success message

---

## Full Test Scenario (10 minutes)

### Test Complete Workflow

#### Test Case 1: Subscribe with All Fields
```bash
# Test subscription with all fields
curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student.elementary@school.edu",
    "name": "Elementary Student",
    "age_group": "elementary",
    "interests": [1, 4],
    "frequency": "daily"
  }'

curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student.middle@school.edu",
    "name": "Middle School Student",
    "age_group": "middle",
    "interests": [2, 3],
    "frequency": "daily"
  }'

curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student.high@school.edu",
    "name": "High School Student",
    "age_group": "high",
    "interests": [1, 2, 3, 4],
    "frequency": "weekly"
  }'
```

#### Check Database Results
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT email, name, age_group, difficulty_level FROM subscriptions_enhanced ORDER BY created_at DESC LIMIT 3;"
```

**Expected**:
```
student.high@school.edu|High School Student|high|hard
student.middle@school.edu|Middle School Student|middle|medium
student.elementary@school.edu|Elementary Student|elementary|easy
```

---

### Test Case 2: Form Validation (Error Handling)

#### Missing Email
```bash
curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "name": "No Email",
    "age_group": "middle",
    "interests": [1],
    "frequency": "daily"
  }'
```

**Expected**: Error message about missing email

#### Missing Name
```bash
curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "noname@example.com",
    "age_group": "middle",
    "interests": [1],
    "frequency": "daily"
  }'
```

**Expected**: Error message about missing name

#### No Interests Selected
```bash
curl -s -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nointerests@example.com",
    "name": "No Interests",
    "age_group": "middle",
    "interests": [],
    "frequency": "daily"
  }'
```

**Expected**: Error about minimum 1 interest required

---

## DeepSeek Integration Tests (When Ready)

### Test Case 3: Generate Batch Prompt

```bash
curl -s -X POST http://localhost:5001/generate-deepseek-summaries \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 6,
    "title": "Historic Swimming Championship",
    "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua..."
  }' | head -100
```

**Expected**: Returns a prompt template (first 100 chars should be a prompt instruction)

### Test Case 4: Store Summaries (After DeepSeek)

```bash
curl -s -X POST http://localhost:5001/store-summaries \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 6,
    "summaries": {
      "elementary": {
        "summary_en": "Simple summary for elementary...",
        "summary_zh": "简单总结为小学...",
        "keywords": ["swimming", "championship"],
        "questions": [...]
      },
      "middle": { ... },
      "high": { ... }
    }
  }'
```

**Expected**: Success message, data stored in database

---

## Database Verification Commands

### Check All Tables
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  ".tables"
```

**Expected Output**:
```
article_summaries  categories         email_logs         quiz_questions
subscriptions_enhanced  articles_enhanced
```

### Check Categories
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT id, name, emoji FROM categories;"
```

**Expected**: 6 categories with emoji

### Check Subscriptions
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  ".mode column"
  "SELECT email, name, age_group, difficulty_level, frequency FROM subscriptions_enhanced;"
```

### Check Article Summaries (After DeepSeek)
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT article_id, difficulty, COUNT(*) as languages FROM article_summaries GROUP BY article_id, difficulty;"
```

---

## Troubleshooting Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Service not responding | `lsof -i :5001` | Restart: `python3 subscription_service_enhanced.py &` |
| Categories not loading | `curl http://localhost:5001/categories` | Check database initialized |
| Form submission fails | Browser console errors | Check network tab, verify service running |
| Database locked | Try query after test | Close other sqlite connections |
| HTTP 405 error | Check request method (GET vs POST) | Use correct method for endpoint |

---

## Success Checklist

- [ ] HTTP server running on port 8000
- [ ] Subscription service running on port 5001
- [ ] /health endpoint returns `{"status": "ok"}`
- [ ] /categories returns 6 categories with emojis
- [ ] /subscribe-enhanced accepts all fields
- [ ] Subscriptions stored in database
- [ ] Age group correctly maps to difficulty level
- [ ] Form displays in browser with all fields
- [ ] Form submission works from browser
- [ ] Database shows new subscriptions

---

## Browser Test Checklist

**URL**: `http://localhost:8000/main_articles_interface_v2.html`

**Visible Elements**:
- [ ] Header with "Daily Digest" title
- [ ] Category filter buttons (World, Science, Tech, Sports)
- [ ] Article cards displaying
- [ ] Subscription section visible
- [ ] Email input field
- [ ] Name input field
- [ ] Age Group dropdown (Elementary, Middle School, High School)
- [ ] Interest checkboxes (loading from API)
- [ ] Frequency selection (Daily/Weekly)
- [ ] Subscribe button

**Interactions**:
- [ ] Click category buttons → filters articles
- [ ] Select age group → dropdown opens
- [ ] Check interests → checkboxes update
- [ ] Fill form → Submit button enables
- [ ] Submit form → Success message appears
- [ ] Check network tab → POST to /subscribe-enhanced sent
- [ ] Refresh page → New subscription form appears

