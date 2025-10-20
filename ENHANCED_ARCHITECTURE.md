# 🏗️ Enhanced System Architecture

## System Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                             │
│         (main_articles_interface_v2.html)                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Article Grid                                               │ │
│  │  - Category Filters (World/Science/Tech/Sports)            │ │
│  │  - Article Cards (title, image, summary, date)             │ │
│  │  - Read More buttons                                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  SUBSCRIPTION FORM (NEW)                                    │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │ Email: [___________________]  *required                 │ │ │
│  │  │ Name:  [___________________]  *required (NEW)           │ │ │
│  │  │ Age:   [▼ Elementary/Middle/High]  *required (NEW)      │ │ │
│  │  │                                                          │ │ │
│  │  │ Interests: (NEW - loaded from /categories)              │ │ │
│  │  │ ☐ 🌍 World    ☐ 🔬 Science   ☐ 💻 Technology           │ │ │
│  │  │ ☐ 🏊 Sports   ☐ 🎨 Life      ☐ 💰 Economy              │ │ │
│  │  │ (At least 1 required)                                   │ │ │
│  │  │                                                          │ │ │
│  │  │ Frequency:                                               │ │ │
│  │  │ ◉ Daily  ◯ Weekly  *required                            │ │ │
│  │  │                                                          │ │ │
│  │  │ [Subscribe Now]                                         │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              │
                    handleSubscribe()
                    (validate & POST)
                              │
                    ┌─────────▼─────────┐
                    │                   │
                ┌───▼───────────────────▼───┐
                │   FLASK BACKEND (port 5001)│
                │   (subscription_service_  │
                │    enhanced.py)           │
                └───┬─────────────────────┬─┘
                    │                     │
        ┌───────────┴─────────┐      ┌────┴──────────────┐
        │                     │      │                   │
    POST /subscribe-enhanced  GET /categories      POST endpoints
        │                     │      │                   │
        ▼                     ▼      ▼                   ▼
   ┌──────────┐          ┌─────────────────┐      ┌──────────────┐
   │ Validate │          │ Read categories │      │ DeepSeek API │
   │ fields   │          │ from DB         │      │ - Generate   │
   │ - Email  │          │ - All 6         │      │ - Store      │
   │ - Name   │          │ - Return JSON   │      │ - Summaries  │
   │ - Age    │          └─────────────────┘      └──────────────┘
   │ - Interests          
   │ - Frequency          
   └──────┬──────┘        
          │ Map age_group to difficulty_level
          │ elementary → easy
          │ middle → medium
          │ high → hard
          │
          ▼
    ┌──────────────────────────────────────┐
    │    SQLite Database (subscriptions.db) │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ categories (6 predefined)      │   │
    │  │ - id, name, emoji, color       │   │
    │  └────────────────────────────────┘   │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ articles_enhanced (per article)│   │
    │  │ - id, title, category_id       │   │
    │  │ - date, source, image, content │   │
    │  └────────────────────────────────┘   │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ article_summaries (NEW)        │   │
    │  │ - 3 levels × 2 languages       │   │
    │  │ - easy/medium/hard + en/zh     │   │
    │  │ - summary, keywords, background│   │
    │  │ - pro_arguments, con_arguments │   │
    │  └────────────────────────────────┘   │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ quiz_questions (NEW)           │   │
    │  │ - 3 levels (easy/medium/hard)  │   │
    │  │ - 5 questions per level        │   │
    │  │ - question, options, answer    │   │
    │  │ - explanation                  │   │
    │  └────────────────────────────────┘   │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ subscriptions_enhanced (NEW)   │   │
    │  │ - email, name, age_group       │   │
    │  │ - difficulty_level (auto set)  │   │
    │  │ - interests (JSON array)       │   │
    │  │ - frequency, status            │   │
    │  │ - created_at, last_sent        │   │
    │  └────────────────────────────────┘   │
    │                                       │
    │  ┌────────────────────────────────┐   │
    │  │ email_logs (NEW)               │   │
    │  │ - email, status, sent_at       │   │
    │  │ - email_id, age_group          │   │
    │  │ - difficulty_level             │   │
    │  └────────────────────────────────┘   │
    │                                       │
    └──────────────────────────────────────┘
                       │
                       │ (Later: email_scheduler.py)
                       │
                       ▼
           ┌───────────────────────────┐
           │   EMAIL DELIVERY         │
           │   (emailapi.6ray.com)    │
           │                           │
           │ - Query subscriptions    │
           │ - Filter by interests    │
           │ - Get summaries @ level  │
           │ - Generate personalized  │
           │   HTML (easy/med/hard)   │
           │ - Send via Email API     │
           │ - Log delivery status    │
           └───────────────────────────┘
