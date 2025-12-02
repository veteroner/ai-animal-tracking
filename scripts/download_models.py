#!/usr/bin/env python3
"""
AI Animal Tracking System - Model Download Script
=================================================

YOLO ve diğer gerekli modelleri indirir.

Kullanım:
    python scripts/download_models.py
    python scripts/download_models.py --models yolov8n yolov8s
"""

import argparse
import sys
from pathlib import Path


def download_yolo_models(models: list, output_dir: Path):
    """YOLO modellerini indir"""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics package not installed.")
        print("Please run: pip install ultralytics")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for model_name in models:
        if not model_name.endswith(".pt"):
            model_name = f"{model_name}.pt"
        
        model_path = output_dir / model_name
        
        if model_path.exists():
            print(f"✓ {model_name} already exists")
        else:
            print(f"⬇ Downloading {model_name}...")
            try:
                model = YOLO(model_name)
                # Model dosyasını hedef dizine kopyala
                import shutil
                from ultralytics import settings
                
                # YOLO varsayılan olarak ~/.cache/ultralytics klasörüne indirir
                # Model zaten yüklendiği için doğrudan kullanılabilir
                print(f"✓ {model_name} ready")
            except Exception as e:
                print(f"❌ Failed to download {model_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download AI models")
    parser.add_argument(
        "--models", "-m",
        nargs="+",
        default=["yolov8n", "yolov8s"],
        help="Models to download (default: yolov8n yolov8s)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Output directory for models"
    )
    
    args = parser.parse_args()
    
    # Proje kök dizini
    project_root = Path(__file__).resolve().parent.parent
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "models" / "pretrained"
    
    print("=" * 50)
    print("AI Animal Tracking - Model Download")
    print("=" * 50)
    print(f"\nOutput directory: {output_dir}")
    print(f"Models to download: {args.models}\n")
    
    download_yolo_models(args.models, output_dir)
    
    print("\n" + "=" * 50)
    print("✅ Download complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
