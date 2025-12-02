#!/bin/bash
# ===========================================
# AI Animal Tracking System - Model Download Script
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/models/pretrained"

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Animal Tracking - Model Download${NC}"
echo -e "${GREEN}========================================${NC}"

# Modeller dizinini oluştur
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo -e "\n${YELLOW}Downloading YOLO models...${NC}\n"

# YOLO modellerini Python ile indir
python3 << 'EOF'
import os
from pathlib import Path

try:
    from ultralytics import YOLO
    
    models = [
        "yolov8n.pt",  # Nano - En hızlı
        "yolov8s.pt",  # Small - Dengeli
    ]
    
    models_dir = Path(".")
    
    for model_name in models:
        model_path = models_dir / model_name
        
        if model_path.exists():
            print(f"✓ {model_name} already exists")
        else:
            print(f"⬇ Downloading {model_name}...")
            model = YOLO(model_name)
            print(f"✓ {model_name} downloaded")
    
    print("\n✅ All YOLO models downloaded successfully!")
    
except ImportError:
    print("❌ ultralytics package not installed.")
    print("Please run: pip install ultralytics")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Download complete!${NC}"
echo -e "${GREEN}Models saved to: $MODELS_DIR${NC}"
echo -e "${GREEN}========================================${NC}"
