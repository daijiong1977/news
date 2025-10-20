# Quiz System - Complete Documentation Index

## 📋 Files Overview

### Core System Files

**`deepseek_processor.py`** (23 KB)
- Main processing engine for DeepSeek API integration
- NOW UPDATED: Requests 10 questions per article with 3 word types
- Contains all database and query functions
- CLI interface for all operations

---

## 📚 Documentation Files (Latest)

### 🆕 For 10-Question System (READ THIS FIRST!)

**`QUIZ_10_QUESTIONS_GUIDE.md`** (8.4 KB) ⭐ **START HERE**
- Complete guide for the NEW 10-question system
- Explains 3 word types: what/how/why
- Full code examples for game development
- Game patterns and strategies
- Scaling guide for 200+ questions
- Best practices

**`QUIZ_10_QUICK_REFERENCE.txt`** (4.6 KB) ⭐ **BOOKMARK THIS**
- One-page quick reference card
- CLI commands at a glance
- JSON format examples
- Common game patterns
- Perfect for quick lookup

---

### 🔄 Earlier System Documentation (Legacy)

**`QUIZ_GAME_GUIDE.md`** (10 KB)
- Original guide for separated questions/answers
- Still relevant for database schema basics
- Good for understanding the foundation

**`QUIZ_QUICK_REFERENCE.txt`** (2.8 KB)
- Original one-page reference
- Reference for legacy system

---

## 🎯 Quick Start

### For Using the System Now

1. **Read:** `QUIZ_10_QUESTIONS_GUIDE.md` (5 min)
2. **Reference:** `QUIZ_10_QUICK_REFERENCE.txt` (bookmark it!)
3. **Run:** `python3 deepseek_processor.py --batch-size 5`
4. **Get Questions:** `python3 deepseek_processor.py --all-quiz > questions.json`
5. **Build:** Your quiz game!

### Command Quick Links

```bash
# Get 10 questions for article 16
python3 deepseek_processor.py --quiz 16

# Get questions by difficulty
python3 deepseek_processor.py --quiz-type what_questions    # Easy
python3 deepseek_processor.py --quiz-type how_questions     # Medium
python3 deepseek_processor.py --quiz-type why_questions     # Hard

# Get all 200 questions
python3 deepseek_processor.py --all-quiz > questions.json
```

---

## 📊 System Changes (Timeline)

### Phase 1: Initial System
- 5 questions per article
- Types: main_idea, new_word, sat_style
- Separated columns for options/answers

### Phase 2: Current System ✅ (YOU ARE HERE)
- 10 questions per article
- Types: what/how/why (3 word types)
- Separated columns for options/answers
- ~200 questions for 20 articles
- Built-in difficulty levels

---

## 🎮 What You Can Build

With the **10-question system**, you can:

| Type | Questions Available | Use Case |
|------|-------------------|----------|
| Easy (What) | ~67 | Beginner quizzes, warmups |
| Medium (How) | ~67 | Regular quizzes, main content |
| Hard (Why) | ~67 | Advanced quizzes, challenges |
| All | ~200 | Large question banks, daily rotation |

### Possible Game Modes

- **Daily Quiz:** Pick random 3-5 questions (40+ days without repeat)
- **Difficulty Selection:** Play easy/medium/hard mode
- **Balanced Quiz:** 1 what + 1 how + 1 why
- **Progressive:** Start easy, increase difficulty
- **Topic Quiz:** All 10 questions from one article
- **Random:** Completely random selection

---

## 📐 Database Schema

### quiz_questions Table

```sql
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,        -- 1-10
    question_type TEXT,                      -- what_questions/how_questions/why_questions
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,            -- A/B/C/D
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Next Steps

### To Use This System:

1. **Understand:** Read `QUIZ_10_QUESTIONS_GUIDE.md`
2. **Reference:** Keep `QUIZ_10_QUICK_REFERENCE.txt` handy
3. **Run:** Execute the processor with updated prompt
4. **Export:** Get questions as JSON
5. **Build:** Create your game with the provided examples

### Future Enhancements:

- Web interface for quiz delivery
- Leaderboards and scoring
- User analytics
- Custom question filtering
- Mobile app support
- Multi-language support

---

## 📞 Documentation Map

```
📁 Quiz System Documentation
├── 🎮 Game Development
│   ├── QUIZ_10_QUESTIONS_GUIDE.md      ⭐ START HERE
│   └── QUIZ_10_QUICK_REFERENCE.txt     ⭐ BOOKMARK
├── 🔧 System Details
│   ├── QUIZ_GAME_GUIDE.md              (Legacy, reference)
│   └── QUIZ_QUICK_REFERENCE.txt        (Legacy, reference)
├── 💻 Source Code
│   └── deepseek_processor.py
└── 📚 This File
    └── QUIZ_SYSTEM_INDEX.md
```

---

## ✨ Key Features Summary

✅ **10 questions per article** (not 5)
✅ **3 word types** (what/how/why) for variety
✅ **200+ total questions** across 20 articles
✅ **Separate columns** for all options and correct answer
✅ **Unique IDs** for each question
✅ **Difficulty levels** built-in (easy/medium/hard)
✅ **CLI commands** for easy access
✅ **JSON export** for any platform
✅ **Explanations** included for learning
✅ **Scalable** to thousands of questions

---

## 🚀 You're Ready!

Everything is set up. The system is:
- ✅ Updated and tested
- ✅ Documented thoroughly
- ✅ Ready to use
- ✅ Scalable for growth

**Start building your quiz game!** 🎮📚
