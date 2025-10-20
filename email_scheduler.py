#!/usr/bin/env python3
"""
Email Digest Scheduler
Runs daily at 8 AM and weekly on Mondays to send digests
"""

import os
import subprocess
import sys
from datetime import datetime, time
import schedule

# Configuration
SUBSCRIPTION_SERVICE_URL = 'http://localhost:5001'
EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY', '')

def send_daily_digest():
    """Send daily digest at 8 AM"""
    print(f"\n[{datetime.now()}] Sending daily digest...")
    try:
        import requests
        response = requests.post(
            f"{SUBSCRIPTION_SERVICE_URL}/send-digest",
            json={'frequency': 'daily'},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Daily digest sent: {data['sent']} succeeded, {data['failed']} failed")
        else:
            print(f"✗ Failed: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

def send_weekly_digest():
    """Send weekly digest on Mondays at 8 AM"""
    print(f"\n[{datetime.now()}] Sending weekly digest...")
    try:
        import requests
        response = requests.post(
            f"{SUBSCRIPTION_SERVICE_URL}/send-digest",
            json={'frequency': 'weekly'},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Weekly digest sent: {data['sent']} succeeded, {data['failed']} failed")
        else:
            print(f"✗ Failed: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

def schedule_jobs():
    """Schedule all digest jobs"""
    # Daily at 8 AM
    schedule.every().day.at("08:00").do(send_daily_digest)
    
    # Weekly on Monday at 8 AM
    schedule.every().monday.at("08:00").do(send_weekly_digest)
    
    print("✓ Scheduler initialized")
    print("  • Daily digest: 8:00 AM every day")
    print("  • Weekly digest: 8:00 AM every Monday")

def run():
    """Run the scheduler"""
    print("=" * 60)
    print("Email Digest Scheduler")
    print("=" * 60)
    
    schedule_jobs()
    
    print("\nScheduler is running. Press Ctrl+C to exit.")
    
    try:
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n✓ Scheduler stopped")

if __name__ == '__main__':
    run()
