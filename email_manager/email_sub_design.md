# Project Design: Email-First "News for Kids"

This document outlines the technical design and implementation plan for building the "News for Kids" platform using an email-first, static-site architecture (Jamstack).

---

## 1. Project Goal & Brief

### Project Target
To create a low-maintenance, highly scalable, and cost-effective news service that delivers personalized, age-appropriate content to users primarily via email. The system should be automated, from content mining to email delivery, requiring minimal server resources.

### Architectural Brief
The system will be composed of three decoupled components:
1.  **Backend Processor:** A Python script (`run_mining_cycle.py`) runs on a schedule on a small VM. It fetches articles, uses an AI service to generate summaries and quizzes, processes images, and saves the final content as structured JSON files in a Git repository.
2.  **Email Service Provider (ESP):** A third-party service (e.g., **Buttondown**) that manages all subscribers, preferences (tags), and email sending. Our backend script will interact with its API to send personalized newsletters.
3.  **Static Frontend:** A fast, modern static website built with a generator like **Astro**. It reads the JSON files from the Git repository to pre-build all article and practice pages. The site is hosted on a static hosting platform (e.g., Netlify, Vercel) and requires no backend server to run.

---

## 2. Backend Data Format (The "Article JSON")

The backend script will generate one JSON file per article. This file is the single source of truth for both the website and the email content.

**Example File:** `content/articles/article-123.json`
```json
{
  "article_id": 123,
  "title": "Scientists Discover New Deep-Sea Fish",
  "original_url": "https://example.com/news/deep-sea-fish",
  "source_name": "Example News",
  "category": "Science",
  "publish_date": "2025-10-22T14:30:00Z",
  "image_web_url": "https://your-cdn.com/images/article-123-web.jpg",
  "image_thumb_url": "https://your-cdn.com/images/article-123-thumb.jpg",
  "summaries": {
    "easy": {
      "text": "Scientists found a new fish! It lives deep in the ocean and glows in the dark. It is very cool.",
      "vocab": ["deep-sea", "glows"]
    },
    "mid": {
      "text": "A new species of bioluminescent fish has been discovered by researchers exploring the Mariana Trench. The fish uses light to attract prey in the dark depths.",
      "vocab": ["bioluminescent", "species", "prey"]
    },
    "hard": {
      "text": "An expedition has yielded a remarkable discovery: a previously uncatalogued species of piscine life exhibiting advanced bioluminescence. This finding provides new insights into deep-sea ecosystems.",
      "vocab": ["uncatalogued", "piscine", "ecosystems"]
    },
    "cn": {
      "text": "科学家们发现了一种新的深海鱼。它生活在海洋深处，能在黑暗中发光。这非常酷。",
      "vocab": ["深海", "发光"]
    }
  },
  "practice_quiz": {
    "easy": [
      {
        "question": "Where does the new fish live?",
        "options": ["In a river", "Deep in the ocean", "In a lake"],
        "answer": "Deep in the ocean"
      }
    ],
    "mid": [
      {
        "question": "What does 'bioluminescent' mean?",
        "options": ["It can swim fast", "It produces its own light", "It is very large"],
        "answer": "It produces its own light"
      }
    ],
    "hard": [
      {
        "question": "What does this discovery provide insights into?",
        "options": ["Space travel", "Deep-sea ecosystems", "Ancient history"],
        "answer": "Deep-sea ecosystems"
      }
    ]
  }
}
```

---

## 3. Implementation To-Do List

### Phase 1: Backend Script Refactoring

*   **Task 1.1: Adapt Script to Generate JSON**
    *   **Technical Suggestion:** Use Python's built-in `json` library.
    *   **Implementation:** Modify `run_mining_cycle.py`. Instead of `INSERT`ing into SQLite, gather all the data for an article (summaries, quiz questions, etc.) into a Python dictionary that matches the structure above. Use `json.dump()` to write this dictionary to a new `.json` file in a `content/articles/` directory.