```

---

## Data Flow: Article Processing

```
SOURCE: article_data_with_summaries.json
├── Article 6 (Swimming)
│   ├── ID: 6
│   ├── Title: "..."
│   ├── Content: "..."
│   └── Category: Sports (id=4)
│
└── Article 11 (Tech)
    ├── ID: 11
    ├── Title: "..."
    ├── Content: "..."
    └── Category: Technology (id=3)
                    │
                    │ POST /generate-deepseek-summaries
                    │ (creates batch prompt for 3 levels)
                    │
                    ▼
        ┌───────────────────────────┐
        │ DeepSeek API (chat model) │
        │ temperature: 0.7          │
        │ max_tokens: 8000          │
        │                           │
        │ Input: Batch prompt       │
        │ - Article content         │
        │ - 3 levels requested      │
        │ - 2 languages (en/zh)     │
        │ - 5 questions per level   │
        │                           │
        └───────────────────────────┘
                    │
                    │ Single response with all 3 levels
                    │
                    ▼
        ┌───────────────────────────────────────┐
        │ Response: JSON Object                 │
        │                                       │
        │ {                                     │
        │   "elementary": {                     │
        │     "summary_en": "Simple...",        │
        │     "summary_zh": "简单...",          │
        │     "keywords": [...],                │
        │     "questions": [                    │
        │       {question, options, answer}     │
        │       ... (5 total)                   │
        │     ]                                 │
        │   },                                  │
        │   "middle": { ... },                  │
        │   "high": {                           │
        │     "summary_en": "Advanced...",      │
        │     "summary_zh": "高级...",          │
        │     "keywords": [...],                │
        │     "background": "...",              │
        │     "pro_arguments": "...",           │
        │     "con_arguments": "...",           │
        │     "questions": [... (5)]            │
        │   }                                   │
        │ }                                     │
        │                                       │
        └───────────────────────────────────────┘
                    │
                    │ POST /store-summaries
                    │ (parse & save to DB)
                    │
                    ▼
        ┌───────────────────────────────────┐
        │ Database Storage                  │
        │                                   │
        │ article_summaries:                │
        │ ┌─────────────────────────────┐   │
        │ │ ID  Article  Difficulty     │   │
        │ ├─────────────────────────────┤   │
        │ │ 1   6        easy      (en) │   │
        │ │ 2   6        easy      (zh) │   │
        │ │ 3   6        medium    (en) │   │
        │ │ 4   6        medium    (zh) │   │
        │ │ 5   6        hard      (en) │   │
        │ │ 6   6        hard      (zh) │   │
        │ │ 7   11       easy      (en) │   │
        │ │ ... (continues for all)    │   │
        │ └─────────────────────────────┘   │
        │                                   │
        │ quiz_questions:                   │
        │ ┌─────────────────────────────┐   │
        │ │ ID  Article  Difficulty Q#  │   │
        │ ├─────────────────────────────┤   │
        │ │ 1   6        easy      1    │   │
        │ │ 2   6        easy      2    │   │
        │ │ ...                         │   │
        │ │ 5   6        easy      5    │   │
        │ │ 6   6        medium    1    │   │
        │ │ ...                         │   │
        │ │ 15  6        hard      5    │   │
        │ │ ... (continues)             │   │
        │ └─────────────────────────────┘   │
        │                                   │
        └───────────────────────────────────┘
