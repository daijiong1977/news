# ArticleInteractive Component - Documentation

## Overview

`ArticleInteractive.tsx` is a **dynamic, multi-level educational React component** designed to present articles with varying depth and complexity. Unlike the static HTML version, this component is fully interactive, pulls data from your database, and provides a seamless learning experience for different age groups and skill levels.

## Key Features

### ✨ **Three Difficulty Levels** (English Only)

1. **Elementary (Grades 3-5)** 
   - Simple vocabulary and concepts
   - Basic key topics
   - Simple quiz questions
   - No background info or perspectives

2. **Middle School (Grades 6-8)**
   - Intermediate complexity
   - More technical details
   - Background information section
   - Pro/Con perspectives
   - Moderate quiz questions

3. **High School (Grades 9-12)**
   - Advanced technical depth
   - Comprehensive background
   - Detailed pro/con arguments
   - Complex quiz questions with explanations

### 📚 **Content Sections**

- **Summary**: Tailored to difficulty level
- **Key Topics**: Relevant keywords and concepts
- **Background Information**: Context (for mid/hard levels)
- **Different Perspectives**: Pro and con arguments (for mid/hard levels)
- **Quiz**: 5 interactive questions with immediate feedback

### 🎨 **Design Highlights**

- Purple gradient theme (#667eea → #764ba2)
- Smooth animations and transitions
- Responsive grid layout
- Beautiful card-based design
- Interactive answer feedback (correct/incorrect)
- Mobile-friendly

## Component Props

```typescript
interface Props {
  articleId: number;        // Article ID from database
  onBack: () => void;       // Callback to return to article list
}
```

## State Management

```typescript
const [article, setArticle] = useState<ArticleData | null>(null);
const [selectedDifficulty, setSelectedDifficulty] = useState<'easy' | 'mid' | 'hard'>('mid');
const [loading, setLoading] = useState(true);
const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
```

## API Integration

The component fetches articles from your backend:

```typescript
GET /api/articles/{articleId}
// Returns: ArticleData with title, source, description, image, etc.
```

**Current Implementation:** Uses placeholder content organized by difficulty level. To make it **truly dynamic**, update the `interactiveContent` object to fetch from your `article_summaries` table.

## Placeholder Content Structure

```typescript
interactiveContent = {
  easy: {
    summary: "...",
    keyTopics: ["..."],
    backgroundInfo: "...",
    proArguments: [...],
    conArguments: [...],
    questions: [...]
  },
  mid: { /* similar structure */ },
  hard: { /* similar structure */ }
}
```

## Data Flow

```
ArticleList (click article)
    ↓
App.tsx (sets selectedArticleId)
    ↓
ArticleInteractive.tsx (fetches article + displays content)
    ↓
User selects difficulty
    ↓
Content updates based on selected level
    ↓
User answers quiz questions
    ↓
Immediate feedback (correct/incorrect)
```

## Styling

The component uses `ArticleInteractive.css` with:

- **Button Styling**: Gradient backgrounds, hover effects, active states
- **Card Layouts**: White cards with subtle shadows
- **Color Coding**: 
  - Green for pro arguments
  - Red for con arguments
  - Blue for feedback
- **Animations**: Slide-up effects, hover transforms
- **Responsive Grid**: Auto-fits to screen size

## Usage Example

```tsx
import ArticleInteractive from './components/ArticleInteractive';

<ArticleInteractive 
  articleId={16}
  onBack={() => setSelectedArticleId(null)}
/>
```

## Integration Steps

### 1. Update App.tsx

```tsx
import ArticleInteractive from './components/ArticleInteractive';

// Add state for interactive mode
const [useInteractiveView, setUseInteractiveView] = useState(false);

// In render:
{useInteractiveView && selectedArticleId ? (
  <ArticleInteractive
    articleId={selectedArticleId}
    onBack={() => {
      setSelectedArticleId(null);
      setUseInteractiveView(false);
    }}
  />
) : selectedArticleId ? (
  <ArticleDetail ... />
) : (
  <ArticleList
    onSelectArticle={(id) => {
      setSelectedArticleId(id);
      // Optional: setUseInteractiveView(true);
    }}
  />
)}
```

### 2. Add Toggle Button in ArticleList

```tsx
<button onClick={() => switchToInteractive()}>
  📚 Interactive Mode
</button>
```

### 3. Connect to Database (Future Enhancement)

```typescript
// Fetch real content from article_summaries table
const fetchSummaries = async (articleId: number) => {
  const response = await axios.get(
    `/api/articles/${articleId}/summaries`
  );
  // Map database content to interactiveContent structure
};
```

## Quiz Feature

- **Radio buttons** for single-select answers
- **Real-time feedback** on answer selection
- **Explanation display** with correct/incorrect visual cues
- **Answer tracking** prevents duplicate submissions

## Responsive Design

- Desktop: 2-column layout for perspectives
- Tablet: Single column for perspectives
- Mobile: Full-width, optimized touch targets

## Next Steps

1. ✅ Create ArticleInteractive component
2. ✅ Create ArticleInteractive.css styling
3. 📋 Update App.tsx to support both views
4. 📋 Fetch real summaries from database
5. 📋 Populate content dynamically based on article ID
6. 📋 Add difficulty/language persistence to localStorage

## Technical Stack

- **React 18**: Component framework
- **TypeScript**: Type safety
- **Axios**: HTTP requests
- **CSS3**: Styling with animations

## Performance Notes

- Lazy loads article data on mount
- Minimal re-renders with proper React hooks
- CSS animations use hardware acceleration
- Optimized for mobile devices

## Future Enhancements

- [ ] Add bookmark functionality
- [ ] Save quiz progress
- [ ] Share results with social media
- [ ] Add difficulty-specific tips
- [ ] Integrate with progress tracking
- [ ] Add speech-to-text for accessibility
- [ ] Support for multiple languages (future)

---

**Status**: ✅ Ready to integrate with existing React app

**File Locations**:
- Component: `/Users/jidai/news/frontend/src/components/ArticleInteractive.tsx`
- Styles: `/Users/jidai/news/frontend/src/styles/ArticleInteractive.css`
