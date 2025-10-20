#!/usr/bin/env python3
"""Interactive configuration setup tool for the daily news digest."""

import json
import pathlib
import sys
from typing import Any


CONFIG_FILE = pathlib.Path("config.json")


def load_config() -> dict[str, Any]:
    """Load existing configuration or return defaults."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "rss_sources": [],
        "smtp": {"enabled": False, "gmail_address": "", "gmail_app_password": ""},
        "recipients": [],
        "digest_settings": {
            "articles_per_source": 3,
            "hours_lookback": 24,
            "include_images": True,
            "output_html": "daily_digest.html",
            "output_json": "daily_digest.json",
        },
    }


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"\n✓ Configuration saved to {CONFIG_FILE}")


def manage_rss_sources(config: dict[str, Any]) -> None:
    """Manage RSS feed sources."""
    print("\n" + "=" * 60)
    print("RSS FEED SOURCES MANAGEMENT")
    print("=" * 60)

    sources = config.get("rss_sources", [])
    
    while True:
        print("\n1. Add RSS source")
        print("2. Edit RSS source")
        print("3. Delete RSS source")
        print("4. List RSS sources")
        print("5. Back to main menu")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            name = input("Enter source name (e.g., 'PBS NewsHour'): ").strip()
            if not name:
                print("✗ Source name cannot be empty")
                continue
            url = input("Enter RSS feed URL: ").strip()
            if not url:
                print("✗ URL cannot be empty")
                continue
            enabled = input("Enable this source? (y/n): ").strip().lower() == "y"
            
            sources.append({"name": name, "url": url, "enabled": enabled})
            print(f"✓ Added source: {name}")
            
        elif choice == "2":
            if not sources:
                print("✗ No sources to edit")
                continue
            for idx, src in enumerate(sources, 1):
                print(f"{idx}. {src['name']} ({src['url']}) - {'Enabled' if src['enabled'] else 'Disabled'}")
            try:
                idx = int(input("Select source number to edit: ").strip()) - 1
                if 0 <= idx < len(sources):
                    src = sources[idx]
                    src["name"] = input(f"Enter name [{src['name']}]: ").strip() or src["name"]
                    src["url"] = input(f"Enter URL [{src['url']}]: ").strip() or src["url"]
                    src["enabled"] = input(f"Enable? (y/n) [{'y' if src['enabled'] else 'n'}]: ").strip().lower() in ("y", "")
                    print("✓ Source updated")
                else:
                    print("✗ Invalid selection")
            except ValueError:
                print("✗ Invalid input")
                
        elif choice == "3":
            if not sources:
                print("✗ No sources to delete")
                continue
            for idx, src in enumerate(sources, 1):
                print(f"{idx}. {src['name']}")
            try:
                idx = int(input("Select source number to delete: ").strip()) - 1
                if 0 <= idx < len(sources):
                    removed = sources.pop(idx)
                    print(f"✓ Removed: {removed['name']}")
                else:
                    print("✗ Invalid selection")
            except ValueError:
                print("✗ Invalid input")
                
        elif choice == "4":
            if not sources:
                print("No RSS sources configured yet")
            else:
                for idx, src in enumerate(sources, 1):
                    status = "✓ Enabled" if src["enabled"] else "✗ Disabled"
                    print(f"\n{idx}. {src['name']} {status}")
                    print(f"   URL: {src['url']}")
                    
        elif choice == "5":
            config["rss_sources"] = sources
            return
        else:
            print("✗ Invalid option")


def manage_smtp(config: dict[str, Any]) -> None:
    """Configure Google SMTP settings."""
    print("\n" + "=" * 60)
    print("GOOGLE SMTP CONFIGURATION")
    print("=" * 60)
    print("""
