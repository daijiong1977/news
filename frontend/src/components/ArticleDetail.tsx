import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
}

interface Comment {
  id: number;
  content: string;
  attitude: string;
  source?: string;
}

interface Props {
  articleId: number;
  filters: Filters;
  onBack: () => void;
}

const ArticleDetail: React.FC<Props> = ({ articleId, filters, onBack }) => {
  const [article, setArticle] = useState<any>(null);
  const [summaries, setSummaries] = useState<any[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});

  useEffect(() => {
    fetchArticleDetail();
  }, [articleId, filters]);

  const fetchArticleDetail = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        difficulty: filters.difficulty,
        language: filters.language,
      });
      const response = await axios.get(
        `/api/articles/${articleId}?${params}`
      );
      setArticle(response.data.article);
      setSummaries(response.data.summaries || []);
      setKeywords(response.data.keywords || []);
      setQuestions(response.data.questions || []);
      setComments(response.data.comments || []);
    } catch (err) {
      console.error('Failed to load article detail', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!article) return <div className="error">Article not found</div>;

  const handleAnswerSelect = (questionId: number, answerIndex: number) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionId]: answerIndex,
    });
  };

  return (
    <div className="article-detail">
      <button onClick={onBack} className="back-button">
        ← Back to Articles
      </button>

      <header className="detail-header">
        <h1>{filters.language === 'zh' && article.zh_title ? article.zh_title : article.title}</h1>
        <p className="source">{article.source}</p>
        <p className="date">{new Date(article.pub_date).toLocaleDateString()}</p>
        <span className="difficulty-badge">{filters.difficulty.toUpperCase()}</span>
      </header>

      {summaries.length > 0 && (
        <section className="summaries">
          <h2>Summary</h2>
          {summaries.map((summary) => (
            <div key={summary.id} className="summary-box">
              <p>{summary.text}</p>
            </div>
          ))}
        </section>
      )}

      {keywords.length > 0 && (
        <section className="keywords">
          <h2>Key Terms</h2>
          <div className="keywords-list">
            {keywords.map((keyword, idx) => (
              <span key={idx} className="keyword-tag">
                {keyword}
              </span>
            ))}
          </div>
        </section>
      )}

      {questions.length > 0 && (
        <section className="questions">
          <h2>Comprehension Check</h2>
          {questions.map((q) => (
            <div key={q.id} className="question-box">
              <p className="question-text">{q.question}</p>
              <div className="choices">
                {q.choices.map((choice, idx) => (
                  <label key={idx} className="choice">
                    <input
                      type="radio"
                      name={`q-${q.id}`}
                      checked={selectedAnswers[q.id] === idx}
                      onChange={() => handleAnswerSelect(q.id, idx)}
                    />
                    <span>{choice}</span>
                    {selectedAnswers[q.id] === idx && (
                      <span className="feedback">
                        {idx === q.correct_answer ? '✓ Correct!' : '✗ Try again'}
                      </span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {comments.length > 0 && (
        <section className="comments">
          <h2>Different Perspectives</h2>
          {comments.map((comment) => (
            <div key={comment.id} className={`comment-box attitude-${comment.attitude}`}>
              <p className="attitude-badge">{comment.attitude}</p>
              <p>{comment.content}</p>
              {comment.source && <p className="source-text">— {comment.source}</p>}
            </div>
          ))}
        </section>
      )}
    </div>
  );
};

export default ArticleDetail;
