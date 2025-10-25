import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/ArticleDetail.css';
import ArticleInteractive from './ArticleInteractive';

interface Filters {
  difficulty: 'easy' | 'mid' | 'hard';
  language: 'en' | 'zh';
  category: string;
}

interface Question {
  id: number;
  question: string;
  choices: string[];
  correct_answer: number;
  explanation?: string;
}

interface Comment {
  id: number;
  content: string;
  attitude: 'positive' | 'neutral' | 'negative';
  source?: string;
}

interface Keyword {
  word: string;
  explanation: string;
}

interface ArticleData {
  id: number;
  title: string;
  zh_title?: string;
  source: string;
  pub_date: string;
  description: string;
  image_url?: string;
}

interface Props {
  articleId: number;
  filters: Filters;
  onBack: () => void;
}

const ArticleDetail: React.FC<Props> = ({ articleId, filters, onBack }) => {
  const [article, setArticle] = useState<ArticleData | null>(null);
  const [summary, setSummary] = useState<string>('');
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [backgroundReading, setBackgroundReading] = useState<string>('');
  const [analysis, setAnalysis] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [showDetailed, setShowDetailed] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState<'en' | 'zh'>(filters.language);
  const [viewMode, setViewMode] = useState<'standard' | 'interactive'>('standard');

  useEffect(() => {
    const fetchArticleDetail = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          difficulty: filters.difficulty,
          language: filters.language,
        });
        // Use full URL instead of proxy
        const response = await axios.get(`http://localhost:8008/api/articles/${articleId}?${params}`);
        
        const data = response.data;
        setArticle(data.article);
        setSummary(data.summary || '');
        setKeywords(data.keywords || []);
        setQuestions(data.questions || []);
        setComments(data.comments || []);
        setBackgroundReading(data.background_reading || '');
        setAnalysis(data.analysis || '');
      } catch (err) {
        console.error('Failed to load article detail', err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticleDetail();
  }, [articleId, filters]);

  const handleAnswerSelect = (questionId: number, answerIndex: number) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionId]: answerIndex,
    });
  };

  const toggleLanguage = (lang: 'en' | 'zh') => {
    setCurrentLanguage(lang);
  };

  if (loading) {
    return (
      <div className="article-detail-wrapper">
        <div className="loading">Loading article details...</div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="article-detail-wrapper">
        <div className="error">Article not found</div>
        <button onClick={onBack} className="detail-back-button">
          ← Back to List
        </button>
      </div>
    );
  }

  const displayTitle = currentLanguage === 'zh' && article.zh_title ? article.zh_title : article.title;

  // If interactive view is selected, show the interactive component
  if (viewMode === 'interactive') {
    return (
      <div className="article-detail-wrapper">
        <button onClick={() => setViewMode('standard')} className="detail-back-button">
          ← Back to Standard View
        </button>
        <ArticleInteractive articleId={articleId} onBack={onBack} />
      </div>
    );
  }

  // Standard view
  return (
    <div className="article-detail-wrapper">
      <div className="detail-header-actions">
        <button onClick={onBack} className="detail-back-button">
          ← Back to Articles
        </button>
        <button 
          onClick={() => setViewMode('interactive')} 
          className="view-mode-toggle"
          title="Switch to interactive view"
        >
          ✨ Interactive View
        </button>
      </div>

      {/* Article Preview Section */}
      <div className="article-preview">
        <div className="preview-header">
          <div className="preview-content">
            <h1>{displayTitle}</h1>

            <div className="preview-meta">
              <div className="meta-item">
                <span className="meta-icon">📰</span>
                <span>{article.source}</span>
              </div>
              <div className="meta-item">
                <span className="meta-icon">📅</span>
                <span>{new Date(article.pub_date).toLocaleDateString()}</span>
              </div>
              <div className="meta-item">
                <span className="meta-icon">📚</span>
                <span>{filters.difficulty}</span>
              </div>
            </div>

            <p className="preview-snippet">{article.description}</p>

            <div className="language-toggle">
              <button
                className={`lang-btn ${currentLanguage === 'en' ? 'active' : ''}`}
                onClick={() => toggleLanguage('en')}
              >
                English
              </button>
              {article.zh_title && (
                <button
                  className={`lang-btn ${currentLanguage === 'zh' ? 'active' : ''}`}
                  onClick={() => toggleLanguage('zh')}
                >
                  中文
                </button>
              )}
            </div>
          </div>

          <div>
            {article.image_url ? (
              <img src={article.image_url} alt={article.title} className="preview-image" />
            ) : (
              <div className="preview-image placeholder">📰</div>
            )}
          </div>
        </div>
      </div>

      {/* Summary Section */}
      {summary && (
        <section className="detail-section">
          <h2 className="section-title">
            <span className="section-title-icon">📖</span>
            Summary
          </h2>
          <div className="summary-container">
            <p className="summary-text">{summary}</p>
          </div>
        </section>
      )}

      {/* Keywords Section */}
      {keywords.length > 0 && (
        <section className="detail-section">
          <h2 className="section-title">
            <span className="section-title-icon">🔑</span>
            Key Words & Concepts
          </h2>
          <div className="keywords-grid">
            {keywords.map((keyword, index) => (
              <div key={index} className="keyword-card">
                <div className="keyword-word">{keyword.word}</div>
                <div className="keyword-explanation">{keyword.explanation}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Background Reading Section */}
      {backgroundReading && (
        <section className="detail-section">
          <h2 className="section-title">
            <span className="section-title-icon">🌍</span>
            Background Reading
          </h2>
          <div className="background-box">{backgroundReading}</div>
        </section>
      )}

      {/* Dive Deeper Button */}
      {(questions.length > 0 || comments.length > 0 || analysis) && (
        <div className="dive-button-container">
          <button
            className="dive-button"
            onClick={() => setShowDetailed(!showDetailed)}
          >
            {showDetailed ? '↑ Show Less' : '↓ Dive Deeper'}
          </button>
        </div>
      )}

      {/* Questions Section */}
      {showDetailed && questions.length > 0 && (
        <section className="quiz-container">
          <h2 className="section-title">
            <span className="section-title-icon">❓</span>
            Test Your Understanding
          </h2>

          {questions.map((question, index) => (
            <div key={question.id} className="quiz-question">
              <div className="quiz-question-number">Question {index + 1}</div>
              <div className="quiz-question-text">{question.question}</div>

              <div className="quiz-options">
                {question.choices.map((choice, choiceIndex) => (
                  <label key={choiceIndex} className="quiz-option">
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      checked={selectedAnswers[question.id] === choiceIndex}
                      onChange={() => handleAnswerSelect(question.id, choiceIndex)}
                    />
                    <span>{choice}</span>
                  </label>
                ))}
              </div>

              {selectedAnswers[question.id] !== undefined && (
                <div className="quiz-explanation">
                  <strong>
                    {selectedAnswers[question.id] === question.correct_answer
                      ? '✓ Correct!'
                      : '✗ Not quite right'}
                  </strong>
                  {question.explanation && <p>{question.explanation}</p>}
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      {/* Comments/Perspectives Section */}
      {showDetailed && comments.length > 0 && (
        <section className="detail-section">
          <h2 className="section-title">
            <span className="section-title-icon">💬</span>
            Different Perspectives
          </h2>
          <div className="comments-container">
            {comments.map((comment) => (
              <div key={comment.id} className={`comment-card ${comment.attitude}`}>
                <div className="comment-header">
                  <span className={`comment-attitude ${comment.attitude}`}>
                    {comment.attitude}
                  </span>
                  {comment.source && <span className="comment-source">{comment.source}</span>}
                </div>
                <div className="comment-text">{comment.content}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Analysis Section */}
      {showDetailed && analysis && (
        <section className="detail-section">
          <h2 className="section-title">
            <span className="section-title-icon">🔍</span>
            Deep Analysis
          </h2>
          <div className="analysis-box">{analysis}</div>
        </section>
      )}
    </div>
  );
};

export default ArticleDetail;
