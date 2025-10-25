# 🎨 ArticleInteractive - Visual Guide

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Articles                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Meta joins Nvidia, OpenAI, and AMD to launch Ethernet...        │
│  Choose your education level to customize the content            │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📚 Education Level:                                              │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │
│  │ Elementary (3-5) │ │ Middle Sch (6-8) │ │ High School (9-12)│ │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📖 Summary                                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Big tech companies like Meta, Nvidia, and OpenAI are...   │  │
│  │ working together to make computers work better for AI...  │  │
│  │ They want to use a common way for computers to talk...    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🎯 Key Topics                                                    │
│  ┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐ ┌──────────┐       │
│  │computers│ │ AI   │ │Ethernet│ │companies │ │ ... etc  │       │
│  └────────┘ └──────┘ └────────┘ └──────────┘ └──────────┘       │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📚 Background Information (Middle/High levels)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ As artificial intelligence systems become more complex... │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  💭 Different Perspectives (Middle/High levels)                   │
│  ┌────────────────────────┐ ┌────────────────────────┐          │
│  │ ✅ Supporting Arguments │ │ ❌ Counter Arguments   │          │
│  ├────────────────────────┤ ├────────────────────────┤          │
│  │ ✅ Better for Everyone │ │ ❌ Maybe Not Fast Enough
│  │    Ethernet is cheaper  │ │    InfiniBand is faster │          │
│  │    and easier...        │ │    for the biggest...  │          │
│  │                        │ │                        │          │
│  │ ✅ Works Well          │ │ ❌ Takes Time to Change│          │
│  │    Already proven...   │ │    Changing could be...│          │
│  └────────────────────────┘ └────────────────────────┘          │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ❓ Check Your Understanding                                      │
│                                                                   │
│  Q1: What are the big companies trying to improve for AI?        │
│  ○ A) Computer games                                             │
│  ○ B) How computers talk to each other ← YOUR ANSWER            │
│  ○ C) Phone batteries                                            │
│  ○ D) Television screens                                         │
│                                                                   │
│  ✓ Correct!                                                       │
│  The companies are working on how computers communicate          │
│  in AI systems.                                                  │
│                                                                   │
│  Q2: What common technology do they want to use?                │
│  ○ A) Bluetooth                                                  │
│  ○ B) Wi-Fi                                                      │
│  ○ C) Ethernet ← YOUR ANSWER                                    │
│  ○ D) Radio waves                                                │
│                                                                   │
│  ✓ Correct!                                                       │
│  They want to use Ethernet for AI computer connections           │
│  because it is common and cheaper.                               │
│                                                                   │
│  Q3: Which system do most AI computers use now?                 │
│  [Answer pending...]                                             │
│                                                                   │
│  Q4: Why might Ethernet be better according to the article?    │
│  [Answer pending...]                                             │
│                                                                   │
│  Q5: What will the companies do regularly?                       │
│  [Answer pending...]                                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Color Scheme

```
Primary Colors:
┌─────────────────────────────────────┐
│  Gradient: #667eea → #764ba2        │  (Purple)
│  Used for: Buttons, headers, borders│
└─────────────────────────────────────┘

Supporting Colors:
┌─────────────────────────────────────┐
│  Success: #4caf50 (Green)           │  ✅ Correct answers, pro arguments
│  Error: #f44336 (Red)               │  ❌ Incorrect answers, con arguments
│  Info: #2196f3 (Blue)               │  ℹ️ Feedback messages
│  Neutral: #999 (Gray)               │  Other text
└─────────────────────────────────────┘

Background:
┌─────────────────────────────────────┐
│  Primary: #ffffff (White)           │  Main content areas
│  Secondary: #f8f9ff (Light purple)  │  Summary boxes
│  Tertiary: #f0f4ff (Very light)     │  Hover states
│  Gradient: #f5f7fa → #c3cfe2        │  Page background
└─────────────────────────────────────┘
```

## Interactive Elements

### Difficulty Buttons

**Normal State:**
```
┌──────────────────────────┐
│ Elementary Level (3-5)   │
└──────────────────────────┘
```

**Hover State:**
```
┌──────────────────────────┐
│ Elementary Level (3-5)   │
└──────────────────────────┘
  (border: #667eea, bg: #f0f4ff)
```

