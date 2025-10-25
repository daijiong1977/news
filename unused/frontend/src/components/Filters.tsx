import React, { useState, useEffect } from 'react';

interface Filters {
  difficulty: 'easy' | 'mid' | 'hard';
  language: 'en' | 'zh';
  category: string;
}

interface Props {
  filters: Filters;
  onFilterChange: (filters: Partial<Filters>) => void;
}

const FilterComponent: React.FC<Props> = ({ filters, onFilterChange }) => {
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    // Fetch available categories from API
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch('http://localhost:8008/api/categories');
      const data = await response.json();
      
      // Handle both array of objects {id, name} and array of strings
      if (Array.isArray(data)) {
        const categoryNames = data.map(cat => 
          typeof cat === 'string' ? cat : cat.name
        );
        setCategories(categoryNames);
      } else {
        // Fallback if response is not an array
        setCategories(['US News', 'Politics', 'Science', 'Technology']);
      }
    } catch (err) {
      console.error('Failed to load categories', err);
      // Fallback categories
      setCategories(['US News', 'Politics', 'Science', 'Technology']);
    }
  };

  return (
    <div className="filters">
      <h2 style={{ fontSize: '1.5em', color: '#333', margin: 0, flexShrink: 0 }}>📰 News Reader</h2>
      
      <div className="filter-categories">
        <div className="category-button-group">
          <button 
            className={`category-btn ${filters.category === '' ? 'active' : ''}`}
            onClick={() => onFilterChange({ category: '' })}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`category-btn ${filters.category === cat ? 'active' : ''}`}
              onClick={() => onFilterChange({ category: cat })}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-controls">
        <select
          className="level-select"
          value={filters.difficulty}
          onChange={(e) =>
            onFilterChange({ difficulty: e.target.value as any })
          }
        >
          <option value="easy">EASY</option>
          <option value="mid">MID</option>
          <option value="hard">HIGH</option>
        </select>

        <button
          className="lang-toggle"
          onClick={() =>
            onFilterChange({
              language: filters.language === 'en' ? 'zh' : 'en',
            })
          }
        >
          {filters.language === 'en' ? 'CN' : 'EN'}
        </button>
      </div>
    </div>
  );
};

export default FilterComponent;
