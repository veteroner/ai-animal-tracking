#!/bin/bash
# ===========================================
# Start Frontend Development Server
# ===========================================

echo "🌐 Starting AI Animal Tracking Frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start development server
npm run dev
