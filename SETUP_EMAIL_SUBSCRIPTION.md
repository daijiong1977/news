# Email Subscription System - Setup Complete

## ✅ What We've Built

We've created a complete subscription management system for "News for Kids" with a clean separation of frontend and backend:

### Frontend (Static, hosted on GitHub Pages)
- **`email_manager/signup_form.html`** - Beautiful, responsive signup form
  - Collects: Name, Email, Reading Level (Easy/Mid/Hard), Grade (K-2, 3-5, 6-8, 9-12, Adult)
  - Optional: Category preferences (Science, Tech, Business, World)
  - Validates form before submission
  - Shows success/error messages inline

### Backend (Flask API, runs on your VM)
- **`email_manager/subscriber_handler.py`** - Flask REST API
  - Receives POST requests from the signup form
  - Validates all required fields
  - Creates subscribers directly in Buttondown with:
    - Tags (for segmentation): `[read_level, grade, ...categories]`
    - Metadata (for future use)
  - Handles duplicates gracefully (409 conflict → user-friendly message)
  - Returns JSON responses for frontend to display

### Templates & Documentation
- **`email_manager/email_newsletter_template.html`** - Daily newsletter template with placeholders
- **`email_manager/article_landing_page_template.html`** - Individual article page template
- **`email_manager/test_buttondown_api.py`** - Direct API test script
- **`email_manager/README.md`** - Complete setup documentation

## 🚀 Next Steps

### 1. Verify Your Buttondown API Key
The test script shows `401 Unauthorized`, which means the API key may be invalid. Please verify:
1. Go to https://buttondown.com/requests
2. Copy your actual API token (should start with a UUID or similar)
3. Update `.env` with the correct key:
   ```
   BUTTONDOWN_API_KEY=your_actual_token
   ```

### 2. Test Again
```bash
python3 email_manager/test_buttondown_api.py
```
Should show a `201 Created` response.

### 3. Update Form Endpoint
Currently, the form posts to `http://localhost:5000/api/subscribe`. Change it to your production endpoint:
```javascript
// In email_manager/signup_form.html, line ~130
const response = await fetch('https://news.6ray.com/api/subscribe', {
```

### 4. Deploy

**Backend (to your VM):**
```bash
# SSH to your VM
# Copy subscriber_handler.py to /var/www/news/email_manager/
# Copy .env to /var/www/news/
# Install dependencies: pip install flask requests python-dotenv
# Run with Gunicorn in production:
gunicorn -w 4 -b 0.0.0.0:8000 email_manager.subscriber_handler:app
```

**Frontend (to GitHub Pages):**
- Commit `email_manager/signup_form.html` to your repo
- Host on GitHub Pages
- Link from your main site

### 5. Integration Points (Future)

Once this is working, we'll connect:
1. **Email sending**: Generate daily emails using `email_newsletter_template.html`
2. **Article pages**: Generate static pages using `article_landing_page_template.html`
3. **Segmentation**: Use the `read_level` and `grade` tags to send targeted newsletters

## 📋 Current Architecture

```
GitHub Pages
     ↓
signup_form.html (user submits form)
     ↓
https://news.6ray.com/api/subscribe (your VM)
     ↓
subscriber_handler.py (validates & creates subscriber)
     ↓
Buttondown API (stores subscriber with tags/metadata)
     ↓
Confirmation email sent to subscriber
```

## ⚠️ Important Notes

1. **API Key**: Must be kept in `.env` and added to `.gitignore` (already done)
2. **CORS**: If the form is on a different domain, add CORS headers to the Flask app
3. **Rate Limiting**: Consider adding rate limiting to prevent abuse
4. **Email Confirmation**: Buttondown handles this automatically

## Files Summary

```
email_manager/
├── signup_form.html                    # Frontend form
├── subscriber_handler.py               # Backend API (Flask)
├── test_buttondown_api.py             # API test script
├── email_newsletter_template.html     # Daily email template
├── article_landing_page_template.html # Article page template
└── README.md                          # Setup guide
```

## Testing Checklist

- [ ] Verify Buttondown API key is valid
- [ ] Run `test_buttondown_api.py` successfully (should get 201)
- [ ] Test signup form locally (submit form, check for success message)
- [ ] Check Buttondown dashboard to see new subscriber
- [ ] Verify subscriber has correct tags and metadata
- [ ] Deploy backend to VM
- [ ] Deploy frontend to GitHub Pages
- [ ] Test end-to-end from GitHub Pages form to Buttondown
