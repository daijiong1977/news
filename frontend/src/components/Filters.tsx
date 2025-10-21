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
      const response = await fetch('http://localhost:8000/api/categories');
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
