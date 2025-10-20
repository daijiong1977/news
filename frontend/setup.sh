#!/bin/bash

# News Frontend Setup Script
# This script sets up the React frontend and installs all dependencies

echo "🚀 Setting up News Reader React Frontend..."

cd "$(dirname "$0")"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. cd frontend"
    echo "   2. npm start"
    echo ""
    echo "🌐 Development server will start at http://localhost:3000"
    echo ""
    echo "📚 For more info, see README.md"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
