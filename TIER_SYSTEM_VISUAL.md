# 📊 Three-Tier System - Visual Overview

## The 3-Tier Pyramid

```
                    ▲
                   /|\
                  / | \
                 /  |  \
                /   |   \
               /    |    \
              /     |     \
             /  HARD LEVEL \
            /   High School  \
           /   (500-700w)     \
          /     + Full Content \
         /                      \
        ┌────────────────────────┐
        │   MEDIUM LEVEL         │
        │   Middle School        │  Same HTML
        │   (300-500w)           │  Layout!
        │   + Full Content       │
        ├────────────────────────┤
        │   EASY LEVEL           │
        │   Elementary           │  Different
        │   (100-200w)           │  Layout
        │   - No Arguments       │  (Simplified)
        │   - No Background      │
        │   - No Original Link   │
        └────────────────────────┘
```

---

## Layout Structure Diagram

```
ELEMENTARY LAYOUT                  MIDDLE/HIGH SCHOOL LAYOUT
(Simplified)                       (Standard - SAME for both)

┌─────────────┐                   ┌──────────────────┐
│   TITLE     │                   │     TITLE        │
├─────────────┤                   ├──────────────────┤
│   SUMMARY   │                   │    SUMMARY       │
│ 100-200w    │                   │  300-500/500-700w│
├─────────────┤                   ├──────────────────┤
│  KEYWORDS   │                   │   KEYWORDS       │
├─────────────┤                   ├──────────────────┤
│ QUIZ (5)    │                   │ BACKGROUND       │
│             │                   ├──────────────────┤
│             │                   │   ARGUMENTS      │
│             │                   │  (Pro + Con)     │
│             │                   ├──────────────────┤
│             │                   │  QUIZ (5)        │
│             │                   ├──────────────────┤
│             │                   │  ORIGINAL LINK   │
└─────────────┘                   └──────────────────┘

NO: Background    vs    YES: Background
NO: Arguments           YES: Arguments
NO: Link                YES: Link
```

---

## Content Difficulty Spectrum

```
ELEMENTARY          MIDDLE             HIGH SCHOOL
(Easy)              (Medium)           (Hard)

Summary:            Summary:           Summary:
Simple words        Intermediate       Sophisticated
Main facts          Facts + Context    Deep analysis
One perspective     Balanced view      Multiple views

100-200 words       300-500 words      500-700 words

Keywords:           Keywords:          Keywords:
5-7 simple          5-7 standard       5-7 detailed

Questions:          Questions:         Questions:
Recall based        Comprehension      Analysis focused
"What is...?"       "Why did...?"      "How does...?"
"Which is...?"      "What causes...?"  "What if...?"
                    "Compare..."       "Evaluate..."

NO Background       YES Background     YES Background
NO Arguments        YES Arguments      YES Arguments
NO Original Link    YES Link           YES Link
```

---

## Subscriber Experience

```
ELEMENTARY SUBSCRIBER          MIDDLE SUBSCRIBER           HIGH SCHOOL SUBSCRIBER
(Age 8-11)                     (Age 11-14)                (Age 14-18)
Grade 3-5                      Grade 6-8                  Grade 9-12

Receives:                      Receives:                  Receives:
┌──────────────────┐          ┌──────────────────┐       ┌──────────────────┐
│ Simple Summary   │          │ Medium Summary   │       │ Detailed Summary │
│ (100-200 words)  │          │ (300-500 words)  │       │ (500-700 words)  │
├──────────────────┤          ├──────────────────┤       ├──────────────────┤
│ Key Topics       │          │ Key Topics       │       │ Key Topics       │
├──────────────────┤          ├──────────────────┤       ├──────────────────┤
│ 5 Easy Questions │          │ Background Info  │       │ Background Info  │
│                  │          ├──────────────────┤       ├──────────────────┤
│                  │          │ Pro/Con Args     │       │ Pro/Con Args     │
│                  │          ├──────────────────┤       ├──────────────────┤
│                  │          │ 5 Medium Qs      │       │ 5 Hard Questions │
│                  │          ├──────────────────┤       ├──────────────────┤
│                  │          │ Original Link    │       │ Original Link    │
└──────────────────┘          └──────────────────┘       └──────────────────┘

Simple & Fun                   Standard & Balanced        Analytical & Deep
```

---

## HTML Template Decision Tree

```
Subscribe: age_group="elementary"
    ↓
subscription_service_enhanced.py maps to difficulty_level="easy"
    ↓
When generating email:
    ↓
    IF difficulty_level == "easy":
        ├─ Use: elementary_template.html
        ├─ Include: title, summary, keywords, quiz
        └─ Exclude: background, arguments, link
    
    ELSE (difficulty_level == "medium" OR "hard"):
        ├─ Use: standard_template.html
        ├─ Include: title, summary, keywords, background, arguments, quiz, link
        └─ Content depth varies (medium vs hard)
```

---

## Files Required

### HTML Templates (2 total)
1. **elementary_template.html**
   - Simplified layout
   - Used when: difficulty_level == 'easy'

2. **standard_template.html**
   - Full layout with all sections
   - Used when: difficulty_level == 'medium' OR 'hard'
   - Same layout for both - content only differs

### Database Tables (Already designed)
- article_summaries (has nullable fields for background/arguments)
- quiz_questions (difficulty-specific questions)
- subscriptions_enhanced (stores age_group → difficulty_level mapping)

### Backend Endpoints (Already designed)
- GET /categories
- POST /subscribe-enhanced
- POST /generate-deepseek-summaries
- POST /store-summaries

---

## Deployment Checklist

### Phase 1: Ready ✅
- [x] Subscription form with age_group dropdown
- [x] Age-to-difficulty mapping (elementary→easy, middle→medium, high→hard)
- [x] DeepSeek batch prompt generates all 3 levels
- [x] Database stores all 3 levels
- [x] Backend endpoints implemented

### Phase 2: To Do
- [ ] Create elementary_template.html
- [ ] Create standard_template.html
- [ ] Update email_scheduler.py with template selection
- [ ] Test email sending for all 3 levels

### Phase 3: Validation
- [ ] Elementary subscriber gets simplified email
- [ ] Middle subscriber gets full email with medium content
- [ ] High subscriber gets full email with hard content
- [ ] Layouts correct for each level

---

## Quick Reference for Developers

```python
# Mapping (in subscription_service_enhanced.py)
AGE_GROUPS = {
    'elementary': {'difficulty': 'easy'},
    'middle': {'difficulty': 'medium'},
    'high': {'difficulty': 'hard'}
}

# Template selection (in email_scheduler.py)
difficulty = subscriber.difficulty_level

if difficulty == 'easy':
    template = 'elementary_template.html'
    # Will hide background, arguments, link sections
else:
    template = 'standard_template.html'
    # Will show all sections

# Content (from database)
content = query_summaries(article_id, difficulty, language)
# Returns different summary length & arguments based on difficulty
```

---

## Status: ✅ CLARIFIED AND READY

- ✅ Elementary: Unique simplified layout
- ✅ Middle School: Standard layout with medium content
- ✅ High School: Standard layout (same as Middle) with hard content
- ✅ DeepSeek generates all 3 in one request
- ✅ Only 2 HTML templates needed
- ✅ Simple template selection logic
- ✅ Ready to build!
