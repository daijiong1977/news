#!/bin/bash
# Setup script for Buttondown API token

echo "=================================================="
echo "Buttondown API Token Setup"
echo "=================================================="
echo ""
echo "To get your Buttondown API token:"
echo ""
echo "1. Go to https://buttondown.email/settings/api"
echo "2. Click 'Create a token' (if you don't have one)"
echo "3. Copy the API token"
echo ""
echo "Then paste it below:"
echo ""

read -p "Enter your Buttondown API token: " API_TOKEN

# Verify token format (usually starts with specific pattern)
if [ -z "$API_TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

# Create .env file
echo "BUTTONDOWN_API_TOKEN=$API_TOKEN" > .env

echo ""
echo "✅ Token saved to .env file"
echo ""
echo "Now you can run:"
echo "  python3 buttondown_subscriber_manager.py"
echo ""
