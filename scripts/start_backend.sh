#!/bin/bash
# ===========================================
# Start Backend API Server
# ===========================================

echo "🐄 Starting AI Animal Tracking Backend..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start server
python src/main.py