```

---

## Form Field Validation Flow

```
User Input
    │
    ├─ Email
    │  │
    │  ▼
    │  Client: Non-empty? YES → Next
    │  Client: Valid format? YES → Next
    │  │
    │  ▼
    │  Server: Received? YES
    │  Server: Duplicate? NO → Continue
    │
    ├─ Name (NEW)
    │  │
    │  ▼
    │  Client: Non-empty? YES → Next
    │  Client: Length ≥ 3? YES → Next
    │  │
    │  ▼
    │  Server: Received? YES → Continue
    │
    ├─ Age Group (NEW)
    │  │
    │  ▼
    │  Client: Selected? YES (not placeholder) → Next
    │  │
    │  ▼
    │  Server: In list? YES
    │  Server: Map to difficulty:
    │         elementary → easy
    │         middle → medium
    │         high → hard
    │  │
    │  ▼
    │  Continue
    │
    ├─ Interests (NEW)
    │  │
    │  ▼
    │  Client: Any checked? YES (≥1) → Next
    │  │
    │  ▼
    │  Server: Array received? YES
    │  Server: Not empty? YES (≥1) → Continue
    │  Server: Each ID valid? YES (1-6) → Continue
    │
    ├─ Frequency
    │  │
    │  ▼
    │  Client: Selected? YES → Next
    │  │
    │  ▼
    │  Server: In list? YES (daily/weekly) → Continue
    │
    ▼
All Validated ✓
    │
    ▼
Store in DB:
├─ subscriptions_enhanced row
├─ SET status='active'
├─ SET created_at=NOW()
├─ SET difficulty_level=[mapped]
├─ SET interests=[JSON]
│
▼
Return Success
├─ Message: "Subscription created successfully"
├─ difficulty_level: "medium" (example)
│
▼
Show Alert to User
├─ Success message displays
├─ Form clears (optional)
└─ Ready for next subscription
```

---

## Request/Response Cycle

```
┌──────────────────────────────────────────────┐
│ Browser                                      │
│  1. GET /main_articles_interface_v2.html    │
│  2. Page loads, DOM ready                   │
│  3. loadCategories() called                 │
│     │                                       │
│     └─► GET /categories                    │
│         │                                  │
│         ▼                                  │
│         [Request goes to port 5001]        │
│                                            │
└──────────────────────────────────────────────┘
                        │
                        │ HTTP GET /categories
                        │
┌───────────────────────▼──────────────────────┐
│ Flask Server (port 5001)                    │
│                                              │
│ @app.route('/categories', methods=['GET'])  │
│ ├─ Query: SELECT * FROM categories          │
│ ├─ Format: [{"id":1, "name":"...", ...}]   │
│ └─ Return: JSON 200 OK                      │
│                                              │
└───────────────────────┬──────────────────────┘
                        │
                        │ JSON Response
                        │
┌───────────────────────▼──────────────────────┐
│ Browser                                      │
│                                              │
│ 4. loadCategories() receives JSON           │
│ 5. Parse response                           │
│ 6. Create checkboxes dynamically            │
│ 7. Insert into #interests-container         │
│ 8. Form now interactive                     │
│                                              │
└──────────────────────────────────────────────┘
                        │
                        │ User fills form and clicks Subscribe
                        │
┌───────────────────────▼──────────────────────┐
│ Browser                                      │
│                                              │
│ 9. handleSubscribe() called                 │
│ 10. Validate all fields                     │
│ 11. Collect form values:                    │
│     ├─ email: "user@example.com"            │
│     ├─ name: "John Doe"                     │
│     ├─ age_group: "middle"                  │
│     ├─ interests: [1, 2, 4]                 │
│     └─ frequency: "daily"                   │
│ 12. POST /subscribe-enhanced                │
│     │                                       │
│     └─► JSON Body sent to port 5001         │
│                                              │
└──────────────────────────────────────────────┘
                        │
                        │ HTTP POST /subscribe-enhanced
                        │ Content-Type: application/json
                        │
┌───────────────────────▼──────────────────────┐
│ Flask Server (port 5001)                    │
│                                              │
│ @app.route('/subscribe-enhanced', POST)    │
│ ├─ Parse JSON request body                 │
│ ├─ Validate all fields (server-side)       │
│ ├─ Check for duplicate email               │
│ ├─ Map age_group to difficulty_level       │
│ ├─ Serialize interests as JSON             │
│ ├─ INSERT into subscriptions_enhanced      │
│ ├─ Commit transaction                       │
│ └─ Return: {                                │
│     "message": "...",                       │
│     "difficulty_level": "medium"            │
│   }                                         │
│                                              │
└───────────────────────┬──────────────────────┘
                        │
                        │ JSON Response 201 Created
                        │
