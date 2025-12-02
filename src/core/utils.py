"""
AI Animal Tracking System - Utility Functions
=============================================

Genel yardımcı fonksiyonlar.
"""

import os
import sys
import logging
import logging.config
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps

import yaml
import numpy as np


# ===========================================
# Logging
# ===========================================

def setup_logging(
    config_path: Optional[str] = None,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Logging sistemini yapılandırır.
    
    Args:
        config_path: Logging config dosya yolu (YAML)
        log_level: Varsayılan log seviyesi
        
    Returns:
        Root logger
    """
    # Log dizinini oluştur
    log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Varsayılan konfigürasyon
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            ]
        )
    
    return logging.getLogger("animal_tracking")


def get_logger(name: str) -> logging.Logger:
    """
    İsimlendirilmiş logger döndürür.
    
    Args:
        name: Logger ismi
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"animal_tracking.{name}")


# ===========================================
# Device Selection
# ===========================================

def get_device(preferred: str = "auto") -> str:
    """
    En uygun işlem cihazını belirler.
    
    Args:
        preferred: Tercih edilen cihaz (auto, cpu, cuda, mps)
        
    Returns:
        Cihaz string'i
    """
    import torch
    
    if preferred == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    elif preferred.startswith("cuda"):
        if torch.cuda.is_available():
            return preferred
        else:
            logging.warning("CUDA not available, falling back to CPU")
            return "cpu"
    elif preferred == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            logging.warning("MPS not available, falling back to CPU")
            return "cpu"
    else:
        return "cpu"


# ===========================================
# Configuration
# ===========================================

def load_yaml_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    YAML konfigürasyon dosyasını yükler.
    
    Args:
        config_path: Config dosya yolu
        
    Returns:
        Config dictionary
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config or {}


def save_yaml_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    YAML konfigürasyon dosyasını kaydeder.
    
    Args:
        config: Config dictionary
        config_path: Hedef dosya yolu
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


# ===========================================
# Image/Video Processing
# ===========================================

def resize_frame(
    frame: np.ndarray,
    target_size: Tuple[int, int],
    keep_aspect_ratio: bool = True
) -> np.ndarray:
    """
    Frame'i yeniden boyutlandırır.
    
    Args:
        frame: Input frame
        target_size: (width, height)
        keep_aspect_ratio: Oranı koru
        
    Returns:
        Yeniden boyutlandırılmış frame
    """
    import cv2
    
    if not keep_aspect_ratio:
        return cv2.resize(frame, target_size)
    
    h, w = frame.shape[:2]
    target_w, target_h = target_size
    
    # Aspect ratio hesapla
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(frame, (new_w, new_h))
    
    # Padding ekle
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    
    return canvas


def letterbox(
    img: np.ndarray,
    new_shape: Union[int, Tuple[int, int]] = 640,
    color: Tuple[int, int, int] = (114, 114, 114),
    auto: bool = True,
    scale_fill: bool = False,
    scaleup: bool = True,
    stride: int = 32
) -> Tuple[np.ndarray, Tuple[float, float], Tuple[int, int]]:
    """
    YOLO için letterbox dönüşümü.
    
    Args:
        img: Input görüntü
        new_shape: Hedef boyut
        color: Padding rengi
        auto: Minimum dikdörtgen
        scale_fill: Stretch to fit
        scaleup: Büyütmeye izin ver
        stride: Stride değeri
        
    Returns:
        (processed_img, ratio, padding)
    """
    import cv2
    
    shape = img.shape[:2]  # [height, width]
    
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    
    # Scale ratio
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)
    
    # Compute padding
    ratio = r, r
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    
    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)
    elif scale_fill:
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]
    
    dw /= 2
    dh /= 2
    
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(
        img, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=color
    )
    
    return img, ratio, (int(dw), int(dh))


# ===========================================
# Bounding Box Utilities
# ===========================================

def xyxy_to_xywh(bbox: np.ndarray) -> np.ndarray:
    """
    Bounding box'ı [x1, y1, x2, y2] -> [x_center, y_center, w, h] formatına çevirir.
    """
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    x_center = x1 + w / 2
    y_center = y1 + h / 2
    return np.array([x_center, y_center, w, h])


def xywh_to_xyxy(bbox: np.ndarray) -> np.ndarray:
    """
    Bounding box'ı [x_center, y_center, w, h] -> [x1, y1, x2, y2] formatına çevirir.
    """
    x_center, y_center, w, h = bbox
    x1 = x_center - w / 2
    y1 = y_center - h / 2
    x2 = x_center + w / 2
    y2 = y_center + h / 2
    return np.array([x1, y1, x2, y2])


