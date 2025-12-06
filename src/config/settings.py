"""
Merkezi Ayarlar Yöneticisi

Uygulama genelinde kullanılacak ayarları yönetir.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import json
import os
from enum import Enum


class LogLevel(Enum):
    """Log seviyesi"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Veritabanı yapılandırması"""
    host: str = "localhost"
    port: int = 5432
    database: str = "animal_tracking"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    
    @property
    def connection_string(self) -> str:
        """PostgreSQL connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis yapılandırması"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50


@dataclass
class ModelConfig:
    """AI Model yapılandırması"""
    detection_model: str = "yolov8n.pt"
    detection_confidence: float = 0.5
    reid_similarity_threshold: float = 0.92
    reid_feature_update_alpha: float = 0.02
    max_age: int = 30
    min_hits: int = 3
    iou_threshold: float = 0.3


@dataclass
class VideoConfig:
    """Video işleme yapılandırması"""
    input_width: int = 1280
    input_height: int = 720
    fps: int = 30
    video_codec: str = "h264"
    save_processed_video: bool = True
    output_path: str = "output/videos"


@dataclass
class APIConfig:
    """API yapılandırması"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list = field(default_factory=lambda: ["*"])
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    rate_limit_per_minute: int = 60


@dataclass
class StorageConfig:
    """Depolama yapılandırması"""
    data_path: str = "data"
    video_retention_days: int = 30
    image_retention_days: int = 7
    log_retention_days: int = 90
    max_storage_gb: int = 100


@dataclass
class NotificationConfig:
    """Bildirim yapılandırması"""
    enabled: bool = True
    apns_key_file: Optional[str] = None
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    fcm_project_id: Optional[str] = None
    fcm_service_account: Optional[str] = None


@dataclass
class MonitoringConfig:
    """İzleme yapılandırması"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 60
    log_level: LogLevel = LogLevel.INFO


class Settings:
    """Merkezi ayarlar sınıfı"""
    
    _instance: Optional['Settings'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.environment = os.getenv("ENVIRONMENT", "development")
            
            # Alt yapılandırmalar
            self.database = DatabaseConfig()
            self.redis = RedisConfig()
            self.model = ModelConfig()
            self.video = VideoConfig()
            self.api = APIConfig()
            self.storage = StorageConfig()
            self.notification = NotificationConfig()
            self.monitoring = MonitoringConfig()
            
            # Genel ayarlar
            self.app_name = "Animal Tracking System"
            self.version = "1.0.0"
            self.debug = self.environment == "development"
            self.timezone = "Europe/Istanbul"
            
            # Özel ayarlar
            self.custom_settings: Dict[str, Any] = {}
            
            # Ayarları yükle
            self._load_from_env()
            self._load_from_file()
    
    def _load_from_env(self):
        """Ortam değişkenlerinden yükle"""
        # Database
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", self.database.port))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)
        
        # Redis
        self.redis.host = os.getenv("REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("REDIS_PORT", self.redis.port))
        self.redis.password = os.getenv("REDIS_PASSWORD", self.redis.password)
        
        # API
        self.api.host = os.getenv("API_HOST", self.api.host)
        self.api.port = int(os.getenv("API_PORT", self.api.port))
        
        # Model
        self.model.detection_model = os.getenv("DETECTION_MODEL", self.model.detection_model)
        
        # Notifications
        self.notification.apns_key_file = os.getenv("APNS_KEY_FILE")
        self.notification.apns_key_id = os.getenv("APNS_KEY_ID")
        self.notification.apns_team_id = os.getenv("APNS_TEAM_ID")
        self.notification.fcm_project_id = os.getenv("FCM_PROJECT_ID")
        self.notification.fcm_service_account = os.getenv("FCM_SERVICE_ACCOUNT")
    
    def _load_from_file(self, config_file: Optional[str] = None):
        """Dosyadan yapılandırma yükle"""
        if config_file is None:
            config_file = os.getenv("CONFIG_FILE", "config/settings.json")
        
        config_path = Path(config_file)
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Yapılandırmaları uygula
            self._apply_config(config_data)
        except Exception as e:
            print(f"Yapılandırma yükleme hatası: {e}")
    
    def _apply_config(self, config_data: Dict[str, Any]):
        """Yapılandırma verilerini uygula"""
        # Database
        if "database" in config_data:
            db_config = config_data["database"]
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        # Redis
        if "redis" in config_data:
            redis_config = config_data["redis"]
            for key, value in redis_config.items():
                if hasattr(self.redis, key):
                    setattr(self.redis, key, value)
        
        # Model
        if "model" in config_data:
            model_config = config_data["model"]
            for key, value in model_config.items():
                if hasattr(self.model, key):
                    setattr(self.model, key, value)
        
        # Video
        if "video" in config_data:
            video_config = config_data["video"]
            for key, value in video_config.items():
                if hasattr(self.video, key):
                    setattr(self.video, key, value)
        
        # API
        if "api" in config_data:
            api_config = config_data["api"]
            for key, value in api_config.items():
                if hasattr(self.api, key):
                    setattr(self.api, key, value)
        
        # Custom settings
        if "custom" in config_data:
            self.custom_settings.update(config_data["custom"])
    
    def save_to_file(self, config_file: str = "config/settings.json"):
        """Ayarları dosyaya kaydet"""
        config_data = {
            "environment": self.environment,
            "app_name": self.app_name,
            "version": self.version,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "pool_size": self.database.pool_size
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db
            },
            "model": {
                "detection_model": self.model.detection_model,
                "detection_confidence": self.model.detection_confidence,
                "reid_similarity_threshold": self.model.reid_similarity_threshold,
                "reid_feature_update_alpha": self.model.reid_feature_update_alpha
            },
            "video": {
                "input_width": self.video.input_width,
                "input_height": self.video.input_height,
                "fps": self.video.fps,
                "save_processed_video": self.video.save_processed_video,
                "output_path": self.video.output_path
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "cors_origins": self.api.cors_origins,
                "rate_limit_per_minute": self.api.rate_limit_per_minute
            },
            "storage": {
                "data_path": self.storage.data_path,
                "video_retention_days": self.storage.video_retention_days,
                "image_retention_days": self.storage.image_retention_days
            },
            "custom": self.custom_settings
        }
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Özel ayarı al"""
        return self.custom_settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Özel ayar belirle"""
        self.custom_settings[key] = value
    
    def update(self, settings_dict: Dict[str, Any]):
        """Toplu ayar güncelleme"""
        self.custom_settings.update(settings_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Tüm ayarları dict'e çevir"""
        return {
            "environment": self.environment,
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port
            },
            "model": {
                "detection_model": self.model.detection_model,
                "detection_confidence": self.model.detection_confidence,
                "reid_similarity_threshold": self.model.reid_similarity_threshold
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port
            },
            "custom": self.custom_settings
        }
    
    def __repr__(self) -> str:
        return f"Settings(environment={self.environment}, debug={self.debug})"


# Singleton instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Ayarlar instance'ını al"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings():
    """Ayarları yeniden yükle"""
    global _settings_instance
    _settings_instance = None
    return get_settings()
