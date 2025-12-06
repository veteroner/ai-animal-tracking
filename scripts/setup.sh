#!/bin/bash
# ===========================================
# AI Animal Tracking System - Full Setup Script
# ===========================================

set -e

echo "🐄 AI Animal Tracking System - Setup"
echo "====================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${BLUE}📦 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "\n${BLUE}🔧 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "\n${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip --quiet

# Install requirements
echo -e "\n${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet

# Create necessary directories
echo -e "\n${BLUE}📁 Creating directories...${NC}"
mkdir -p data/{datasets/images,datasets/labels,embeddings,exports,gallery,snapshots,videos}
mkdir -p logs
mkdir -p models/{pretrained,custom}
mkdir -p recordings
mkdir -p reports

# Download YOLO model if not exists
if [ ! -f "yolov8n.pt" ]; then
    echo -e "\n${BLUE}🤖 Downloading YOLO model...${NC}"
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}📝 Creating .env file from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    fi
fi

# Initialize database
echo -e "\n${BLUE}💾 Initializing database...${NC}"
python3 -c "
from src.database.connection import init_db
init_db()
print('Database initialized successfully!')
" 2>/dev/null || echo "Database will be initialized on first run"

# Check if frontend exists and setup
if [ -d "frontend" ]; then
    echo -e "\n${BLUE}🌐 Setting up Frontend...${NC}"
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        if command -v npm &> /dev/null; then
            npm install --silent
            echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
        else
            echo -e "${YELLOW}⚠️  npm not found. Install Node.js to use frontend.${NC}"
        fi
    else
        echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
    fi
    
    cd ..
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo ""
echo "====================================="
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Start Backend API:"
echo "   python src/main.py"
echo ""
echo "2. Start Frontend (in another terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Test with webcam:"
echo "   python src/live_tracking.py --camera 0"
echo ""
echo "4. Open API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "5. Open Frontend:"
echo "   http://localhost:3000"
echo "====================================="
