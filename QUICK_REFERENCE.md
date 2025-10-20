# 🎯 QUICK REFERENCE - Three-Tier System

## ⚡ 30-Second Summary

| | Elementary | Middle | High |
|---|---|---|---|
| **Age** | 8-11 | 11-14 | 14-18 |
| **Grade** | 3-5 | 6-8 | 9-12 |
| **Difficulty** | Easy | Medium | Hard |
| **Summary Length** | 100-200w | 300-500w | 500-700w |
| **Layout** | **DIFFERENT** | **SAME** | **SAME** |
| **Background?** | ❌ | ✅ | ✅ |
| **Arguments?** | ❌ | ✅ | ✅ |
| **Original Link?** | ❌ | ✅ | ✅ |

## The One Rule

**Middle School and High School have IDENTICAL layouts.**
**Only Elementary is different.**

## Database Storage

```
All stored the same way:
- article_id: 6
- difficulty: 'easy' OR 'medium' OR 'hard'
- language: 'en' OR 'zh'
- summary: TEXT (length varies)
- background_reading: NULL (for easy) or TEXT (for medium/hard)
- pro_arguments: NULL (for easy) or TEXT (for medium/hard)
- con_arguments: NULL (for easy) or TEXT (for medium/hard)
```

## Email Template Selection

```
IF subscriber.difficulty_level == 'easy':
    USE: elementary_template.html
         (hides: background, arguments, link sections)

ELSE (medium or hard):
    USE: standard_template.html
         (shows: all sections, same layout)
```

## DeepSeek Generation

```
Single request → 3 responses:

{
  "elementary": { ... },    ← Easy level
  "middle": { ... },        ← Medium level  
  "high": { ... }           ← Hard level
}
```

## Files You Need

1. **elementary_template.html** - Simplified version
2. **standard_template.html** - Full version (for middle + high)

That's it. 2 templates total.

## Migration Path

```
Old System:
- All subscribers get same layout
- All articles same format

New System:
- Elementary: Simple layout (no background/args/link)
- Middle: Full layout (background + args + link)
- High: Full layout (background + args + link)
- Middle & High share the EXACT SAME HTML layout
```

## Implementation Checklist

- [x] Subscription form collects age_group
- [x] Backend maps age_group → difficulty_level
- [x] DeepSeek generates all 3 levels
- [x] Database stores all content variants
- [ ] Create elementary_template.html
- [ ] Create standard_template.html
- [ ] Update email_scheduler.py (add template logic)
- [ ] Test all 3 levels

## Status

✅ Backend ready
✅ Database ready
✅ Content generation ready
⏳ Templates to create
⏳ Email system to update

---

**Remember**: Middle and High School layouts are IDENTICAL!
