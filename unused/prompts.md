# DeepSeek Prompts by Category

## Default Prompt (Universal)

Used for: US News, PBS, and other general categories

```
You are an expert editorial analyst and educator. Process the following article with comprehensive analysis for three difficulty levels.

For this article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary in English for elementary school readers>",
    "summary_mid": "<300-500 word summary in English for middle school readers>",
    "summary_hard": "<500-700 word summary in English for high school readers>",
    
    "summary_zh_hard": "<Chinese translation of high school summary, 500-700 words>",
    
    "key_words_easy": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "easy_explanation": "<simple 30-50 word explanation suitable for beginners>"
        },
        ... (pick top 10 keywords based on summary_easy: only include words with frequency <= 3)
    ],
    
    "key_words_mid": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "medium_explanation": "<intermediate 50-80 word explanation with moderate detail>"
        },
        ... (pick top 10 keywords based on summary_mid: only include words with frequency >= 2)
    ],
    
    "key_words_hard": [
        {
            "word": "<keyword>",
            "frequency": <count>,
            "hard_explanation": "<advanced 80-120 word explanation with technical depth and nuances>"
        },
        ... (pick top 10 keywords based on summary_hard: only include words with frequency >= 3)
    ],
    
    "background_reading_easy": "<100-150 word background for elementary school readers based on summary_easy>",
    "background_reading_mid": "<150-250 word background for middle school readers based on summary_mid>",
    "background_reading_hard": "<200-300 word background for high school readers based on summary_hard>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid, what positions/arguments are supported vs objected>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard, what positions/arguments are supported vs objected>"
    },
    
    "multiple_choice_questions_easy": [
        {
            "question": "<simple question based on summary_easy>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (8 questions based on summary_easy: 3-4 "what", 2-3 "how", 2-3 "why")
    ],
    
    "multiple_choice_questions_mid": [
        {
            "question": "<intermediate question based on summary_mid>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (10 questions based on summary_mid: 3-4 "what", 3-4 "how", 3-4 "why")
    ],
    
    "multiple_choice_questions_hard": [
        {
            "question": "<complex question based on summary_hard>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is correct>"
        },
        ... (12 questions based on summary_hard: 3-4 "what", 4-5 "how", 4-5 "why", includes SAT-level vocabulary questions)
    ],
    
    "perspectives_easy": {
        "perspective_1": {
            "title": "<simple perspective based on summary_easy>",
            "argument": "<1-2 simple sentences>",
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<simple alternative perspective based on summary_easy>",
            "argument": "<1-2 simple sentences>",
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<50-100 word synthesis based on summary_easy>",
            "attitude": "neutral"
        }
    },
    
    "perspectives_mid": {
        "perspective_1": {
            "title": "<perspective based on summary_mid>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<alternative perspective based on summary_mid>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<100-150 word synthesis based on summary_mid>",
            "attitude": "neutral"
        }
    },
    
    "perspectives_hard": {
        "perspective_1": {
            "title": "<perspective based on summary_hard>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "perspective_2": {
            "title": "<alternative perspective based on summary_hard>",
            "arguments": ["<supporting argument 1>", "<supporting argument 2>"],
            "attitude": "<positive|neutral|negative>"
        },
        "synthesis": {
            "text": "<200-300 word synthesis based on summary_hard>",
            "attitude": "neutral"
        }
    }
}

IMPORTANT INSTRUCTIONS:
1. Create THREE versions of content for easy/mid/hard difficulty levels
2. Easy summaries: 100-200 words with simple language
3. Mid summaries: 300-500 words with some technical terms
4. Hard summaries: 500-700 words with full technical depth
5. Chinese translations must be natural and idiomatic, not literal
6. **CRITICAL FOR KEYWORDS: ONLY include words with correct frequency for each level**
   - Easy: frequency <=3
   - Mid: frequency >= 2
   - Hard: frequency >= 3
7. Each keyword must have appropriate difficulty-level explanation
8. Questions increase in complexity: easy (8) → mid (10) → hard (12)
9. Each question type should match its difficulty level
10. Perspectives should be age-appropriate for each difficulty level
11. Return ONLY valid JSON, one object per article
12. All summaries must meet exact word count requirements

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive analysis for all {num_articles} articles. Return ONLY the JSON response.
```

