"""
Pytest konfigürasyonu.

Bu dosya pytest'in projenin root dizinini Python path'e eklemesini sağlar.
"""
import sys
from pathlib import Path

# Proje root'unu Python path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
