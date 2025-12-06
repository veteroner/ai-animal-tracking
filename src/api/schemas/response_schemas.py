"""
Genel Yanıt Şemaları
"""

from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class BaseResponse(BaseModel):
    """Temel yanıt şeması"""
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseResponse):
    """Başarılı yanıt şeması"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "İşlem başarıyla tamamlandı",
                "timestamp": "2025-12-06T10:30:00",
                "data": {"id": 1}
            }
        }


class ErrorResponse(BaseResponse):
    """Hata yanıt şeması"""
    success: bool = False
    error_code: str = "UNKNOWN_ERROR"
    error_details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Bir hata oluştu",
                "timestamp": "2025-12-06T10:30:00",
                "error_code": "NOT_FOUND",
                "error_details": {"resource": "animal", "id": 999}
            }
        }


class PaginatedResponse(BaseModel):
    """Sayfalanmış yanıt şeması"""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }


class HealthCheckResponse(BaseModel):
    """Sistem sağlık kontrolü yanıtı"""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    services: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "detector": "healthy"
                },
                "timestamp": "2025-12-06T10:30:00"
            }
        }


class SystemStatusResponse(BaseModel):
    """Sistem durum yanıtı"""
    status: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    gpu_available: bool = False
    gpu_memory_percent: Optional[float] = None
    active_cameras: int = 0
    active_tracks: int = 0
    detections_per_second: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AlertResponse(BaseModel):
    """Uyarı yanıt şeması"""
    id: str
    title: str
    message: str
    severity: str = "info"  # info, warning, error, critical
    animal_id: Optional[int] = None
    camera_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertListResponse(BaseModel):
    """Uyarı listesi yanıtı"""
    items: List[AlertResponse]
    total: int
    unread_count: int = 0


class CameraStatusResponse(BaseModel):
    """Kamera durum yanıtı"""
    camera_id: str
    name: str
    status: str = "offline"  # online, offline, error
    fps: float = 0.0
    resolution: Optional[str] = None
    last_frame_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CameraListResponse(BaseModel):
    """Kamera listesi yanıtı"""
    items: List[CameraStatusResponse]
    total: int
    online_count: int = 0


class ExportResponse(BaseModel):
    """Dışa aktarma yanıtı"""
    export_id: str
    status: str = "pending"  # pending, processing, completed, failed
    format: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket mesaj şeması"""
    type: str  # detection, alert, status, error
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchOperationResponse(BaseModel):
    """Toplu işlem yanıtı"""
    success: bool
    total_items: int
    processed_items: int
    failed_items: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    duration_seconds: float = 0.0