Note: To use Gmail with this app:
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or your device)
4. Copy the 16-character password and paste it here
""")
    
    while True:
        smtp = config.get("smtp", {})
        
        print(f"\n1. Email address: {smtp.get('gmail_address', 'Not set')}")
        print(f"2. App password: {'Set' if smtp.get('gmail_app_password') else 'Not set'}")
        print("3. Enable SMTP: Yes" if smtp.get("enabled") else "3. Enable SMTP: No")
        print("4. Test connection")
        print("5. Back to main menu")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            email = input("Enter Gmail address: ").strip()
            if email and "@" in email:
                smtp["gmail_address"] = email
                print("✓ Email address updated")
            else:
                print("✗ Invalid email address")
                
        elif choice == "2":
            password = input("Enter app password (16 characters): ").strip()
            if len(password) >= 16 or (password and len(password) == 16 and " " not in password):
                smtp["gmail_app_password"] = password
                print("✓ App password updated")
            else:
                print("✗ App password should be 16 characters (from Google)")
                
        elif choice == "3":
            current = smtp.get("enabled", False)
            smtp["enabled"] = not current
            print(f"✓ SMTP {'enabled' if smtp['enabled'] else 'disabled'}")
            
        elif choice == "4":
            if not smtp.get("gmail_address") or not smtp.get("gmail_app_password"):
                print("✗ Email and password must be set first")
            else:
                test_smtp_connection(smtp)
                
        elif choice == "5":
            config["smtp"] = smtp
            return
        else:
            print("✗ Invalid option")


def test_smtp_connection(smtp: dict[str, Any]) -> None:
    """Test SMTP connection."""
    import smtplib
    
    try:
        print("Testing connection...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5)
        server.login(smtp["gmail_address"], smtp["gmail_app_password"])
        server.quit()
        print("✓ Connection successful!")
    except smtplib.SMTPAuthenticationError:
        print("✗ Authentication failed. Check email and app password.")
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def manage_recipients(config: dict[str, Any]) -> None:
    """Manage email recipients."""
    print("\n" + "=" * 60)
    print("EMAIL RECIPIENTS MANAGEMENT")
    print("=" * 60)
    
    recipients = config.get("recipients", [])
    
    while True:
        print("\n1. Add recipient")
        print("2. Remove recipient")
        print("3. List recipients")
        print("4. Back to main menu")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            email = input("Enter recipient email address: ").strip()
            if "@" in email and "." in email:
                if email not in recipients:
                    recipients.append(email)
                    print(f"✓ Added: {email}")
                else:
                    print("✗ Email already in list")
            else:
                print("✗ Invalid email address")
                
        elif choice == "2":
            if not recipients:
                print("✗ No recipients to remove")
                continue
            for idx, email in enumerate(recipients, 1):
                print(f"{idx}. {email}")
            try:
                idx = int(input("Select recipient number to remove: ").strip()) - 1
                if 0 <= idx < len(recipients):
                    removed = recipients.pop(idx)
                    print(f"✓ Removed: {removed}")
                else:
                    print("✗ Invalid selection")
            except ValueError:
                print("✗ Invalid input")
                
        elif choice == "3":
            if recipients:
                for idx, email in enumerate(recipients, 1):
                    print(f"{idx}. {email}")
            else:
                print("No recipients configured yet")
                
        elif choice == "4":
            config["recipients"] = recipients
            return
        else:
            print("✗ Invalid option")


def manage_digest_settings(config: dict[str, Any]) -> None:
    """Configure digest generation settings."""
    print("\n" + "=" * 60)
    print("DIGEST SETTINGS")
    print("=" * 60)
    
    settings = config.get("digest_settings", {})
    
    while True:
        print(f"\n1. Articles per source: {settings.get('articles_per_source', 3)}")
        print(f"2. Hours lookback: {settings.get('hours_lookback', 24)}")
        print(f"3. Include images: {'Yes' if settings.get('include_images', True) else 'No'}")
        print(f"4. HTML output file: {settings.get('output_html', 'daily_digest.html')}")
        print(f"5. JSON output file: {settings.get('output_json', 'daily_digest.json')}")
        print("6. Back to main menu")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            try:
                num = int(input("Enter articles per source (1-10): ").strip())
                if 1 <= num <= 10:
                    settings["articles_per_source"] = num
                    print(f"✓ Set to {num}")
                else:
                    print("✗ Must be between 1 and 10")
            except ValueError:
                print("✗ Invalid number")
                
        elif choice == "2":
            try:
                hours = int(input("Enter hours lookback (1-168): ").strip())
                if 1 <= hours <= 168:
                    settings["hours_lookback"] = hours
                    print(f"✓ Set to {hours} hours")
                else:
                    print("✗ Must be between 1 and 168")
            except ValueError:
                print("✗ Invalid number")
                
        elif choice == "3":
            current = settings.get("include_images", True)
            settings["include_images"] = not current
            print(f"✓ Images {'enabled' if settings['include_images'] else 'disabled'}")
            
        elif choice == "4":
            filename = input("Enter HTML output filename: ").strip()
            if filename:
                settings["output_html"] = filename
                print(f"✓ Set to {filename}")
                
        elif choice == "5":
            filename = input("Enter JSON output filename: ").strip()
            if filename:
                settings["output_json"] = filename
                print(f"✓ Set to {filename}")
                
        elif choice == "6":
            config["digest_settings"] = settings
            return
        else:
            print("✗ Invalid option")


def main() -> None:
    """Main menu."""
    print("\n" + "=" * 60)
    print("DAILY NEWS DIGEST - CONFIGURATION SETUP")
    print("=" * 60)
    
    config = load_config()
    
    while True:
        print("\n1. Manage RSS Feed Sources")
        print("2. Configure Google SMTP Email")
        print("3. Manage Email Recipients")
        print("4. Digest Settings")
        print("5. View Full Configuration")
        print("6. Save and Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            manage_rss_sources(config)
        elif choice == "2":
            manage_smtp(config)
        elif choice == "3":
            manage_recipients(config)
        elif choice == "4":
            manage_digest_settings(config)
        elif choice == "5":
            print("\n" + json.dumps(config, indent=2))
        elif choice == "6":
            save_config(config)
            print("\nGoodbye!")
            break
        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
