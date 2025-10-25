import { useState } from 'react';
import './App.css';
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';
import Filters from './components/Filters';

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

  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters({ ...filters, ...newFilters });
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📰 News Reader</h1>
        <p>Learn news at your level</p>
      </header>

      <Filters filters={filters} onFilterChange={handleFilterChange} />

      <main className="app-main">
        {selectedArticleId ? (
          <ArticleDetail
            articleId={selectedArticleId}
            filters={filters}
            onBack={() => setSelectedArticleId(null)}
          />
        ) : (
          <ArticleList
            filters={filters}
            onSelectArticle={setSelectedArticleId}
          />
        )}
      </main>
    </div>
  );
}

export default App;