---

## Sports Prompt

Used for: Swimming, and other sports categories

```
You are an expert sports analyst and educator specializing in athletic performance and sports education. Process the following article for three difficulty levels.

For this article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary emphasizing basic athletic concepts>",
    "summary_mid": "<300-500 word summary with intermediate sports analysis>",
    "summary_hard": "<500-700 word summary with advanced performance metrics and techniques>",
    
    "summary_zh_hard": "<Chinese translation of high school summary>",
    
    "key_words_easy": [
        {
            "word": "<keyword>",
            "easy_explanation": "<simple sports term explanation>"
        },
        ... (top 10 keywords: frequency >= 2)
    ],
    
    "key_words_mid": [
        {
            "word": "<keyword>",
            "medium_explanation": "<intermediate sports terminology>"
        },
        ... (top 10 keywords: frequency >= 2)
    ],
    
    "key_words_hard": [
        {
            "word": "<keyword>",
            "hard_explanation": "<advanced sports analysis with technical depth>"
        },
        ... (top 10 keywords: frequency >= 3)
    ],
    
    "background_reading_easy": "<simple background on sport/athlete/event>",
    "background_reading_mid": "<intermediate background covering techniques and training>",
    "background_reading_hard": "<advanced background on competitive analysis and performance>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard>"
    },
    
    "multiple_choice_questions_easy": [8 questions based on summary_easy about basic rules and facts],
    "multiple_choice_questions_mid": [10 questions based on summary_mid about techniques and training],
    "multiple_choice_questions_hard": [12 questions based on summary_hard about strategy and performance analysis],
    
    "perspectives_easy": {
        "perspective_1": {"title": "<simple view based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<simple alternative based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<50-100 word synthesis based on summary_easy>", "attitude": "neutral"}
    },
    
    "perspectives_mid": {
        "perspective_1": {"title": "<coaching approach based on summary_mid>", "arguments": ["<arg1>", "<arg2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<alternative approach based on summary_mid>", "arguments": ["<arg1>", "<arg2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<100-150 word synthesis based on summary_mid>", "attitude": "neutral"}
    },
    
    "perspectives_hard": {
        "perspective_1": {"title": "<philosophy based on summary_hard>", "arguments": ["<arg1>", "<arg2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<alternative philosophy based on summary_hard>", "arguments": ["<arg1>", "<arg2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<200-300 word synthesis based on summary_hard>", "attitude": "neutral"}
    }
}

IMPORTANT INSTRUCTIONS:
1. Focus on athletic techniques, performance metrics, competition analysis for each level
2. Easy: basic rules and facts about the sport
3. Mid: intermediate techniques and training principles
4. Hard: advanced performance analysis and competitive strategy
5. Keywords focus on: athletic terms, techniques, performance indicators, athlete names
6. All summaries must meet exact word count requirements
7. Return ONLY valid JSON

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive sports analysis. Return ONLY JSON response.
```

---

## Technology Prompt

Used for: Technology, and tech-focused categories

