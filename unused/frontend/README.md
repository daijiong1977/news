# News Reader React Frontend

A modern React application for reading news articles at different difficulty levels with language support.

## Features

- 📚 **Three Difficulty Levels**: Easy (Elementary), Mid (Middle School), Hard (High School)
- 🌐 **Multi-language Support**: English and Chinese
- 📂 **Category Filtering**: Browse articles by category
- 📖 **Interactive Reading**: 
  - Article summaries
  - Key terms and keywords
  - Comprehension questions
  - Multiple perspectives and comments
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- ⚡ **Fast Performance**: React with optimized components

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── ArticleList.tsx
│   │   ├── ArticleDetail.tsx
│   │   └── Filters.tsx
│   ├── App.tsx
│   ├── App.css
│   ├── index.tsx
│   └── index.css
├── package.json
└── tsconfig.json
```

## Setup Instructions

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

## API Integration

The app expects the following API endpoints:

### Get Articles
```
GET /api/articles?difficulty=mid&language=en&category=tech
```

Response:
```json
[
  {
    "id": 1,
    "title": "Article Title",
    "zh_title": "文章标题",
    "description": "...",
    "source": "BBC",
    "pub_date": "2025-10-20"
  }
]
```

### Get Article Detail
```
GET /api/articles/1?difficulty=mid&language=en
```

Response:
```json
{
  "article": { ... },
  "summaries": [ ... ],
  "keywords": [ ... ],
  "questions": [ ... ],
  "comments": [ ... ]
}
```

### Get Categories
```
GET /api/categories
```

Response:
```json
["Technology", "Science", "Politics", ...]
```

## Building for Production

```bash
# Create optimized production build
npm run build

# Build folder contains static files ready to deploy
```

## Environment Variables

Create `.env` file in frontend directory (if needed):

```
REACT_APP_API_URL=http://localhost:8000
```

## Technologies Used

- **React 18** - UI library
- **TypeScript** - Type safety
- **React Router** - Navigation (future)
- **Axios** - HTTP client
- **CSS3** - Styling with gradients and animations

## Future Enhancements

- [ ] React Router for multiple pages
- [ ] User authentication
- [ ] Save progress and bookmarks
- [ ] Dark mode support
- [ ] PWA for offline reading
- [ ] React Native for mobile app

## License

MIT