┌───────────────────────▼──────────────────────┐
│ Browser                                      │
│                                              │
│ 13. handleSubscribe() receives response     │
│ 14. Check status code: 201 ✓                │
│ 15. Parse JSON:                             │
│     └─ difficulty_level = "medium"          │
│ 16. Show success alert                      │
│ 17. Clear form (optional)                   │
│ 18. Return control to user                  │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Content Personalization Pipeline

```
Subscriber: age_group="middle" → difficulty="medium"
Articles in Interests: World (1), Science (2)

    ┌─────────────────────────────────────┐
    │ Email Scheduler (daily at 8am)      │
    └─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ Query subscriptions       │
        │ WHERE status='active'     │
        │ AND frequency='daily'     │
        │ AND DATEDIFF(NOW, last_   │
        │     sent) >= 1 day        │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ For each subscriber:      │
        │ {"email": "...",          │
        │  "difficulty": "medium",  │
        │  "interests": [1, 2]}     │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ Get articles:             │
        │ WHERE category_id         │
        │ IN (1, 2)                 │
        │ AND created_at > 7 days   │
        │ (or since last_sent)      │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ For each article:         │
        │ Query article_summaries   │
        │ WHERE difficulty='medium' │
        │ AND language='en'         │
        │ (or 'zh' based on pref)   │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ For each article:         │
        │ Query quiz_questions      │
        │ WHERE difficulty='medium' │
        │ AND article_id = ?        │
        │ LIMIT 5                   │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ Generate personalized     │
        │ HTML email:               │
        │                           │
        │ ELEMENTARY (Simplified):  │
        │ - Summary (100-200w)      │
        │ - Keywords                │
        │ - 5 Easy questions        │
        │ - NO background           │
        │ - NO arguments            │
        │ - NO original article     │
        │                           │
        │ MIDDLE/HIGH (Standard):   │
        │ - Summary (300-500/700w)  │
        │ - Keywords                │
        │ - Background reading      │
        │ - Pro/Con arguments       │
        │ - 5 Questions             │
        │ - Link to original        │
        │                           │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ Send via Email API:       │
        │ POST emailapi.6ray.com    │
        │ X-API-Key: [API KEY]      │
        │ Subject: "📰 Daily News   │
        │ Summary - [Date]"         │
        │ Body: [HTML email]        │
        │ To: subscriber@email.com  │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ Log delivery:             │
        │ INSERT email_logs         │
        │ email, age_group,         │
        │ difficulty_level,         │
        │ subject, status, sent_at  │
        │                           │
        │ UPDATE subscriptions      │
        │ SET last_sent = NOW()     │
        └───────────────────────────┘
```

---

## File Dependencies

```
main_articles_interface_v2.html
├─ Loads articles_data_with_summaries.json (via fetch)
├─ Calls loadCategories() on page load
│  └─► GET /categories from subscription_service_enhanced.py
├─ On form submit, calls handleSubscribe()
│  └─► POST /subscribe-enhanced to subscription_service_enhanced.py
│
subscription_service_enhanced.py
├─ Imports Flask, requests, sqlite3, json, datetime
├─ Reads/writes to subscriptions.db
│  ├─ Tables: categories, articles_enhanced, article_summaries
│  ├─         quiz_questions, subscriptions_enhanced, email_logs
│  └─ Initializes with 6 categories on startup
├─ Endpoints serve to http://localhost:5001
│
subscriptions.db
├─ Created automatically by subscription_service_enhanced.py
├─ Contains 6 tables (see above)
├─ Read by email_scheduler.py (for digest generation)
│
email_scheduler.py
├─ Queries subscriptions_enhanced (which subscribers to email)
├─ Joins with article_summaries (get content at difficulty level)
├─ Joins with quiz_questions (get questions)
├─ Generates HTML digest
├─ Sends via Email API (emailapi.6ray.com)
├─ Updates email_logs for tracking
│
articles_data_with_summaries.json
├─ Source data for 2 initial articles (IDs 6, 11)
├─ Used for testing and UI display
├─ Later: migrated to articles_enhanced table in DB
```

---

**Diagram Complete** ✅  
All flows, validations, and data paths shown
