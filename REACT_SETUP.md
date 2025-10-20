# React Frontend - Quick Start Guide

## What Was Created

A complete React + TypeScript frontend application for your news reader with the following structure:

### 📁 Folder Structure
```
frontend/
├── public/
│   └── index.html              # HTML entry point
├── src/
│   ├── components/
│   │   ├── ArticleList.tsx     # List of articles with filters
│   │   ├── ArticleDetail.tsx   # Article detail view with content
│   │   └── Filters.tsx         # Difficulty/Language/Category selectors
│   ├── App.tsx                 # Main app component
│   ├── App.css                 # Styling (responsive, modern design)
│   ├── index.tsx               # React entry point
│   └── index.css               # Global styles
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── README.md                   # Full documentation
└── setup.sh                    # Setup script
```

## Features Implemented

✅ **Three Difficulty Levels**: Easy, Mid (Middle School), Hard
✅ **Language Support**: English & Chinese (zh_title support)
✅ **Category Filtering**: Dynamic category selection
✅ **Article Display**: Title, source, description, publication date
✅ **Article Detail View**: 
  - Summaries for selected difficulty
  - Keywords/key terms
  - Comprehension questions with multiple choice
  - Different perspectives (comments with attitudes: support/neutral/against)
  - Visual feedback for correct/incorrect answers

✅ **Responsive Design**: Mobile-friendly layout
✅ **Modern UI**: Gradients, shadows, smooth transitions

## Installation & Running

### Step 1: Install Dependencies
```bash
cd /Users/jidai/news/frontend
npm install
```

Network issues? Try:
```bash
npm install --legacy-peer-deps
```

### Step 2: Start Development Server
```bash
npm start
```

The app opens at: `http://localhost:3000`

### Step 3: Build for Production
```bash
npm run build
```

Creates optimized build in `build/` folder

## Component Details

### ArticleList Component
- Fetches articles from `/api/articles` with filters
- Displays as grid of cards
- Click to view article details
- Shows title (in selected language), source, description, date

### ArticleDetail Component
- Fetches full article data including:
  - Summaries (3 levels)
  - Keywords (10 per level with explanations)
  - Questions (8/10/12 per level with 4 choices each)
  - Comments/perspectives (with attitude badges)
  - Background reading
- Interactive quiz with instant feedback
- Back button to return to list

### Filters Component
- Difficulty selector: Easy, Mid, Hard
- Language selector: English, 中文
- Category selector: Dynamic from `/api/categories`
- Applied in real-time

## API Integration Required

Your backend needs to provide these endpoints:

### 1. Get Articles List
```
GET /api/articles?difficulty=mid&language=en&category=tech
```

### 2. Get Article Detail
```
GET /api/articles/{id}?difficulty=mid&language=en
```

### 3. Get Categories
```
GET /api/categories
```

## Next Steps

1. **Set up backend API** - Python Flask/FastAPI server to serve articles data
2. **Connect to database** - Query your articles.db with summaries, questions, etc.
3. **Deploy** - Can be served from:
   - Same EC2 server via Node.js or Nginx
   - Separate frontend server
   - CDN (static files)

## File Sizes & Performance

- Modern React with TypeScript
- CSS optimized with media queries
- No external UI library (lightweight)
- Bundle size ~150KB minified

## Production Deployment

On EC2:
```bash
npm run build
npm install -g serve
serve -s build -l 3000
```

Or with PM2:
```bash
npm run build
pm2 start "serve -s build -l 3000" --name news-frontend
```

## Styling

The app uses custom CSS with:
- **Color scheme**: Purple gradients (#667eea, #764ba2)
- **Responsive breakpoints**: Mobile, tablet, desktop
- **Components styled**:
  - Article cards with hover effects
  - Filter selectors with focus states
  - Question cards with interactive feedback
  - Comment boxes with attitude indicators

## Mobile Support (Future)

This codebase can easily be converted to React Native for iOS/Android:
- Components are structured to be reusable
- State management is simple (React hooks)
- Minimal dependencies

## Common Issues & Solutions

### Network Error on npm install
```bash
npm install --legacy-peer-deps --registry https://registry.npmjs.org/
```

### Port 3000 already in use
```bash
npm start -- --port 3001
```

### TypeScript errors on first run
```bash
npm run build   # TypeScript will check and report errors
```

## Need Help?

1. Check `README.md` in frontend folder
2. Review component files for comments
3. Check console (F12) for React errors

---

**Ready to test?** Run:
```bash
cd /Users/jidai/news/frontend
npm install
npm start
```

You should see the app at `http://localhost:3000` in ~30 seconds! 🚀
