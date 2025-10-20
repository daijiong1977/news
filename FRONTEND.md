# React Frontend Documentation

## Overview

The React frontend provides a beautiful, responsive web interface for the News Pipeline learning platform. It displays articles with multi-level content tailored to different difficulty levels and languages.

---

## Design Philosophy

### Color Scheme
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Background**: White with subtle gradients
- **Text**: Dark gray (#2c3e50, #333)
- **Accents**: Light purple backgrounds, blue borders

### Key Features
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Bilingual support (English & Chinese)
- ✅ Multi-difficulty levels (easy, mid, hard)
- ✅ Smooth animations and transitions
- ✅ Accessible UI with proper contrast
- ✅ Flexible, scalable component structure

---

## Project Structure

```
frontend/
├── public/               # Static assets
├── src/
│   ├── components/       # React components
│   │   ├── ArticleList.tsx      # Grid of articles
│   │   ├── ArticleDetail.tsx    # Detailed article view
│   │   └── Filters.tsx          # Filter controls
│   ├── styles/           # Component-specific CSS
│   │   └── ArticleDetail.css    # Detailed page styling
│   ├── App.tsx           # Main app component
│   ├── App.css           # Global app styling
│   ├── index.tsx         # React root
│   └── index.css         # Global CSS
├── package.json
├── tsconfig.json
└── README.md
```

---

## Components

### 1. **ArticleList** (`ArticleList.tsx`)

Displays a grid of articles with basic information.

**Props:**
```typescript
{
  filters: {
    difficulty: 'easy' | 'mid' | 'hard',
    language: 'en' | 'zh',
    category: string
  },
  onSelectArticle: (articleId: number) => void
}
```

**Features:**
- Article cards with title, source, description
- Clickable to view details
- Responsive grid (auto-fill, minmax(300px, 1fr))
- Hover effects with elevation

### 2. **ArticleDetail** (`ArticleDetail.tsx`)

Comprehensive single-article view with all content sections.

**Props:**
```typescript
{
  articleId: number,
  filters: Filters,
  onBack: () => void
}
```

**Sections:**
1. **Article Preview**
   - Title, metadata (source, date, difficulty)
   - Article description/snippet
   - Article image (or placeholder)
   - Language toggle buttons

2. **Summary**
   - Multi-level content based on difficulty
   - Large, readable text

3. **Keywords & Concepts**
   - Gradient card grid
   - Word + explanation pairs
   - Hover animations

4. **Background Reading**
   - Context and related information
   - Light purple background box

5. **"Dive Deeper" Collapsible Section**
   - Quiz questions with multiple choice
   - Different perspectives/comments
   - Deep analysis content

### 3. **Filters** (`Filters.tsx`)

Top navigation for filtering articles.

**Props:**
```typescript
{
  filters: Filters,
  onFilterChange: (newFilters: Partial<Filters>) => void
}
```

**Options:**
- **Difficulty**: easy | mid | hard
- **Language**: English | 中文 (Chinese)
- **Category**: All categories from database

---

## Styling System

### CSS Structure

#### ArticleDetail.css (450+ lines)
Comprehensive styling for the detail page including:

- **Layout Components**
  - `.article-preview` - Header section
  - `.detail-section` - Content sections
  - `.dive-button-container` - Collapsible trigger

- **Content Sections**
  - `.summary-text` - Article summary
  - `.keywords-grid` - Keyword card layout
  - `.background-box` - Background reading
  - `.quiz-container` - Quiz questions
  - `.comments-container` - Perspectives
  - `.analysis-box` - Deep analysis

- **Interactive Elements**
  - `.keyword-card` - Animated gradient cards
  - `.quiz-option` - Radio button styling
  - `.lang-btn` - Language toggle buttons
  - `.dive-button` - Gradient button

- **Responsive Breakpoints**
  - `@media (max-width: 768px)` - Tablets
  - `@media (max-width: 480px)` - Mobile

- **Animations**
  - `slideIn` - Section entrance
  - `fadeIn` - Page load
  - `spin` - Loading indicator

### App.css
Global styling for:
- App header with gradient
- Filter bar layout
- Article list grid
- Back buttons
- General layout and spacing

---

## API Integration

The frontend expects these API endpoints:

### `GET /api/articles?filters`

**Query Parameters:**
```
difficulty: 'easy' | 'mid' | 'hard'
language: 'en' | 'zh'
category: string (optional)
limit: number (optional)
offset: number (optional)
```

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "zh_title": "中文标题",
      "source": "BBC",
      "pub_date": "2025-10-20T00:00:00Z",
      "description": "Short description...",
      "image_url": "https://..."
    }
  ],
  "total": 42
}
```

### `GET /api/articles/:id?difficulty=mid&language=en`

**Response:**
```json
{
  "article": {
    "id": 1,
    "title": "Article Title",
    "zh_title": "中文标题",
    "source": "BBC",
    "pub_date": "2025-10-20T00:00:00Z",
    "description": "...",
    "image_url": "https://..."
  },
  "summary": "Full summary text...",
  "keywords": [
    {
      "word": "term",
      "explanation": "definition..."
    }
  ],
  "questions": [
    {
      "id": 1,
      "question": "Question text?",
      "choices": ["A", "B", "C", "D"],
      "correct_answer": 0,
      "explanation": "Why this is correct..."
    }
  ],
  "comments": [
    {
      "id": 1,
      "content": "Perspective text...",
      "attitude": "positive",
      "source": "Author Name"
    }
  ],
  "background_reading": "Background context...",
  "analysis": "Deep analysis text..."
}
```

---

## Installation & Setup

### Prerequisites
- Node.js 14+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm start
```

