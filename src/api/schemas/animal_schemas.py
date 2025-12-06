"""
Hayvan API Şemaları
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class AnimalBase(BaseModel):
    """Hayvan temel şeması"""
    name: Optional[str] = Field(None, description="Hayvan adı")
    species: str = Field(..., description="Tür (cattle, sheep, goat, vb.)")
    breed: Optional[str] = Field(None, description="Irk")
    birth_date: Optional[date] = Field(None, description="Doğum tarihi")
    gender: Optional[str] = Field(None, description="Cinsiyet (male/female)")
    color: Optional[str] = Field(None, description="Renk")
    weight: Optional[float] = Field(None, ge=0, description="Ağırlık (kg)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sarıkız",
                "species": "cattle",
                "breed": "Holstein",
                "birth_date": "2022-03-15",
                "gender": "female",
                "color": "black-white",
                "weight": 450.5
            }
        }


class AnimalCreate(AnimalBase):
    """Hayvan oluşturma şeması"""
    external_id: Optional[str] = Field(None, description="Harici ID (küpe no vb.)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Ek bilgiler")


class AnimalUpdate(BaseModel):
    """Hayvan güncelleme şeması"""
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    health_score: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AnimalResponse(AnimalBase):
    """Hayvan yanıt şeması"""
    id: int
    external_id: Optional[str] = None
    health_score: float = Field(default=100.0, ge=0, le=100)
    is_active: bool = True
    last_seen: Optional[datetime] = None
    last_position_x: Optional[float] = None
    last_position_y: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "external_id": "TR-001-2022",
                "name": "Sarıkız",
                "species": "cattle",
                "breed": "Holstein",
                "birth_date": "2022-03-15",
                "gender": "female",
                "color": "black-white",
                "weight": 450.5,
                "health_score": 95.5,
                "is_active": True,
                "last_seen": "2025-12-06T10:30:00",
                "created_at": "2025-01-01T00:00:00"
            }
        }


class AnimalListResponse(BaseModel):
    """Hayvan listesi yanıt şeması"""
    items: List[AnimalResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class AnimalStatistics(BaseModel):
    """Hayvan istatistikleri şeması"""
    animal_id: int
    total_detections: int = 0
    total_tracking_time: float = 0.0
    average_speed: float = 0.0
    total_distance: float = 0.0
    behavior_counts: Dict[str, int] = Field(default_factory=dict)
    zone_visits: Dict[str, int] = Field(default_factory=dict)
    health_history: List[Dict[str, Any]] = Field(default_factory=list)


class AnimalHealth(BaseModel):
    """Hayvan sağlık şeması"""
    animal_id: int
    health_score: float = Field(ge=0, le=100)
    body_condition_score: Optional[float] = Field(None, ge=1, le=5)
    lameness_score: Optional[float] = Field(None, ge=0, le=5)
    activity_level: str = "normal"  # low, normal, high
    anomalies: List[str] = Field(default_factory=list)
    last_updated: datetime
    recommendations: List[str] = Field(default_factory=list)


class AnimalBehavior(BaseModel):
    """Hayvan davranış şeması"""
    animal_id: int
    current_behavior: str
    behavior_confidence: float = Field(ge=0, le=1)
    behavior_history: List[Dict[str, Any]] = Field(default_factory=list)
    daily_pattern: Dict[str, float] = Field(default_factory=dict)  # behavior_type: percentage
    timestamp: datetime
