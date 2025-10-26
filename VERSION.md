# Website Version History

## v1.0 - "Website Up Day 1" (October 26, 2025)

### Launch Features
- ✅ **Main Page** (`/main/index.html`)
  - Dynamic content loading with timestamped payloads
  - 4 difficulty levels: Relax (easy), Enjoy (middle), Research (high), CN (Chinese)
  - 3 categories: News, Science, Fun
  - Dark/light mode toggle
  - Responsive card layout

- ✅ **Article Page** (`/article_page/article.html`)
  - Interactive keyword tooltips with definitions
  - Vocabulary matching game
  - Multiple choice quiz with explanations
  - Article structure analysis (WHO/WHAT/WHERE/WHEN/WHY/HOW)
  - Background context with highlighted terms
  - Level-specific content (easy/middle/high)

- ✅ **Backend Infrastructure**
  - Database payload tracking (incremental updates)
  - Automated JSON payload generation
  - Image optimization and watermark removal
  - Deepseek AI content generation
  - RSS feed mining from multiple sources

- ✅ **Deployment**
  - Production server: news.6ray.com
  - HTTPS with SSL certificate
  - SELinux properly configured
  - Nginx static file serving

### Technical Stack
- Frontend: HTML, CSS (Tailwind via CDN), Vanilla JavaScript
- Backend: Python 3.12, SQLite
- Server: Amazon EC2, Nginx, Let's Encrypt SSL
- AI: Deepseek API for content analysis

---

**Dedicated to Helen, Daisy & Mattie**
