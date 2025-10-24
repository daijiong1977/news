# Email Manager Module

This directory contains all subscription and email delivery components.

## Files

- **signup_form.html** - Frontend signup form (hosted on GitHub Pages)
- **subscriber_handler.py** - Backend Flask API that receives form submissions and creates subscribers in Buttondown
- **test_buttondown_api.py** - Direct test script for Buttondown API connectivity
- **email_newsletter_template.html** - Email template with placeholders for daily digest
- **article_landing_page_template.html** - Landing page template for individual articles

## Setup

### 1. Local Testing

```bash
# Install dependencies
pip install flask requests python-dotenv

# Add Buttondown API key to .env in the repo root
BUTTONDOWN_API_KEY=your_key_here

# Start the backend server
python3 email_manager/subscriber_handler.py
```

The server will run on `http://localhost:5000`.

### 2. Test the API

```bash
# Direct test to Buttondown
python3 email_manager/test_buttondown_api.py

# Or via curl
curl -X POST http://localhost:5000/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "read_level": "easy",
    "grade": "3-5",
    "categories": ["science"]
  }'
```

### 3. Frontend Form URL

For local testing:
- `file:///Users/jidai/news/email_manager/signup_form.html` (and change form endpoint to `http://localhost:5000/api/subscribe`)

For production:
- Host on GitHub Pages at `https://yourorg.github.io/signup.html`
- Update endpoint to `https://news.6ray.com/api/subscribe`

## API Endpoint

**POST /api/subscribe**

Request body:
```json
{
  "name": "string",
  "email": "string",
  "read_level": "easy|mid|hard",
  "grade": "K-2|3-5|6-8|9-12|Adult",
  "categories": ["science", "tech", "business", "world"]
}
```

Success response (201):
```json
{
  "message": "Successfully subscribed! Check your email to confirm.",
  "subscriber_id": "uuid"
}
```

## Buttondown Integration

- Subscribers are created with tags: `[read_level, grade, ...categories]`
- Metadata is stored for future filtering and personalization
- All subscribers receive a confirmation email from Buttondown

## Environment Variables

Required in `.env`:
- `BUTTONDOWN_API_KEY` - Your Buttondown API token from https://buttondown.com/requests