*   **Task 1.2: Implement Image Handling & Optimization**
    *   **Technical Suggestion:** Use the `Pillow` library (`pip install Pillow`).
    *   **Implementation:**
        1.  Create a new function, e.g., `process_and_save_image(image_url, article_id)`.
        2.  Inside this function, use `requests` to download the image data.
        3.  Use `Image.open()` from Pillow to load the image.
        4.  **Resize:** Create a "web" version by resizing to a max-width of 1200px, maintaining the aspect ratio.
        5.  **Compress:** Save this resized image as a JPEG with a quality setting of `80`.
        6.  **Save:** Store the final image in a `public/images/` directory with a name like `article-{article_id}-web.jpg`.
        7.  Return the public URL of the saved image to be stored in the article's JSON file.
    *   **Testing:** Create a small, separate test script (`test_image_processing.py`) that takes a sample image URL and runs it through your new function. Verify that the output file is created, check its dimensions, and confirm its file size is significantly smaller than the original.

*   **Task 1.3: Integrate Git Commits**
    *   **Technical Suggestion:** Use the `git` command-line tool via Python's `subprocess` module.
    *   **Implementation:** At the end of `run_mining_cycle.py`, after all new JSON files and images have been created, have the script execute the following shell commands:
        ```bash
        git add content/articles/*.json
        git add public/images/*.jpg
        git commit -m "Content update: Add X new articles"
        git push origin main
        ```

### Phase 2: Email Service Integration

*   **Task 2.1: Set Up Buttondown Account**
    *   **Technical Suggestion:** [buttondown.email](https://buttondown.email/)
    *   **Implementation:** Create an account. Get your API key and store it securely as an environment variable (`BUTTONDOWN_API_KEY`) on your server.

*   **Task 2.2: Send Newsletters via API**
    *   **Technical Suggestion:** Use Python's `requests` library to call the Buttondown API.
    *   **Implementation:** Add a new step to your main script. After the Git push, the script will loop through the newly processed articles. For each article, it will construct the email body (HTML) and make a POST request to the Buttondown API's `/v1/emails` endpoint to create and send a new broadcast email.

*   **Task 2.3: Implement Personalization (Advanced)**
    *   **Implementation:** Modify the email-sending step. The script will first fetch subscribers and their tags from Buttondown. It will then build personalized email bodies for different segments (e.g., a "Science" digest for users with the 'science' tag) and send them to the correct subscriber lists.

### Phase 3: Static Site Development

*   **Task 3.1: Set Up Astro Project**
    *   **Technical Suggestion:** [astro.build](https://astro.build/)
    *   **Implementation:** Initialize a new Astro project. Configure it to read content from the `content/articles/` directory.

*   **Task 3.2: Create Article & Practice Pages**
    *   **Implementation:**
        1.  Create a dynamic route in Astro: `src/pages/articles/[...slug].astro`.
        2.  This page will fetch the corresponding JSON file based on the slug.
        3.  Design the page to display the article title, image, and summaries. Use a small amount of JavaScript to handle the client-side switching between Easy, Mid, Hard, and CN tabs.
        4.  Create a separate dynamic route for practice pages: `src/pages/practice/[...slug].astro`. This page will render the quiz questions from the JSON file.

*   **Task 3.3: Implement Subscription Form**
    *   **Implementation:** Create a simple HTML form on the site that POSTs directly to your Buttondown account's subscription endpoint. No backend code is needed on your site for this.

### Phase 4: Deployment & Automation

*   **Task 4.1: Deploy Static Site**
    *   **Technical Suggestion:** Netlify, Vercel, or Cloudflare Pages.
    *   **Implementation:** Connect your Git repository to the hosting provider. Configure it to run the `astro build` command and deploy the resulting `dist` directory. The provider will now automatically re-deploy your site on every `git push`.

*   **Task 4.2: Schedule the Backend Script**
    *   **Technical Suggestion:** `cron` on your VM.
    *   **Implementation:** Set up a cron job to run `run_mining_cycle.py` on your desired schedule (e.g., twice a day).
        ```cron
        0 8,20 * * * cd /path/to/your/repo && /usr/bin/python3 run_mining_cycle.py >> /var/log/mining.log 2>&1
        ```
