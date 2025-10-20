# Updated Quiz System: 10 Questions Per Article with 3 Word Types

## 🎯 What Changed

**Before:** 5 questions per article (1 main idea, 1 new word, 3 SAT-style)  
**After:** 10 questions per article with **3 word types** (what/how/why)

---

## 📊 New Question Structure

Each article now gets **10 questions** organized by question type:

### Question Types (Word Types)

| Type | Count | Description | Examples |
|------|-------|-------------|----------|
| **What** | 3-4 | Facts, definitions, identification | "What is...?", "Which of the following..." |
| **How** | 3-4 | Processes, mechanisms, procedures | "How does...?", "What is the process of..." |
| **Why** | 3-4 | Reasons, implications, consequences | "Why is...?", "What would happen if..." |

---

## 💾 Database Schema (Updated)

The `quiz_questions` table already supports this! No changes needed because it has:

```sql
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,     ← 1-10 (was 1-5)
    question_type TEXT,                   ← NEW: "what_questions/how_questions/why_questions"
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎮 CLI Commands (Unchanged)

All commands still work, now with 10 questions per article:

```bash
# Get all 10 questions for article 16
python3 deepseek_processor.py --quiz 16

# Get one question by ID
python3 deepseek_processor.py --quiz-id 42

# Get ALL 10x(num_articles) questions
python3 deepseek_processor.py --all-quiz

# Get questions of a specific word type
python3 deepseek_processor.py --quiz-type what_questions
python3 deepseek_processor.py --quiz-type how_questions
python3 deepseek_processor.py --quiz-type why_questions
```

---

## 📋 JSON Response Format (Updated)

```json
[
  {
    "id": 42,
    "article_id": 16,
    "question_number": 1,
    "type": "what_questions",
    "word_type": "what",
    "question": "What is the main concept being discussed?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "B",
    "explanation": "Option B is correct because..."
  },
  {
    "id": 43,
    "article_id": 16,
    "question_number": 2,
    "type": "how_questions",
    "word_type": "how",
    "question": "How does this process work?",
    "options": ["...", "...", "...", "..."],
    "correct_answer": "C",
    "explanation": "..."
  },
  {
    "id": 44,
    "article_id": 16,
    "question_number": 3,
    "type": "why_questions",
    "word_type": "why",
    "question": "Why is this important to the topic?",
    "options": ["...", "...", "...", "..."],
    "correct_answer": "A",
    "explanation": "..."
  }
  // ... 7 more questions (total 10)
]
```

---

## 🎲 Game Development with 10 Questions

### Example 1: Get Questions by Word Type (Difficulty Mix)

```python
import json
import subprocess

# Get all "what" questions (easier/fact-based)
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz-type", "what_questions"],
    capture_output=True, text=True
)
what_questions = json.loads(result.stdout)

# Get all "why" questions (harder/reasoning-based)
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz-type", "why_questions"],
    capture_output=True, text=True
)
why_questions = json.loads(result.stdout)

print(f"Easy questions (What): {len(what_questions)}")
print(f"Hard questions (Why): {len(why_questions)}")
```

### Example 2: Random Quiz from 10 Questions

```python
import json
import random
import subprocess

# Get all 10 questions for an article
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz", "16"],
    capture_output=True, text=True
)
questions = json.loads(result.stdout)

# Randomly pick 3-5 questions for a quiz
quiz = random.sample(questions, k=random.randint(3, 5))

for q in quiz:
    print(f"\n[{q['word_type'].upper()}] Question {q['question_number']}")
    print(q['question'])
    for i, opt in enumerate(q['options']):
        print(f"  {chr(65+i)}) {opt}")
```

### Example 3: Balanced Quiz (One of Each Type)

```python
import json
import random
import subprocess

# Get all 10 questions
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz", "16"],
    capture_output=True, text=True
)
questions = json.loads(result.stdout)

