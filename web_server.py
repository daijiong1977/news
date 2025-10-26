#!/usr/bin/env python3
"""
Simple Flask web server to serve the generated news website
"""
import os
from flask import Flask, send_file, render_template_string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(BASE_DIR, 'website')
MAIN_DIR = os.path.join(WEBSITE_DIR, 'main')

@app.route('/')
def index():
    """Serve the main index.html"""
    index_path = os.path.join(MAIN_DIR, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Website not found", 404

@app.route('/article_image/<path:filename>')
def serve_image(filename):
    """Serve article images"""
    image_dir = os.path.join(WEBSITE_DIR, 'article_image')
    file_path = os.path.join(image_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Image not found", 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy"}, 200

if __name__ == '__main__':
    # Run on port 5001 as expected by nginx
    app.run(host='127.0.0.1', port=5001, debug=False)
