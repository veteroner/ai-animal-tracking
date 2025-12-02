# src/core/config.py
"""
Configuration module for AI Animal Tracking System.

Uses pydantic-settings for environment-based configuration.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "AI Animal Tracking System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENV: str = "development"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    API_RELOAD: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///data/tracking.db"
    DATABASE_ECHO: bool = False
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    # Detection
    DETECTION_MODEL: str = "yolov8n.pt"
    DETECTION_CONFIDENCE: float = 0.5
    DETECTION_IOU: float = 0.45
    DETECTION_DEVICE: str = "auto"
    
    # Tracking
    TRACKING_MAX_AGE: int = 30
    TRACKING_MIN_HITS: int = 3
    TRACKING_IOU_THRESHOLD: float = 0.3
    
    # Camera
    CAMERA_DEFAULT_FPS: int = 30
    CAMERA_BUFFER_SIZE: int = 30
    CAMERA_RECONNECT_DELAY: int = 5
    
    # Alert
    ALERT_COOLDOWN: int = 300
    ALERT_HEALTH_CRITICAL: float = 30.0
    ALERT_HEALTH_WARNING: float = 60.0
    
    # Storage
    DATA_DIR: str = "data"
    LOGS_DIR: str = "logs"
    MODELS_DIR: str = "models"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings


def configure_logging():
    """Configure logging based on settings."""
    import logging
    import colorlog
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]
    
    # Suppress noisy loggers
    logging.getLogger('ultralytics').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
