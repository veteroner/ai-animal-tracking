#!/bin/bash
# ===========================================
# AI Animal Tracking System - Environment Setup
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Animal Tracking System Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Python version kontrolü
echo -e "\n${BLUE}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Virtual environment oluştur
echo -e "\n${BLUE}Creating virtual environment...${NC}"
cd "$PROJECT_ROOT"

if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Pip upgrade
echo -e "\n${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Bağımlılıkları yükle
echo -e "\n${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Dev dependencies (opsiyonel)
read -p "Install development dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install -r requirements-dev.txt
    echo -e "${GREEN}✓ Development dependencies installed${NC}"
fi

# Dizinleri oluştur
echo -e "\n${BLUE}Creating directories...${NC}"
mkdir -p data/{videos,snapshots,exports,datasets/images,datasets/labels,embeddings}
mkdir -p models/{pretrained,custom,configs}
mkdir -p logs
mkdir -p web/frontend

# .gitkeep dosyaları ekle
touch data/videos/.gitkeep
touch data/snapshots/.gitkeep
touch data/exports/.gitkeep
touch data/datasets/images/.gitkeep
touch data/datasets/labels/.gitkeep
touch data/embeddings/.gitkeep
touch models/pretrained/.gitkeep
touch models/custom/.gitkeep
touch logs/.gitkeep

echo -e "${GREEN}✓ Directories created${NC}"

# .env dosyası
echo -e "\n${BLUE}Setting up environment file...${NC}"
if [ -f ".env" ]; then
    echo -e "${YELLOW}.env file already exists. Skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from .env.example${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file with your settings${NC}"
fi

# Modelleri indir
echo -e "\n${BLUE}Downloading AI models...${NC}"
read -p "Download YOLO models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/download_models.py
fi

# Test
echo -e "\n${BLUE}Running quick test...${NC}"
python -c "
import sys
print(f'Python: {sys.version}')

try:
    import cv2
    print(f'OpenCV: {cv2.__version__}')
except ImportError:
    print('OpenCV: Not installed')

try:
    import torch
    print(f'PyTorch: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if hasattr(torch.backends, 'mps'):
        print(f'MPS available: {torch.backends.mps.is_available()}')
except ImportError:
    print('PyTorch: Not installed')

try:
    from ultralytics import YOLO
    print('Ultralytics: Installed')
except ImportError:
    print('Ultralytics: Not installed')

try:
    import fastapi
    print(f'FastAPI: {fastapi.__version__}')
except ImportError:
    print('FastAPI: Not installed')
"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Edit .env file with your settings"
echo -e "2. Activate virtual environment: source venv/bin/activate"
echo -e "3. Run the application: python src/main.py --camera 0"
echo -e "\n${BLUE}For help: python src/main.py --help${NC}"
