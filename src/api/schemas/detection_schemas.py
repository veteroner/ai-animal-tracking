"""
Tespit API Şemaları
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box şeması"""
    x: float = Field(..., description="Sol üst köşe X koordinatı")
    y: float = Field(..., description="Sol üst köşe Y koordinatı")
    width: float = Field(..., gt=0, description="Genişlik")
    height: float = Field(..., gt=0, description="Yükseklik")
    
    class Config:
        json_schema_extra = {
            "example": {
                "x": 100.0,
                "y": 150.0,
                "width": 200.0,
                "height": 180.0
            }
        }


class DetectionBase(BaseModel):
    """Tespit temel şeması"""
    class_name: str = Field(..., description="Sınıf adı (cattle, sheep, vb.)")
    confidence: float = Field(..., ge=0, le=1, description="Güven skoru")
    bbox: BoundingBox = Field(..., description="Bounding box")


class DetectionCreate(DetectionBase):
    """Tespit oluşturma şeması"""
    camera_id: str = Field(..., description="Kamera ID")
    animal_id: Optional[int] = Field(None, description="İlişkili hayvan ID")
    track_id: Optional[int] = Field(None, description="Takip ID")
    frame_number: Optional[int] = Field(None, ge=0, description="Frame numarası")
    timestamp: Optional[datetime] = Field(None, description="Zaman damgası")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DetectionResponse(DetectionBase):
    """Tespit yanıt şeması"""
    id: int
    camera_id: str
    animal_id: Optional[int] = None
    track_id: Optional[int] = None
    frame_number: Optional[int] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "class_name": "cattle",
                "confidence": 0.95,
                "bbox": {
                    "x": 100.0,
                    "y": 150.0,
                    "width": 200.0,
                    "height": 180.0
                },
                "camera_id": "cam-001",
                "animal_id": 1,
                "track_id": 42,
                "frame_number": 1500,
                "timestamp": "2025-12-06T10:30:00"
            }
        }


class DetectionListResponse(BaseModel):
    """Tespit listesi yanıt şeması"""
    items: List[DetectionResponse]
    total: int
    page: int = 1
    page_size: int = 100


class DetectionStatistics(BaseModel):
    """Tespit istatistikleri şeması"""
    total_detections: int = 0
    average_confidence: float = 0.0
    unique_animals: int = 0
    by_class: Dict[str, int] = Field(default_factory=dict)
    by_camera: Dict[str, int] = Field(default_factory=dict)
    hourly_distribution: Dict[int, int] = Field(default_factory=dict)
    period_hours: int = 24


class TrackInfo(BaseModel):
    """Takip bilgisi şeması"""
    track_id: int
    animal_id: Optional[int] = None
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox
    velocity: Optional[Dict[str, float]] = None  # {"x": 0.0, "y": 0.0}
    age: int = 0  # Frame sayısı olarak yaş
    hits: int = 0  # Başarılı eşleşme sayısı
    time_since_update: int = 0


class FrameDetections(BaseModel):
    """Frame tespitleri şeması"""
    frame_number: int
    timestamp: datetime
    camera_id: str
    detections: List[DetectionResponse]
    tracks: List[TrackInfo] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class DetectionFilter(BaseModel):
    """Tespit filtreleme şeması"""
    camera_ids: Optional[List[str]] = None
    animal_ids: Optional[List[int]] = None
    class_names: Optional[List[str]] = None
    min_confidence: float = Field(default=0.0, ge=0, le=1)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class RealTimeDetection(BaseModel):
    """Gerçek zamanlı tespit şeması (WebSocket için)"""
    type: str = "detection"
    camera_id: str
    frame_number: int
    timestamp: datetime
    detections: List[Dict[str, Any]]
    fps: float = 0.0
    latency_ms: float = 0.0
