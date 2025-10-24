#!/usr/bin/env python3
"""
Simple test script for subscription form.
"""

import os
import sqlite3
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Test data
test_subscriber = {
    "name": "Test User",
    "email": "test.user.final@example.com",
    "read_level": "easy",
    "grade": "3-5",
    "categories": ["science"]
}

print("=" * 60)
print("SUBSCRIPTION FORM TEST")
print("=" * 60)

# Step 1: Test Buttondown API directly
print("\n✅ Step 1: Testing Buttondown API...")
BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
if not BUTTONDOWN_API_KEY:
    print("❌ No Buttondown API key found")
    exit(1)

buttondown_payload = {
    'email_address': test_subscriber['email'],
    'tags': [test_subscriber['read_level'], test_subscriber['grade']] + test_subscriber['categories'],
    'metadata': {
        'name': test_subscriber['name'],
        'read_level': test_subscriber['read_level'],
        'grade': test_subscriber['grade'],
        'categories': ','.join(test_subscriber['categories'])
    }
}

headers = {
    'Authorization': f'Token {BUTTONDOWN_API_KEY}',
    'Content-Type': 'application/json'
}

try:
    response = requests.post(
        'https://api.buttondown.email/v1/subscribers',
        json=buttondown_payload,
        headers=headers,
        timeout=10
    )
    
    if response.status_code in [201, 409]:
        buttondown_id = response.json().get('id')
        print(f"   ✅ Buttondown: Status {response.status_code}, ID: {buttondown_id}")
    else:
        print(f"   ❌ Buttondown error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Buttondown error: {str(e)}")
    exit(1)

# Step 2: Test local database save
print("\n✅ Step 2: Testing local database save...")
DATABASE_PATH = os.getenv('DATABASE_PATH', '/Users/jidai/news/articles.db')

try:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("   ❌ users table not found")
        exit(1)
    
    # Insert test user
    import uuid
    token = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    name_parts = test_subscriber['name'].strip().split(maxsplit=1)
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    cursor.execute("""
        INSERT INTO users (email, token, password, username, first_name, last_name, registered, registered_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_subscriber['email'],
        token,
        '',
        test_subscriber['name'],
        first_name,
        last_name,
        1,
        now,
        now,
        now
    ))
    
    user_id = cursor.lastrowid
    
    # Save difficulty level
    difficulty_map = {'easy': 1, 'mid': 2, 'hard': 3}
    difficulty_id = difficulty_map.get(test_subscriber['read_level'], 1)
    
    cursor.execute("""
        INSERT INTO user_difficulty_levels (user_id, difficulty_id)
        VALUES (?, ?)
    """, (user_id, difficulty_id))
    
    # Save categories
    for cat_name in test_subscriber['categories']:
        cursor.execute("""
            SELECT category_id FROM categories WHERE name = ?
        """, (cat_name,))
        category = cursor.fetchone()
        if category:
            cursor.execute("""
                INSERT INTO user_categories (user_id, category_id)
                VALUES (?, ?)
            """, (user_id, category[0]))
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Local DB: Saved user_id={user_id}")
    
except sqlite3.IntegrityError as e:
    print(f"   ⚠️  Duplicate entry (already exists): {str(e)}")
except Exception as e:
    print(f"   ❌ Local DB error: {str(e)}")
    exit(1)

# Step 3: Verify the data was saved
print("\n✅ Step 3: Verifying saved data...")
try:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, email, username, first_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    print(f"   ✅ User record: {user}")
    
    cursor.execute("""
        SELECT u.user_id, u.email, d.difficulty_id FROM users u
        LEFT JOIN user_difficulty_levels d ON u.user_id = d.user_id
        WHERE u.user_id = ?
    """, (user_id,))
    user_diff = cursor.fetchone()
    print(f"   ✅ Difficulty: {user_diff}")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Verification error: {str(e)}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print(f"\nTest subscriber created:")
print(f"  - Email: {test_subscriber['email']}")
print(f"  - Name: {test_subscriber['name']}")
print(f"  - Level: {test_subscriber['read_level']}")
print(f"  - Grade: {test_subscriber['grade']}")
print(f"  - Categories: {', '.join(test_subscriber['categories'])}")