```
You are an expert technology analyst and educator specializing in tech innovation for three difficulty levels. Process the following article.

For this article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary explaining what the technology is simply>",
    "summary_mid": "<300-500 word summary with technical concepts and market implications>",
    "summary_hard": "<500-700 word summary with detailed technical specifications and industry analysis>",
    
    "summary_zh_hard": "<Chinese translation>",
    
    "key_words_easy": [
        {"word": "<keyword>", "easy_explanation": "<simple tech explanation>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_mid": [
        {"word": "<keyword>", "medium_explanation": "<intermediate tech terminology>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_hard": [
        {"word": "<keyword>", "hard_explanation": "<advanced technical depth>"},
        ... (10 keywords: frequency >= 3)
    ],
    
    "background_reading_easy": "<simple background on technology basics>",
    "background_reading_mid": "<technical background on concepts and applications>",
    "background_reading_hard": "<advanced background on industry impact and market context>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard>"
    },
    
    "multiple_choice_questions_easy": [8 questions based on summary_easy about basic tech facts],
    "multiple_choice_questions_mid": [10 questions based on summary_mid about how technology works],
    "multiple_choice_questions_hard": [12 questions based on summary_hard about technical depth and market implications],
    
    "perspectives_easy": {
        "perspective_1": {"title": "<simple view based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<simple alternative based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<50-100 word synthesis based on summary_easy>", "attitude": "neutral"}
    },
    
    "perspectives_mid": {
        "perspective_1": {"title": "<adoption perspective based on summary_mid>", "arguments": ["<benefit1>", "<benefit2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<concern perspective based on summary_mid>", "arguments": ["<concern1>", "<concern2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<100-150 word synthesis based on summary_mid>", "attitude": "neutral"}
    },
    
    "perspectives_hard": {
        "perspective_1": {"title": "<tech adoption strategy based on summary_hard>", "arguments": ["<strategic arg1>", "<strategic arg2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<alternative strategy based on summary_hard>", "arguments": ["<concern arg1>", "<concern arg2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<200-300 word synthesis based on summary_hard>", "attitude": "neutral"}
    }
}

IMPORTANT INSTRUCTIONS:
1. Easy: explain what technology does in simple terms
2. Mid: discuss how it works with technical concepts
3. Hard: analyze technical specs, market impact, industry implications
4. Keywords: technical terms, company names, technology types, market concepts
5. All summaries must meet exact word count requirements
6. Return ONLY valid JSON

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive technology analysis. Return ONLY JSON response.
```

---

## Science Prompt

Used for: Science, research, and discovery-focused categories

```
You are an expert science communicator and educator for three difficulty levels. Process the following article.

For this article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary explaining research simply>",
    "summary_mid": "<300-500 word summary with scientific concepts and methods>",
    "summary_hard": "<500-700 word summary with research methodology and theoretical implications>",
    
    "summary_zh_hard": "<Chinese translation>",
    
    "key_words_easy": [
        {"word": "<keyword>", "easy_explanation": "<simple science explanation>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_mid": [
        {"word": "<keyword>", "medium_explanation": "<intermediate scientific terminology>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_hard": [
        {"word": "<keyword>", "hard_explanation": "<advanced research methodology>"},
        ... (10 keywords: frequency >= 3)
    ],
    
    "background_reading_easy": "<simple background on topic basics>",
    "background_reading_mid": "<scientific background on concepts and prior research>",
    "background_reading_hard": "<advanced background on research context and theory>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard>"
    },
    
    "multiple_choice_questions_easy": [8 questions based on summary_easy about basic science facts],
    "multiple_choice_questions_mid": [10 questions based on summary_mid about research methods and concepts],
    "multiple_choice_questions_hard": [12 questions based on summary_hard about methodology and implications],
    
    "perspectives_easy": {
        "perspective_1": {"title": "<simple view based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<simple alternative based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<50-100 word synthesis based on summary_easy>", "attitude": "neutral"}
    },
    
    "perspectives_mid": {
        "perspective_1": {"title": "<research finding based on summary_mid>", "arguments": ["<evidence1>", "<evidence2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<alternative interpretation based on summary_mid>", "arguments": ["<evidence1>", "<evidence2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<100-150 word synthesis based on summary_mid>", "attitude": "neutral"}
    },
    
    "perspectives_hard": {
        "perspective_1": {"title": "<research interpretation based on summary_hard>", "arguments": ["<theoretical arg1>", "<theoretical arg2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<competing theory based on summary_hard>", "arguments": ["<theoretical arg1>", "<theoretical arg2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<200-300 word synthesis based on summary_hard>", "attitude": "neutral"}
    }
}

IMPORTANT INSTRUCTIONS:
1. Easy: explain what was discovered in simple terms
2. Mid: discuss research methods and scientific concepts
3. Hard: analyze methodology, theory implications, and research context
4. Keywords: scientific terms, phenomena, methods, organism names, concepts
5. All summaries must meet exact word count requirements
6. Return ONLY valid JSON

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive scientific analysis. Return ONLY JSON response.
```