def calculate_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """
    İki bounding box arasındaki IoU (Intersection over Union) hesaplar.
    
    Args:
        box1, box2: [x1, y1, x2, y2] formatında
        
    Returns:
        IoU değeri [0, 1]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def get_box_center(bbox: np.ndarray) -> Tuple[float, float]:
    """
    Bounding box'ın merkez noktasını döndürür.
    
    Args:
        bbox: [x1, y1, x2, y2] formatında
        
    Returns:
        (x_center, y_center)
    """
    return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2


def get_box_area(bbox: np.ndarray) -> float:
    """
    Bounding box'ın alanını hesaplar.
    
    Args:
        bbox: [x1, y1, x2, y2] formatında
        
    Returns:
        Alan değeri
    """
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


# ===========================================
# Time Utilities
# ===========================================

def get_timestamp() -> str:
    """ISO format timestamp döndürür."""
    return datetime.now().isoformat()


def get_timestamp_filename() -> str:
    """Dosya ismi için uygun timestamp döndürür."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def format_duration(seconds: float) -> str:
    """
    Süreyi okunabilir formatta döndürür.
    
    Args:
        seconds: Saniye cinsinden süre
        
    Returns:
        Formatlanmış string (örn: "2h 30m 15s")
    """
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if td.days:
        parts.append(f"{td.days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


# ===========================================
# Performance Utilities
# ===========================================

class FPSCounter:
    """FPS sayacı"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps: List[float] = []
    
    def update(self) -> float:
        """Yeni frame için güncelle ve FPS döndür."""
        now = time.time()
        self.timestamps.append(now)
        
        # Pencere dışındakileri kaldır
        while len(self.timestamps) > self.window_size:
            self.timestamps.pop(0)
        
        if len(self.timestamps) < 2:
            return 0.0
        
        elapsed = self.timestamps[-1] - self.timestamps[0]
        return (len(self.timestamps) - 1) / elapsed if elapsed > 0 else 0.0
    
    def reset(self):
        """Sayacı sıfırla."""
        self.timestamps.clear()


class Timer:
    """Zamanlayıcı context manager"""
    
    def __init__(self, name: str = "Timer"):
        self.name = name
        self.start_time = None
        self.elapsed = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start_time
    
    def __str__(self):
        return f"{self.name}: {self.elapsed*1000:.2f}ms"


def timing_decorator(func):
    """Fonksiyon süresini ölçen decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.debug(f"{func.__name__} took {elapsed*1000:.2f}ms")
        return result
    return wrapper


# ===========================================
# File Utilities
# ===========================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Dizinin var olduğundan emin ol, yoksa oluştur.
    
    Args:
        path: Dizin yolu
        
    Returns:
        Path objesi
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(path: Union[str, Path]) -> int:
    """Dosya boyutunu byte olarak döndürür."""
    return Path(path).stat().st_size


def get_file_size_str(path: Union[str, Path]) -> str:
    """Dosya boyutunu okunabilir formatta döndürür."""
    size = get_file_size(path)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def cleanup_old_files(
    directory: Union[str, Path],
    max_age_days: int,
    extensions: Optional[Tuple[str, ...]] = None
) -> int:
    """
    Belirli süreyi geçmiş dosyaları siler.
    
    Args:
        directory: Hedef dizin
        max_age_days: Maksimum yaş (gün)
        extensions: Filtrelenecek uzantılar (None = hepsi)
        
    Returns:
        Silinen dosya sayısı
    """
    directory = Path(directory)
    if not directory.exists():
        return 0
    
    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted = 0
    
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        
        if extensions and file_path.suffix.lower() not in extensions:
            continue
        
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if mtime < cutoff:
            file_path.unlink()
            deleted += 1
    
    return deleted


# ===========================================
# Geometry Utilities
# ===========================================

def point_in_polygon(
    point: Tuple[float, float],
    polygon: List[Tuple[float, float]]
) -> bool:
    """
    Noktanın polygon içinde olup olmadığını kontrol eder.
    Ray casting algoritması kullanır.
    
    Args:
        point: (x, y) koordinatları
        polygon: Köşe noktaları listesi [(x1,y1), (x2,y2), ...]
        
    Returns:
        İçeride ise True
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        
        j = i
    
    return inside


def calculate_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> float:
    """
    İki nokta arasındaki Euclidean mesafeyi hesaplar.
    """
    return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)


# ===========================================
# Color Utilities
# ===========================================

def get_color_by_id(object_id: int, palette: Optional[List[Tuple[int, int, int]]] = None) -> Tuple[int, int, int]:
    """
    ID'ye göre tutarlı renk döndürür.
    
    Args:
        object_id: Nesne ID'si
        palette: Renk paleti (BGR)
        
    Returns:
        BGR renk tuple'ı
    """
    from src.core.constants import VISUALIZATION_COLORS
    
    if palette is None:
        palette = VISUALIZATION_COLORS
    
    return palette[object_id % len(palette)]


def bgr_to_rgb(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """BGR'dan RGB'ye çevir."""
    return (color[2], color[1], color[0])


def rgb_to_bgr(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """RGB'den BGR'ye çevir."""
    return (color[2], color[1], color[0])
