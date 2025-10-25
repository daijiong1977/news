# 💡 Implementation Examples

## Example 1: Basic Integration into App.tsx

```tsx
import { useState } from 'react';
import './App.css';
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';
import ArticleInteractive from './components/ArticleInteractive'; // NEW
import Filters from './components/Filters';

interface FilterState {
  difficulty: 'easy' | 'mid' | 'hard';
  language: 'en' | 'zh';
  category: string;
}

type ViewMode = 'list' | 'detail' | 'interactive'; // NEW

function App() {
  const [filters, setFilters] = useState<FilterState>({
    difficulty: 'mid',
    language: 'en',
    category: '',
  });
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list'); // NEW

  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters({ ...filters, ...newFilters });
  };

  const handleSelectArticle = (id: number) => {
    setSelectedArticleId(id);
    setViewMode('interactive'); // NEW: Default to interactive view
  };

  const handleBack = () => {
    setSelectedArticleId(null);
    setViewMode('list');
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📰 News Reader</h1>
        <p>Learn news at your level</p>
      </header>

      <Filters filters={filters} onFilterChange={handleFilterChange} />

      <main className="app-main">
        {/* NEW: Interactive view */}
        {viewMode === 'interactive' && selectedArticleId ? (
          <ArticleInteractive
            articleId={selectedArticleId}
            onBack={handleBack}
          />
        ) 
        /* OLD: Detail view */
        : viewMode === 'detail' && selectedArticleId ? (
          <ArticleDetail
            articleId={selectedArticleId}
            filters={filters}
            onBack={handleBack}
          />
        )
        /* List view */
        : (
          <ArticleList
            filters={filters}
            onSelectArticle={handleSelectArticle}
          />
        )}
      </main>
    </div>
  );
}

export default App;
```

## Example 2: Add Buttons to ArticleList

```tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/ArticleList.css';

interface Article {
  id: number;
  title: string;
  description: string;
  source: string;
  pub_date: string;
  image?: string | null;
}

interface Props {
  filters: { difficulty: 'easy' | 'mid' | 'hard'; language: 'en' | 'zh'; category: string };
  onSelectArticle: (id: number, mode?: 'detail' | 'interactive') => void; // UPDATED
}

const ArticleList: React.FC<Props> = ({ filters, onSelectArticle }) => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          difficulty: filters.difficulty,
          language: filters.language,
          limit: '20',
        });
        const response = await axios.get(
          `http://localhost:8000/api/articles?${params}`
        );
        setArticles(response.data || []);
      } catch (err) {
        console.error('Failed to load articles', err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, [filters]);

  if (loading) {
    return <div className="loading">Loading articles...</div>;
  }

  return (
    <div className="article-grid">
      {articles.map((article) => (
        <div key={article.id} className="article-card">
          {article.image && (
            <img src={`http://localhost:8000${article.image}`} alt={article.title} className="article-image" />
          )}
          
          <div className="article-content">
            <h3>{article.title}</h3>
            <p className="article-snippet">{article.description}</p>
            
            <div className="article-meta">
              <span className="source">{article.source}</span>
              <span className="date">{new Date(article.pub_date).toLocaleDateString()}</span>
            </div>
          </div>

          {/* NEW: Action buttons */}
          <div className="article-actions">
            <button 
              className="btn btn-interactive"
              onClick={() => onSelectArticle(article.id, 'interactive')}
            >
              📚 Interactive
            </button>
            <button 
              className="btn btn-detail"
              onClick={() => onSelectArticle(article.id, 'detail')}
            >
              📄 Detail
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ArticleList;
```

Add to ArticleList.css:

```css
.article-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.article-actions .btn {
  flex: 1;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.article-actions .btn-interactive {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.article-actions .btn-interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.article-actions .btn-detail {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
}

.article-actions .btn-detail:hover {
  background: #e8e8e8;
  border-color: #667eea;
}
```

## Example 3: Tab Toggle Between Views

```tsx
import { useState } from 'react';
import './App.css';
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';
import ArticleInteractive from './components/ArticleInteractive';
import Filters from './components/Filters';

function App() {
  const [filters, setFilters] = useState({
    difficulty: 'mid' as const,
    language: 'en' as const,
    category: '',
  });
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [detailViewType, setDetailViewType] = useState<'interactive' | 'detail'>('interactive');

  const handleSelectArticle = (id: number) => {
    setSelectedArticleId(id);
  };

  const handleBack = () => {
    setSelectedArticleId(null);
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📰 News Reader</h1>
        <p>Learn news at your level</p>
      </header>

      <Filters filters={filters} onFilterChange={(newFilters) => setFilters({ ...filters, ...newFilters })} />

      <main className="app-main">
        {selectedArticleId ? (
          <>
            {/* Tab toggle */}
            <div className="view-toggle">
              <button 
                className={`tab ${detailViewType === 'interactive' ? 'active' : ''}`}
                onClick={() => setDetailViewType('interactive')}
              >
                📚 Interactive
              </button>
              <button 
                className={`tab ${detailViewType === 'detail' ? 'active' : ''}`}
                onClick={() => setDetailViewType('detail')}
              >
                📄 Detail
              </button>
              <button 
                className="tab close"
                onClick={handleBack}
              >
                ✕ Close
              </button>
            </div>

            {/* Content based on selected tab */}
            {detailViewType === 'interactive' ? (
              <ArticleInteractive
                articleId={selectedArticleId}
                onBack={handleBack}
              />
            ) : (
              <ArticleDetail
                articleId={selectedArticleId}
                filters={filters}
                onBack={handleBack}
              />
            )}
          </>
        ) : (
          <ArticleList
            filters={filters}
            onSelectArticle={handleSelectArticle}
          />
        )}
      </main>
    </div>
  );
}

export default App;
```

Add to App.css:

```css
.view-toggle {
  display: flex;
  gap: 12px;
  margin: 20px;
  padding: 0 20px;
  border-bottom: 2px solid #eee;
}

.view-toggle .tab {
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

.view-toggle .tab:hover {
  color: #667eea;
}

.view-toggle .tab.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.view-toggle .tab.close {
  margin-left: auto;
  padding: 12px 16px;
  color: #999;
}

.view-toggle .tab.close:hover {
  color: #f44336;
  background: #ffebee;
  border-radius: 6px;
}
```

## Example 4: Custom Content for Specific Article

```typescript
// If you want to customize content for specific articles:

const customContent: Record<number, Partial<InteractiveContent>> = {
  16: {
    easy: {
      summary: "Custom elementary summary for article 16...",
      keyTopics: ["topic1", "topic2"],
      // ... etc
    }
  },
  17: {
    mid: {
      summary: "Custom middle school summary for article 17...",
      // ... etc
    }
  }
};

// Then in your component:
const content = customContent[articleId] ? 
  { ...interactiveContent[selectedDifficulty], ...customContent[articleId][selectedDifficulty] } :
  interactiveContent[selectedDifficulty];
```

## Example 5: Fetch Real Content from Database

```typescript
// In ArticleInteractive.tsx, add this function:

const fetchArticleContent = async (articleId: number, difficulty: 'easy' | 'mid' | 'hard') => {
  try {
    // Option 1: Fetch from article_summaries table
    const response = await axios.get(
      `http://localhost:8000/api/articles/${articleId}/summaries`
    );
    
    const summaries = response.data;
    
    // Map database format to component format
    return {
      summary: summaries[difficulty]?.summary || 'No summary available',
      keyTopics: summaries[difficulty]?.keywords || [],
      backgroundInfo: summaries[difficulty]?.background || 'No background info',
      proArguments: summaries[difficulty]?.pro_arguments || [],
      conArguments: summaries[difficulty]?.con_arguments || [],
      questions: summaries[difficulty]?.questions || []
    };
  } catch (error) {
    console.error('Failed to fetch content:', error);
    return null;
  }
};

// Call it on mount or when difficulty changes:
useEffect(() => {
  const loadContent = async () => {
    const content = await fetchArticleContent(articleId, selectedDifficulty);
    if (content) {
      // Update interactiveContent with real data
      setDynamicContent(content);
    }
  };
  
  loadContent();
}, [articleId, selectedDifficulty]);
```

## Example 6: Add Analytics Tracking

```typescript
// Track when user completes quiz:

const handleAnswerSelect = (questionId: number, answerIndex: number) => {
  setSelectedAnswers({
    ...selectedAnswers,
    [questionId]: answerIndex,
  });
  
  // NEW: Track analytics
  trackEvent({
    eventType: 'quiz_answer',
    articleId: articleId,
    difficulty: selectedDifficulty,
    questionId: questionId,
    correct: answerIndex === content.questions.find(q => q.id === questionId)?.answer,
    timestamp: new Date().toISOString()
  });
};
```

## Example 7: Print Article

```typescript
// Add print button to header:

const handlePrint = () => {
  window.print();
};

// In CSS, add:
@media print {
  .article-interactive-wrapper {
    background: white;
  }
  
  .interactive-back-button,
  .interactive-controls {
    display: none;
  }
  
  .interactive-section {
    page-break-inside: avoid;
    box-shadow: none;
    border: 1px solid #ddd;
  }
}
```

## Example 8: Save Favorite / Bookmark

```typescript
// In ArticleInteractive component:

const [isFavorite, setIsFavorite] = useState(false);

const toggleFavorite = () => {
  setIsFavorite(!isFavorite);
  
  // Save to localStorage
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
  if (!isFavorite) {
    favorites.push(articleId);
  } else {
    favorites = favorites.filter(id => id !== articleId);
  }
  localStorage.setItem('favorites', JSON.stringify(favorites));
};

// In header:
<button 
  className={`favorite-btn ${isFavorite ? 'active' : ''}`}
  onClick={toggleFavorite}
>
  {isFavorite ? '❤️' : '🤍'} Save
</button>
```

---

These examples show you how to integrate, customize, and extend the ArticleInteractive component in various ways!
