#!/bin/bash
# ===========================================
# Start All Services (Backend + Frontend)
# ===========================================

echo "🚀 Starting AI Animal Tracking System..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Start backend in background
echo "🐄 Starting Backend API..."
./scripts/start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend in background
echo "🌐 Starting Frontend..."
./scripts/start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "====================================="
echo "✅ All services started!"
echo ""
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Frontend:     http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo "====================================="

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