Runs at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Creates optimized production build in `build/` directory

### TypeScript Compilation

```bash
npm run build-ts
```

---

## Styling Customization

### Change Primary Color

Edit `frontend/src/styles/ArticleDetail.css`:

```css
/* Find and replace all instances of: */
#667eea  /* Primary blue */
#764ba2  /* Primary purple */

/* With your desired colors, e.g.: */
#667eea  → #FF6B6B
#764ba2  → #FF8787
```

### Modify Spacing

Global spacing is based on multiples of 5px:
- Padding: `15px`, `20px`, `25px`, `30px`, `40px`
- Margins: `15px`, `20px`, `25px`, `30px`
- Gaps: `10px`, `12px`, `15px`, `20px`

Change in CSS files to adjust overall density.

### Adjust Font Sizes

Main typography scales:
- Headings: `1.4em` → `2.2em`
- Body: `0.95em` → `1.1em`
- Small: `0.85em` → `0.9em`

---

## Performance Optimization

### Implemented Optimizations
- React.memo for component memoization
- CSS animations use `transform` and `opacity` (GPU accelerated)
- Grid layouts use `auto-fill` for responsive scaling
- Lazy loading support ready for images

### Best Practices
- Minimize re-renders with proper state management
- Use CSS Grid for layout (better than Flexbox for large grids)
- Animations are GPU-accelerated
- Images should be optimized before deployment

### Network Performance
- Minify CSS and JavaScript in production
- Enable gzip compression on server
- Implement image CDN for image delivery
- Cache static assets

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Android latest

### Known Limitations
- IE11: Not supported (uses CSS Grid, Flexbox, ES6)
- Older mobile browsers may not support all CSS features

---

## Accessibility Features

- ✅ Semantic HTML structure
- ✅ ARIA labels on interactive elements
- ✅ Sufficient color contrast (WCAG AA)
- ✅ Keyboard navigation support
- ✅ Screen reader friendly
- ✅ Focus indicators on buttons

---

## Testing

### Run Tests

```bash
npm test
```

### TypeScript Type Checking

```bash
npm run type-check
```

---

## Responsive Design Breakpoints

| Device | Width | Layout |
|--------|-------|--------|
| Mobile | < 480px | 1 column, stacked |
| Small Tablet | 480-768px | 1-2 columns |
| Tablet | 768-1024px | 2-3 columns |
| Desktop | > 1024px | 3-4 columns |

### Key Responsive Adjustments
- **Preview Header**: Grid → Single column on mobile
- **Keywords Grid**: Adjusts from 4 → 2 → 1 column
- **Language Buttons**: Flex wrap on mobile
- **Typography**: Scales down on small screens
- **Padding**: Reduced from 40px → 25px → 20px

---

## Future Enhancements

### Planned Features
- [ ] Article bookmarking/favorites
- [ ] Progress tracking
- [ ] User statistics dashboard
- [ ] Spaced repetition for vocabulary
- [ ] Text-to-speech for summaries
- [ ] Dark mode toggle
- [ ] Social sharing buttons
- [ ] Comment/discussion feature
- [ ] Achievement badges

### Performance Upgrades
- [ ] Implement virtual scrolling for large lists
- [ ] Code splitting for lazy loading components
- [ ] Service workers for offline support
- [ ] Image lazy loading

---

## Troubleshooting

### Common Issues

#### "Cannot find module 'axios'"
```bash
npm install axios
```

#### TypeScript compilation errors
Ensure `tsconfig.json` has correct settings:
```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"]
  }
}
```

#### Styles not applying
- Clear browser cache (Ctrl+Shift+Delete)
- Ensure CSS file is imported correctly
- Check for CSS specificity conflicts

#### API calls failing
- Verify backend server is running
- Check CORS configuration on backend
- Verify API endpoint URLs in code

---

## Quick Reference

### Component Usage

```tsx
// App.tsx
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';

<ArticleList 
  filters={filters} 
  onSelectArticle={setSelectedArticleId}
/>

<ArticleDetail 
  articleId={articleId}
  filters={filters}
  onBack={handleBack}
/>
```

### State Management

```tsx
const [filters, setFilters] = useState({
  difficulty: 'mid',
  language: 'en',
  category: ''
});

const [selectedArticleId, setSelectedArticleId] = useState(null);
```

---

## Support & Contributing

For issues or feature requests:
1. Check existing GitHub issues
2. Create new issue with:
   - Browser/OS information
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable

