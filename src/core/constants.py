"""
AI Animal Tracking System - Constants
=====================================

Sistem genelinde kullanılan sabitler.
"""

from enum import Enum, auto
from typing import Dict, List, Tuple


# ===========================================
# Video ve Görüntü Formatları
# ===========================================

SUPPORTED_VIDEO_FORMATS: Tuple[str, ...] = (
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"
)

SUPPORTED_IMAGE_FORMATS: Tuple[str, ...] = (
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"
)

VIDEO_CODECS: Dict[str, str] = {
    "h264": "avc1",
    "h265": "hvc1",
    "xvid": "XVID",
    "mjpeg": "MJPG",
}


# ===========================================
# COCO Dataset Sınıfları (Hayvanlar)
# ===========================================

COCO_ANIMAL_CLASSES: Dict[int, str] = {
    14: "bird",      # kuş
    15: "cat",       # kedi
    16: "dog",       # köpek
    17: "horse",     # at
    18: "sheep",     # koyun
    19: "cow",       # inek
    20: "elephant",  # fil
    21: "bear",      # ayı
    22: "zebra",     # zebra
    23: "giraffe",   # zürafa
}

# Türkçe karşılıklar
ANIMAL_NAMES_TR: Dict[str, str] = {
    "bird": "Kuş",
    "cat": "Kedi",
    "dog": "Köpek",
    "horse": "At",
    "sheep": "Koyun",
    "cow": "İnek",
    "elephant": "Fil",
    "bear": "Ayı",
    "zebra": "Zebra",
    "giraffe": "Zürafa",
}

# Çiftlik hayvanları (öncelikli)
FARM_ANIMAL_CLASSES: List[int] = [17, 18, 19]  # horse, sheep, cow


# ===========================================
# Davranış Türleri
# ===========================================

class BehaviorType(Enum):
    """Hayvan davranış türleri"""
    UNKNOWN = auto()
    EATING = auto()
    DRINKING = auto()
    WALKING = auto()
    RUNNING = auto()
    STANDING = auto()
    LYING = auto()
    SLEEPING = auto()
    GROOMING = auto()
    SOCIAL = auto()


BEHAVIOR_TYPES: Dict[str, str] = {
    "unknown": "Bilinmeyen",
    "eating": "Yeme",
    "drinking": "Su İçme",
    "walking": "Yürüme",
    "running": "Koşma",
    "standing": "Ayakta Durma",
    "lying": "Yatma",
    "sleeping": "Uyuma",
    "grooming": "Tımar",
    "social": "Sosyal Etkileşim",
}


# ===========================================
# Sağlık Durumları
# ===========================================

class HealthStatus(Enum):
    """Hayvan sağlık durumları"""
    UNKNOWN = auto()
    HEALTHY = auto()
    MINOR_ISSUE = auto()
    MODERATE_ISSUE = auto()
    SEVERE_ISSUE = auto()
    CRITICAL = auto()


HEALTH_STATUS: Dict[str, str] = {
    "unknown": "Bilinmeyen",
    "healthy": "Sağlıklı",
    "minor_issue": "Hafif Sorun",
    "moderate_issue": "Orta Sorun",
    "severe_issue": "Ciddi Sorun",
    "critical": "Kritik",
}

# Vücut Kondisyon Skoru (BCS)
BCS_RANGES: Dict[str, Tuple[float, float]] = {
    "emaciated": (1.0, 1.5),    # Çok zayıf
    "thin": (1.5, 2.5),          # Zayıf
    "ideal": (2.5, 3.5),         # İdeal
    "overweight": (3.5, 4.5),    # Kilolu
    "obese": (4.5, 5.0),         # Obez
}


# ===========================================
# Kamera Ayarları
# ===========================================

class CameraType(Enum):
    """Kamera türleri"""
    USB = "usb"
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"


DEFAULT_RESOLUTIONS: Dict[str, Tuple[int, int]] = {
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
}

DEFAULT_FPS_OPTIONS: List[int] = [10, 15, 20, 25, 30, 60]


# ===========================================
# Takip Algoritmaları
# ===========================================

class TrackingAlgorithm(Enum):
    """Takip algoritmaları"""
    SORT = "sort"
    DEEPSORT = "deepsort"
    BYTETRACK = "bytetrack"


# Track durumları
class TrackState(Enum):
    """Track durumları"""
    TENTATIVE = auto()    # Geçici
    CONFIRMED = auto()     # Onaylanmış
    DELETED = auto()       # Silinmiş


# ===========================================
# Bölge Türleri
# ===========================================

class ZoneType(Enum):
    """Bölge türleri"""
    FEEDING = "feeding"
    DRINKING = "drinking"
    RESTING = "resting"
    WALKING = "walking"
    MILKING = "milking"
    CUSTOM = "custom"


ZONE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "feeding": (0, 255, 0),    # Yeşil
    "drinking": (255, 0, 0),   # Mavi (BGR)
    "resting": (0, 165, 255),  # Turuncu
    "walking": (255, 255, 0),  # Cyan
    "milking": (255, 0, 255),  # Magenta
    "custom": (128, 128, 128), # Gri
}


# ===========================================
# Bildirim Türleri
# ===========================================

class NotificationType(Enum):
    """Bildirim türleri"""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Bildirim kanalları"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


# ===========================================
# API ve HTTP
# ===========================================

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

HTTP_STATUS_CODES: Dict[str, int] = {
    "ok": 200,
    "created": 201,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "internal_error": 500,
}


# ===========================================
# Görselleştirme
# ===========================================

# Renk paleti (BGR formatında)
VISUALIZATION_COLORS: List[Tuple[int, int, int]] = [
    (255, 0, 0),      # Mavi
    (0, 255, 0),      # Yeşil
    (0, 0, 255),      # Kırmızı
    (255, 255, 0),    # Cyan
    (255, 0, 255),    # Magenta
    (0, 255, 255),    # Sarı
    (128, 0, 0),      # Koyu Mavi
    (0, 128, 0),      # Koyu Yeşil
    (0, 0, 128),      # Koyu Kırmızı
    (128, 128, 0),    # Teal
    (128, 0, 128),    # Mor
    (0, 128, 128),    # Olive
    (255, 128, 0),    # Açık Mavi
    (128, 255, 0),    # Açık Yeşil
    (0, 128, 255),    # Turuncu
]

# Font ayarları
FONT_SCALE = 0.6
FONT_THICKNESS = 2
BOX_THICKNESS = 2


# ===========================================
# Zaman Sabitleri
# ===========================================

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400

# Varsayılan saklama süreleri (gün)
DEFAULT_VIDEO_RETENTION_DAYS = 30
DEFAULT_SNAPSHOT_RETENTION_DAYS = 7
DEFAULT_LOG_RETENTION_DAYS = 90
