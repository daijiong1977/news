# Integration Guide: Adding ArticleInteractive to Your App

## Step-by-Step Integration

### Step 1: Import the Component

In your `App.tsx`, add the import:

```tsx
import ArticleInteractive from './components/ArticleInteractive';
```

### Step 2: Add State to Track View Mode

```tsx
interface FilterState {
  difficulty: 'easy' | 'mid' | 'hard';
  language: 'en' | 'zh';
  category: string;
}

function App() {
  const [filters, setFilters] = useState<FilterState>({
    difficulty: 'mid',
    language: 'en',
    category: '',
  });
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'detail' | 'interactive'>('list');

  // ... rest of component
}
```

### Step 3: Update Render Logic

Replace your current render with this:

```tsx
return (
  <div className="App">
    <header className="app-header">
      <h1>📰 News Reader</h1>
      <p>Learn news at your level</p>
    </header>

    {viewMode !== 'list' && (
      <button 
        className="app-back-button"
        onClick={() => {
          setSelectedArticleId(null);
          setViewMode('list');
        }}
      >
        ← Back to Articles
      </button>
    )}

    <main className="app-main">
      {viewMode === 'interactive' && selectedArticleId ? (
        <ArticleInteractive
          articleId={selectedArticleId}
          onBack={() => setViewMode('list')}
        />
      ) : viewMode === 'detail' && selectedArticleId ? (
        <ArticleDetail
          articleId={selectedArticleId}
          filters={filters}
          onBack={() => setViewMode('list')}
        />
      ) : (
        <>
          <Filters filters={filters} onFilterChange={handleFilterChange} />
          <ArticleList
            filters={filters}
            onSelectArticle={(id) => {
              setSelectedArticleId(id);
              setViewMode('interactive'); // or 'detail'
            }}
          />
        </>
      )}
    </main>
  </div>
);
```

### Step 4: Update ArticleList Component

Add a "Read Interactive" button next to each article:

```tsx
// In ArticleList.tsx, in the article card JSX:

<div className="article-actions">
  <button 
    className="read-interactive-btn"
    onClick={() => onSelectArticle(article.id, 'interactive')}
  >
    📚 Read (Interactive)
  </button>
  <button 
    className="read-detail-btn"
    onClick={() => onSelectArticle(article.id, 'detail')}
  >
    📄 Read (Detail)
  </button>
</div>
```

Then update the prop type:

```tsx
interface Props {
  filters: Filters;
  onSelectArticle: (id: number, mode?: 'detail' | 'interactive') => void;
}
```

### Step 5: Add CSS for Buttons

In `App.css`, add:

```css
.app-back-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.app-back-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.article-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.read-interactive-btn,
.read-detail-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.read-interactive-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.read-interactive-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.read-detail-btn {
  background: #f0f0f0;
  color: #333;
  border: 2px solid #ddd;
}

.read-detail-btn:hover {
  background: #e8e8e8;
  border-color: #667eea;
}
```

## Option 2: Replace ArticleDetail Completely

If you want to use ArticleInteractive as the main detail view:

```tsx
// In App.tsx

{selectedArticleId ? (
  <ArticleInteractive
    articleId={selectedArticleId}
    onBack={() => setSelectedArticleId(null)}
  />
) : (
  <>
    <Filters filters={filters} onFilterChange={handleFilterChange} />
    <ArticleList
      filters={filters}
      onSelectArticle={setSelectedArticleId}
    />
  </>
)}
```

This is simpler but removes the detail view option.

## Option 3: Tab Toggle in Detail View

Add tabs at the top of the detail section:

```tsx
const [detailView, setDetailView] = useState<'interactive' | 'detail'>('interactive');

// In render:
{selectedArticleId ? (
  <>
    <div className="view-tabs">
      <button 
        className={`tab ${detailView === 'interactive' ? 'active' : ''}`}
        onClick={() => setDetailView('interactive')}
      >
        📚 Interactive
      </button>
      <button 
        className={`tab ${detailView === 'detail' ? 'active' : ''}`}
        onClick={() => setDetailView('detail')}
      >
        📄 Detail
      </button>
    </div>
    
    {detailView === 'interactive' ? (
      <ArticleInteractive
        articleId={selectedArticleId}
        onBack={() => setSelectedArticleId(null)}
      />
    ) : (
      <ArticleDetail
        articleId={selectedArticleId}
        filters={filters}
        onBack={() => setSelectedArticleId(null)}
      />
    )}
  </>
) : (
  // ... list view
)}
```

CSS for tabs:

```css
.view-tabs {
  display: flex;
  gap: 12px;
  margin: 20px;
  border-bottom: 2px solid #eee;
}

.tab {
  padding: 12px 24px;
  border: none;
  background: transparent;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  color: #999;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}

.tab:hover {
  color: #667eea;
}

.tab.active {
  color: #667eea;
  border-bottom-color: #667eea;
}
```

## Testing Your Integration

1. **Start your servers:**
   ```bash
   # Terminal 1: Backend
   nohup python db_server.py > /tmp/db_server.log 2>&1 &
   
   # Terminal 2: Frontend
   cd /Users/jidai/news/frontend
   BROWSER=none PORT=3000 npm start
   ```

2. **Test the flow:**
   - Navigate to http://localhost:3000
   - Click on an article
   - You should see the ArticleInteractive component
   - Try changing difficulty levels
   - Try answering quiz questions

3. **Check for errors:**
   - Open browser DevTools (F12)
   - Check Console tab for errors
   - Check Network tab to see API calls

## Troubleshooting Integration

**Error: "Cannot find module 'ArticleInteractive'"**
- Make sure the import path is correct
- Check file is in `src/components/ArticleInteractive.tsx`

**Component doesn't show up**
- Check if viewMode state is being set correctly
- Verify conditional rendering logic
- Check browser console for errors

**Styling looks broken**
- Make sure `ArticleInteractive.css` exists
- Check import statement in component
- Clear browser cache

**Backend not responding**
- Make sure db_server.py is running
- Check port 8000 is accessible
- Look at /tmp/db_server.log for errors

## Configuration

### Default Difficulty Level

Change the initial difficulty in ArticleInteractive.tsx:

```typescript
const [selectedDifficulty, setSelectedDifficulty] = useState<'easy' | 'mid' | 'hard'>('easy'); // was 'mid'
```

### Default View Mode

Change the initial view in App.tsx:

```typescript
const [viewMode, setViewMode] = useState<'list' | 'detail' | 'interactive'>('interactive'); // was 'list'
```

## Performance Tips

1. **Lazy load the component:**
   ```tsx
   const ArticleInteractive = React.lazy(() => import('./components/ArticleInteractive'));
   
   <Suspense fallback={<div>Loading...</div>}>
     <ArticleInteractive ... />
   </Suspense>
   ```

2. **Memoize component:**
   ```tsx
   export default React.memo(ArticleInteractive);
   ```

3. **Cache article data:**
   ```tsx
   const [articleCache, setArticleCache] = useState<Map<number, ArticleData>>(new Map());
   ```

## Next Steps After Integration

1. ✅ Component is working
2. 📋 Test with all 20 articles
3. 📋 Gather user feedback on difficulty levels
4. 📋 Adjust content based on feedback
5. 📋 Add more features:
   - Bookmark articles
   - Track progress
   - Save quiz scores
   - Print articles
   - Share articles

---

**All set!** Your ArticleInteractive component is ready to use.

**Questions?** Check the documentation files for more details.