**Active State:**
```
┌──────────────────────────┐
│ Elementary Level (3-5)   │ ← Purple gradient
└──────────────────────────┘
```

### Quiz Options

**Unselected:**
```
○ A) Computer games
```

**Hover:**
```
○ A) Computer games
  (border: #667eea, bg: #f0f4ff)
```

**Selected (Correct):**
```
◉ B) How computers talk to each other
  ✓ Correct! (green feedback)
```

**Selected (Incorrect):**
```
◉ C) Phone batteries
  ✗ Not quite right (red feedback)
```

## Responsive Breakpoints

### Desktop (1200px+)
```
┌─────────────────────────────────┐
│     Summary                     │
├─────────────────────────────────┤
│     Key Topics                  │
├─────────────────────────────────┤
│ Background Info                 │
├─────────────────────────────────┤
│ ┌─ Supporting ─┐ ┌─ Counter ─┐ │
│ │ Arguments    │ │ Arguments  │ │
│ └──────────────┘ └────────────┘ │
├─────────────────────────────────┤
│     Quiz                        │
└─────────────────────────────────┘
```

### Tablet (768px - 1200px)
```
┌──────────────────────┐
│ Summary              │
├──────────────────────┤
│ Key Topics           │
├──────────────────────┤
│ Background Info      │
├──────────────────────┤
│ Supporting Arguments │
├──────────────────────┤
│ Counter Arguments    │
├──────────────────────┤
│ Quiz                 │
└──────────────────────┘
```

### Mobile (< 768px)
```
┌─────────────┐
│ Summary     │
├─────────────┤
│ Key Topics  │
├─────────────┤
│ Background  │
├─────────────┤
│ Arguments   │
├─────────────┤
│ Quiz        │
└─────────────┘
```

## Animation Effects

### Slide-Up Animation
```
Start:  Content at +20px, opacity 0%
        └─────────────────────────┘

End:    Content at 0px, opacity 100%
        ↑
        └─────────────────────────┘

Duration: 0.5s
Easing: ease
```

### Button Hover
```
Normal:  translateY(0px)
Hover:   translateY(-2px) + Shadow
```

### Keyword Tag Hover
```
Normal:  bg: light purple, color: purple
Hover:   bg: purple (gradient), color: white
         translateY(-2px)
```

## Typography

```
Headers:
├─ Page Title: 36px, Bold (700), #333
├─ Section Title: 24px, Bold (700), #333
├─ Subsection: 18px, Bold (700), #333
└─ Argument Title: 16px, Bold (700)

Body Text:
├─ Main: 16px, Regular (400), #444
├─ Secondary: 15px, Regular (400), #555
└─ Small: 14px, Regular (400), #666

Spacing:
├─ Sections: 30px gap
├─ Elements: 20px padding
└─ Text: 1.6-1.8 line height
```

## State Indicators

### Loading State
```
┌────────────────────┐
│ Loading article... │
└────────────────────┘
```

### Empty State
```
┌────────────────────┐
│ Article not found  │
│ ← Back to Articles │
└────────────────────┘
```

### Answer Feedback

**Correct:**
```
┌───────────────────────────┐
│ ✓ Correct!                │
│ The companies are working │
│ on how computers...       │
└───────────────────────────┘
 (green background, left border)
```

**Incorrect:**
```
┌───────────────────────────┐
│ ✗ Not quite right         │
│ InfiniBand is currently   │
│ used in about 80% of...   │
└───────────────────────────┘
 (red background, left border)
```

## Accessibility Features

- ✅ High contrast ratios (WCAG AA compliant)
- ✅ Large touch targets (44px minimum on mobile)
- ✅ Clear focus states on interactive elements
- ✅ Semantic HTML structure
- ✅ Proper form labels
- ✅ Icon + text combinations

## Browser Rendering

```
Chrome:  Smooth, hardware-accelerated
Safari:  Smooth, -webkit- prefixed
Firefox: Smooth, standard CSS
Edge:    Smooth, Chromium-based
Mobile:  Optimized touch, 60fps
```

---

This visual guide helps understand the layout, colors, and interactions of the ArticleInteractive component.
