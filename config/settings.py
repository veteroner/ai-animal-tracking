"""
AI Animal Tracking System - Settings Configuration
==================================================

Merkezi konfigürasyon yönetimi için Pydantic Settings kullanılır.
Environment variables, .env dosyası ve varsayılan değerler desteklenir.
"""

import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Proje kök dizini
BASE_DIR = Path(__file__).resolve().parent.parent


class AppSettings(BaseSettings):
    """Uygulama genel ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Uygulama bilgileri
    app_name: str = Field(default="AI Animal Tracking System")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_secret_key: str = Field(default="change-this-secret-key-in-production")
    app_log_level: str = Field(default="INFO")
    
    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v.lower()


class ServerSettings(BaseSettings):
    """Sunucu ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVER_",
        extra="ignore"
    )
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    reload: bool = Field(default=True)


class DatabaseSettings(BaseSettings):
    """Veritabanı ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DATABASE_",
        extra="ignore"
    )
    
    url: str = Field(default="sqlite:///./data/animal_tracking.db")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    echo: bool = Field(default=False)


class RedisSettings(BaseSettings):
    """Redis ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="REDIS_",
        extra="ignore"
    )
    
    url: str = Field(default="redis://localhost:6379/0")
    password: Optional[str] = Field(default=None)


class StorageSettings(BaseSettings):
    """Depolama ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STORAGE_",
        extra="ignore"
    )
    
    type: str = Field(default="local")
    path: str = Field(default="./data")
    
    # Video ayarları
    video_retention_days: int = Field(default=30)
    snapshot_retention_days: int = Field(default=7)
    max_video_size_mb: int = Field(default=500)


class ModelSettings(BaseSettings):
    """AI Model ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MODEL_",
        extra="ignore"
    )
    
    device: str = Field(default="auto")
    detection: str = Field(default="yolov8n.pt")
    detection_confidence: float = Field(default=0.5)
    tracking_algorithm: str = Field(default="deepsort")
    
    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        allowed = ["auto", "cpu", "cuda", "mps"]
        if v.lower() not in allowed and not v.startswith("cuda:"):
            raise ValueError(f"device must be one of {allowed} or 'cuda:N'")
        return v.lower()


class CameraSettings(BaseSettings):
    """Kamera ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CAMERA_",
        extra="ignore"
    )
    
    default_fps: int = Field(default=30)
    default_resolution: str = Field(default="1280x720")
    max_cameras: int = Field(default=10)
    reconnect_interval: int = Field(default=5)


class NotificationSettings(BaseSettings):
    """Bildirim ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore"
    )
    
    # SMTP
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_from_email: str = Field(default="noreply@animal-tracking.local")
    smtp_use_tls: bool = Field(default=True)
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)


class SecuritySettings(BaseSettings):
    """Güvenlik ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore"
    )
    
    jwt_secret_key: str = Field(default="change-this-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)
    
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")
    cors_allow_credentials: bool = Field(default=True)
    
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=60)
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


class BehaviorSettings(BaseSettings):
    """Davranış analizi ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BEHAVIOR_",
        extra="ignore"
    )
    
    analysis_interval: float = Field(default=1.0)
    history_window: int = Field(default=300)
    feeding_zone_enabled: bool = Field(default=True)
    anomaly_detection_enabled: bool = Field(default=True)
    anomaly_threshold: float = Field(default=2.5)


class HealthSettings(BaseSettings):
    """Sağlık izleme ayarları"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HEALTH_",
        extra="ignore"
    )
    
    check_interval: int = Field(default=3600)
    bcs_estimation_enabled: bool = Field(default=True)
    lameness_detection_enabled: bool = Field(default=True)
    early_warning_enabled: bool = Field(default=True)


class Settings:
    """Tüm ayarları birleştiren ana sınıf"""
    
    def __init__(self):
        self.app = AppSettings()
        self.server = ServerSettings()
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.storage = StorageSettings()
        self.model = ModelSettings()
        self.camera = CameraSettings()
        self.notification = NotificationSettings()
        self.security = SecuritySettings()
        self.behavior = BehaviorSettings()
        self.health = HealthSettings()
        
        # Dizin yolları
        self.base_dir = BASE_DIR
        self.config_dir = BASE_DIR / "config"
        self.data_dir = BASE_DIR / "data"
        self.models_dir = BASE_DIR / "models"
        self.logs_dir = BASE_DIR / "logs"
        
        # Dizinleri oluştur
        self._create_directories()
    
    def _create_directories(self):
        """Gerekli dizinleri oluştur"""
        directories = [
            self.data_dir,
            self.data_dir / "videos",
            self.data_dir / "snapshots",
            self.data_dir / "exports",
            self.data_dir / "datasets",
            self.data_dir / "embeddings",
            self.models_dir / "pretrained",
            self.models_dir / "custom",
            self.logs_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        return self.app.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Singleton Settings instance döndürür"""
    return Settings()


# Global settings instance
settings = get_settings()
