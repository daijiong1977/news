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
      const response = await fetch('/api/categories');
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories', err);
      // Fallback categories
      setCategories(['Technology', 'Science', 'Politics']);
    }
  };

  return (
    <div className="filters">
      <div className="filter-group">
        <label htmlFor="difficulty">Difficulty:</label>
        <select
          id="difficulty"
          value={filters.difficulty}
          onChange={(e) =>
            onFilterChange({ difficulty: e.target.value as any })
          }
        >
          <option value="easy">Easy (Elementary)</option>
          <option value="mid">Medium (Middle School)</option>
          <option value="hard">Hard (High School)</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="language">Language:</label>
        <select
          id="language"
          value={filters.language}
          onChange={(e) =>
            onFilterChange({ language: e.target.value as any })
          }
        >
          <option value="en">English</option>
          <option value="zh">中文 (Chinese)</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="category">Category:</label>
        <select
          id="category"
          value={filters.category}
          onChange={(e) => onFilterChange({ category: e.target.value })}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default FilterComponent;