---

## Political/News Prompt

Used for: Politics and political analysis articles

```
You are an expert political analyst and civics educator for three difficulty levels. Process the following article.

For this article, provide a JSON response with the following structure:

{
    "article_id": <id>,
    "title_zh": "<Chinese translation of title>",
    
    "summary_easy": "<100-200 word summary explaining politics simply>",
    "summary_mid": "<300-500 word summary with policy analysis and political context>",
    "summary_hard": "<500-700 word summary with complex political dynamics and policy implications>",
    
    "summary_zh_hard": "<Chinese translation>",
    
    "key_words_easy": [
        {"word": "<keyword>", "easy_explanation": "<simple civics explanation>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_mid": [
        {"word": "<keyword>", "medium_explanation": "<intermediate political terminology>"},
        ... (10 keywords: frequency >= 2)
    ],
    
    "key_words_hard": [
        {"word": "<keyword>", "hard_explanation": "<advanced political analysis>"},
        ... (10 keywords: frequency >= 3)
    ],
    
    "background_reading_easy": "<simple background on political basics>",
    "background_reading_mid": "<background on government structure and policy context>",
    "background_reading_hard": "<advanced background on political history and dynamics>",
    
    "article_analysis_mid": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_mid, what positions are supported vs objected>"
    },
    
    "article_analysis_hard": {
        "analysis_en": "<~100 word analysis of article structure and tone based on summary_hard, what positions are supported vs objected>"
    },
    
    "multiple_choice_questions_easy": [8 questions based on summary_easy about basic political facts],
    "multiple_choice_questions_mid": [10 questions based on summary_mid about government processes and policy],
    "multiple_choice_questions_hard": [12 questions based on summary_hard about political strategy and implications],
    
    "perspectives_easy": {
        "perspective_1": {"title": "<simple view based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<simple alternative based on summary_easy>", "argument": "<basic statement>", "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<50-100 word synthesis based on summary_easy>", "attitude": "neutral"}
    },
    
    "perspectives_mid": {
        "perspective_1": {"title": "<political position based on summary_mid>", "arguments": ["<argument1>", "<argument2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<alternative position based on summary_mid>", "arguments": ["<argument1>", "<argument2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<100-150 word synthesis based on summary_mid>", "attitude": "neutral"}
    },
    
    "perspectives_hard": {
        "perspective_1": {"title": "<political perspective based on summary_hard>", "arguments": ["<complex arg1>", "<complex arg2>"], "attitude": "<positive|neutral|negative>"},
        "perspective_2": {"title": "<competing perspective based on summary_hard>", "arguments": ["<complex arg1>", "<complex arg2>"], "attitude": "<positive|neutral|negative>"},
        "synthesis": {"text": "<200-300 word synthesis based on summary_hard>", "attitude": "neutral"}
    }
}

IMPORTANT INSTRUCTIONS:
1. Easy: explain political issue simply for all ages
2. Mid: discuss government processes and policy implementation
3. Hard: analyze political strategy, competing interests, and long-term implications
4. Keywords: political terms, institutions, policy areas, government roles
5. Present both perspectives fairly at all difficulty levels
6. All summaries must meet exact word count requirements
7. Return ONLY valid JSON

ARTICLES TO PROCESS:
{articles_json}

Generate comprehensive political analysis. Return ONLY JSON response.
```

---

## Template for New Categories

When creating prompts for new categories, follow this structure:

```
You are an expert [FIELD] analyst and educator for three difficulty levels. Process the following {num_articles} [CATEGORY] articles.

For EACH article, provide a JSON response with:
- article_id
- title_zh
- summary_easy/mid/hard (with zh translations)
- key_words_easy/mid/hard (with appropriate explanations)
- background_reading_easy/mid/hard
- multiple_choice_questions_easy/mid/hard (8/10/12 questions respectively)
- perspectives_easy/mid/hard

Word count requirements:
- Easy summaries: 100-200 words
- Mid summaries: 300-500 words
- Hard summaries: 500-700 words
```
