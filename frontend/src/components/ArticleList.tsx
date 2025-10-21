import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Filters {
  difficulty: 'easy' | 'mid' | 'hard';
  language: 'en' | 'zh';
  category: string;
}

interface Article {
  id: number;
  title: string;
  zh_title?: string;
  description: string;
  source: string;
  pub_date: string;
  image?: string | null;
}

interface Props {
  filters: Filters;
  onSelectArticle: (id: number) => void;
}

const ArticleList: React.FC<Props> = ({ filters, onSelectArticle }) => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          difficulty: filters.difficulty,
          language: filters.language,
          ...(filters.category && { category: filters.category }),
        });
        // Use full URL instead of proxy
        const response = await axios.get(`http://localhost:8000/api/articles?${params}`);
        setArticles(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load articles');
        console.error('API Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, [filters]);

  if (loading) return <div className="loading">Loading articles...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="article-list">
      <h2>Articles</h2>
      {articles.length === 0 ? (
        <p>No articles found</p>
      ) : (
        <div className="articles-grid">
          {articles.map((article) => (
            <article
              key={article.id}
              className="article-card"
              onClick={() => onSelectArticle(article.id)}
            >
              {article.image && (
                <div className="article-image">
                  <img src={`http://localhost:8000${article.image}`} alt={article.title} />
                </div>
              )}
              <h3>
                {filters.language === 'zh' && article.zh_title
                  ? article.zh_title
                  : article.title}
              </h3>
              <p className="source">{article.source}</p>
              <p className="description">{article.description}</p>
              <p className="date">{new Date(article.pub_date).toLocaleDateString()}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default ArticleList;