# Group by type
by_type = {}
for q in questions:
    wtype = q['word_type']
    if wtype not in by_type:
        by_type[wtype] = []
    by_type[wtype].append(q)

# Create balanced quiz: 1 what, 1 how, 1 why
balanced_quiz = [
    random.choice(by_type.get('what', [])),
    random.choice(by_type.get('how', [])),
    random.choice(by_type.get('why', []))
]

print("Your balanced 3-question quiz:")
for q in balanced_quiz:
    print(f"  • {q['word_type'].upper()}: {q['question']}")
```

---

## 📊 Prompt Changes

The DeepSeek prompt was updated to request:

✅ **10 questions per article** (instead of 5)  
✅ **3 word types:** what/how/why (instead of main_idea/new_word/sat_style)  
✅ **Balanced distribution:** 3-4 questions of each type  
✅ **Different question styles:**
   - **What questions:** Facts, definitions, concepts
   - **How questions:** Processes, mechanisms, procedures
   - **Why questions:** Reasons, implications, consequences

---

## 🚀 Usage After This Update

### Step 1: Run the processor

```bash
python3 deepseek_processor.py --batch-size 5
```

This will:
- Request 10 questions per article from DeepSeek
- Store them in `quiz_questions` table with `question_number` 1-10
- Classify them as what/how/why
- Include unique IDs for each question

### Step 2: Use in your game

```bash
# Get all questions
python3 deepseek_processor.py --all-quiz > game_questions.json

# Filter by type
python3 deepseek_processor.py --quiz-type what_questions > easy_questions.json
python3 deepseek_processor.py --quiz-type why_questions > hard_questions.json
```

### Step 3: Build quiz games with random selection

```python
import json
import random

# Load all questions
with open('game_questions.json') as f:
    all_questions = json.load(f)

# Randomly pick 5 questions for today's quiz
today_quiz = random.sample(all_questions, k=5)
```

---

## 🎯 Benefits of 10 Questions + 3 Types

| Benefit | Why It Helps |
|---------|--------------|
| **10 questions per article** | Can pick random subsets (3, 5, 10) for different quiz lengths |
| **3 word types** | Create difficulty levels without changing articles |
| **What questions** | Easy/foundational knowledge checks |
| **How questions** | Medium/procedural understanding |
| **Why questions** | Hard/deeper analysis and critical thinking |
| **Each question has ID** | Track individual question analytics |
| **Separated columns** | Easy to shuffle, check, and analyze |

---

## 📈 Scalability

With this system:

| Scenario | Questions Available |
|----------|-------------------|
| 20 articles × 10 questions | **200 total questions** |
| Randomly pick 1-3 questions | Can run **thousands** of unique quizzes |
| Daily quiz (5 questions) | Can run for **40 days** without repetition |
| Difficulty levels | **67 "what", 67 "how", 67 "why"** questions |

---

## ✨ Features Summary

✅ **10 questions per article** (not 5)  
✅ **3 word types** for different question styles  
✅ **Balanced distribution** (3-4 of each type)  
✅ **Separate database columns** for easy game logic  
✅ **Unique question IDs** for tracking  
✅ **CLI commands** for easy filtering  
✅ **JSON output** for any platform  
✅ **Scalable** to thousands of questions  
✅ **Educational** with explanations included  

---

## 🔄 Migration Guide

If you already ran the processor with 5 questions:

1. Delete old questions: `DELETE FROM quiz_questions;`
2. Mark articles as unprocessed: `UPDATE articles SET deepseek_processed = 0;`
3. Run processor again: `python3 deepseek_processor.py --batch-size 5`

New processor will now request **10 questions per article** with **3 word types**!

---

## 🎮 Ready to Build!

You now have:
- **10 questions per article** with different word types
- **200 questions** across all articles (if you have 20 articles)
- **Separated columns** for easy game development
- **Unique question IDs** for tracking
- **CLI commands** to filter by type

Start building your quiz game! 🚀📚
