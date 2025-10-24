"""
Backend handler for subscription form.
Receives POST requests from the signup form and creates subscribers in Buttondown only.
No local database storage - all user data is managed by Buttondown.
"""

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Buttondown API configuration
BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
BUTTONDOWN_API_URL = 'https://api.buttondown.email/v1/subscribers'

if not BUTTONDOWN_API_KEY:
    raise ValueError("BUTTONDOWN_API_KEY not set in environment variables")

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """
    Subscribe a new user to Buttondown.
    
    Expected JSON payload:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "read_level": "easy|mid|hard",
        "grade": "K-2|3-5|6-8|...|Adult",
        "categories": ["science", "tech", "business", "world"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'email', 'read_level']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
        
        # Prepare Buttondown payload
        # Store all metadata including read_level, grade, and categories
        metadata = {
            'read_level': data.get('read_level', '').lower(),
            'grade': data.get('grade', ''),
            'categories': ','.join(data.get('categories', []))
        }
        
        # Create tags for filtering
        tags = [data.get('read_level', 'unknown').lower()]
        if data.get('grade'):
            tags.append(data.get('grade').lower())
        
        buttondown_payload = {
            'email_address': data['email'],
            'name': data['name'],
            'metadata': metadata,
            'tags': tags
        }
        
        # Call Buttondown API
        headers = {
            'Authorization': f'Token {BUTTONDOWN_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            BUTTONDOWN_API_URL,
            json=buttondown_payload,
            headers=headers,
            timeout=10
        )
        
        # Handle Buttondown response
        if response.status_code == 201:
            return jsonify({
                'message': 'Successfully subscribed! Check your email to confirm.',
                'subscriber_id': response.json().get('id')
            }), 201
        elif response.status_code == 409:
            # Email already exists
            return jsonify({
                'message': 'This email is already subscribed. Check your preferences anytime.',
                'subscriber_id': response.json().get('id')
            }), 200
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return jsonify({
                'error': f'Buttondown API error: {error_detail}'
            }), response.status_code
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        print(f'Subscription error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['GET'])
def serve_form():
    """Serve the signup form."""
    try:
        form_path = os.path.join(os.path.dirname(__file__), 'signup_form.html')
        with open(form_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Signup form not found'}), 404

@app.route('/<filename>', methods=['GET'])
def serve_file(filename):
    """Serve HTML test files."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            return jsonify({'error': 'File not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local testing only; use a proper WSGI server (Gunicorn) in production
    app.run(debug=False, host='localhost', port=5001, threaded=True)
