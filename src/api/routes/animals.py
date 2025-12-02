"""
AI Animal Tracking System - Animal Routes
==========================================

Hayvan yönetimi API endpoint'leri.
DatabaseService ile gerçek veritabanı entegrasyonu.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.api.services import DatabaseService


router = APIRouter(prefix="/animals", tags=["Animals"])


# ===========================================
# Pydantic Models
# ===========================================

class AnimalBase(BaseModel):
    """Hayvan temel modeli"""
    class_name: str = Field(..., description="Tür (cat, dog, cow, etc.)")
    name: Optional[str] = Field(None, description="Hayvan ismi")
    tag: Optional[str] = Field(None, description="Kulak numarası/tag")


class AnimalCreate(AnimalBase):
    """Hayvan oluşturma modeli"""
    id: Optional[str] = Field(None, description="Benzersiz hayvan ID (otomatik oluşturulabilir)")
    color: Optional[str] = Field(None, description="Renk")
    markings: Optional[str] = Field(None, description="Ayırt edici işaretler")


class AnimalUpdate(BaseModel):
    """Hayvan güncelleme modeli"""
    name: Optional[str] = None
    tag: Optional[str] = None
    color: Optional[str] = None
    health_status: Optional[str] = None


class AnimalResponse(BaseModel):
    """Hayvan yanıt modeli"""
    id: str
    class_name: str
    name: Optional[str] = None
    tag: Optional[str] = None
    color: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_detections: int = 0
    health_status: str = "unknown"


class AnimalListResponse(BaseModel):
    """Hayvan listesi yanıtı"""
    animals: List[AnimalResponse]
    total: int
    page: int
    per_page: int


class AnimalStats(BaseModel):
    """Hayvan istatistikleri"""
    animal_id: str
    total_detections: int
    behavior_distribution: dict
    health_records_count: int
    alerts_count: int


class BehaviorRecord(BaseModel):
    """Davranış kaydı"""
    behavior: str
    confidence: float
    timestamp: str
    duration: Optional[float] = None


class HealthRecord(BaseModel):
    """Sağlık kaydı"""
    bcs_score: Optional[float] = None
    lameness_score: Optional[int] = None
    status: str
    timestamp: str


# ===========================================
# Service instance
# ===========================================

def get_db_service() -> DatabaseService:
    """Get database service instance."""
    return DatabaseService.get_instance()


# ===========================================
# Helper functions
# ===========================================

def _animal_to_response(animal) -> AnimalResponse:
    """Convert database animal to response model."""
    return AnimalResponse(
        id=animal.id,
        class_name=animal.class_name,
        name=animal.name,
        tag=animal.tag,
        color=animal.color,
        first_seen=animal.first_seen_at.isoformat() if animal.first_seen_at else None,
        last_seen=animal.last_seen_at.isoformat() if animal.last_seen_at else None,
        total_detections=animal.total_detections or 0,
        health_status=animal.health_status or "unknown"
    )


# ===========================================
# Endpoints
# ===========================================

@router.get("/", response_model=AnimalListResponse)
async def list_animals(
    class_name: Optional[str] = Query(None, description="Tür filtresi"),
    page: int = Query(1, ge=1, description="Sayfa"),
    per_page: int = Query(20, ge=1, le=100, description="Sayfa başına")
):
    """
    Tüm hayvanları listele.
    
    Args:
        class_name: Tür filtresi (opsiyonel)
        page: Sayfa numarası
        per_page: Sayfa başına kayıt
        
    Returns:
        Hayvan listesi
    """
    db = get_db_service()
    
    # Get all animals
    animals = db.get_all_animals()
    
    # Filter by class
    if class_name:
        animals = [a for a in animals if a.class_name == class_name]
    
    # Pagination
    total = len(animals)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = animals[start:end]
    
    return AnimalListResponse(
        animals=[_animal_to_response(a) for a in paginated],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_animal(animal: AnimalCreate):
    """
    Yeni hayvan ekle (manuel).
    
    Args:
        animal: Hayvan bilgileri
        
    Returns:
        Oluşturulan hayvan
    """
    db = get_db_service()
    
    # Generate ID if not provided
    animal_id = animal.id
    if not animal_id:
        import uuid
        animal_id = f"{animal.class_name.upper()}_{uuid.uuid4().hex[:8].upper()}"
    
    # Check if already exists
    existing = db.get_animal(animal_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Animal {animal_id} already exists"
        )
    
    # Create animal
    new_animal = db.create_animal(
        animal_id=animal_id,
        class_name=animal.class_name,
        name=animal.name,
        tag=animal.tag,
        color=animal.color,
        markings=animal.markings
    )
    
    return {
        "message": f"Animal {animal_id} created",
        "animal": _animal_to_response(new_animal)
    }


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(animal_id: str):
    """
    Hayvan detayları.
    
    Args:
        animal_id: Hayvan ID
        
    Returns:
        Hayvan bilgileri
    """
    db = get_db_service()
    
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    return _animal_to_response(animal)


@router.put("/{animal_id}")
async def update_animal(animal_id: str, update: AnimalUpdate):
    """
    Hayvan bilgilerini güncelle.
    
    Args:
        animal_id: Hayvan ID
        update: Güncellenecek alanlar
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    # Build update dict
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.tag is not None:
        update_data["tag"] = update.tag
    if update.color is not None:
        update_data["color"] = update.color
    if update.health_status is not None:
        update_data["health_status"] = update.health_status
    
    if update_data:
        updated = db.update_animal(animal_id, **update_data)
        return {
            "message": f"Animal {animal_id} updated",
            "animal": _animal_to_response(updated)
        }
    
    return {"message": "No fields to update"}


@router.delete("/{animal_id}")
async def delete_animal(animal_id: str):
    """
    Hayvanı sil.
    
    Args:
        animal_id: Hayvan ID
    """
    db = get_db_service()
    
    if not db.delete_animal(animal_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    return {"message": f"Animal {animal_id} deleted"}


@router.get("/{animal_id}/stats", response_model=AnimalStats)
async def get_animal_stats(animal_id: str):
    """
    Hayvan istatistikleri.
    
    Args:
        animal_id: Hayvan ID
        
    Returns:
        İstatistikler
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    # Get statistics
    detections = db.get_detections_for_animal(animal_id, limit=10000)
    behaviors = db.get_behaviors_for_animal(animal_id, limit=10000)
    health_records = db.get_health_records_for_animal(animal_id, limit=10000)
    alerts = db.get_alerts_for_animal(animal_id, limit=10000)
    
    # Calculate behavior distribution
    behavior_counts = {}
    for b in behaviors:
        bt = b.behavior
        behavior_counts[bt] = behavior_counts.get(bt, 0) + 1
    
    return AnimalStats(
        animal_id=animal_id,
        total_detections=len(detections),
        behavior_distribution=behavior_counts,
        health_records_count=len(health_records),
        alerts_count=len(alerts)
    )


@router.get("/{animal_id}/detections")
async def get_animal_detections(
    animal_id: str,
    limit: int = Query(100, description="Maksimum kayıt")
):
    """
    Hayvan tespit geçmişi.
    
    Args:
        animal_id: Hayvan ID
        limit: Maksimum kayıt
        
    Returns:
        Tespit listesi
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    detections = db.get_detections_for_animal(animal_id, limit=limit)
    
    return {
        "animal_id": animal_id,
        "total": len(detections),
        "detections": [
            {
                "id": d.id,
                "track_id": d.track_id,
                "camera_id": d.camera_id,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2],
                "center": [d.center_x, d.center_y],
                "timestamp": d.detected_at.isoformat() if d.detected_at else None
            }
            for d in detections
        ]
    }


@router.get("/{animal_id}/behaviors")
async def get_animal_behaviors(
    animal_id: str,
    limit: int = Query(50, description="Maksimum kayıt")
):
    """
    Hayvan davranış geçmişi.
    
    Args:
        animal_id: Hayvan ID
        limit: Maksimum kayıt
        
    Returns:
        Davranış listesi
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    behaviors = db.get_behaviors_for_animal(animal_id, limit=limit)
    
    return {
        "animal_id": animal_id,
        "total": len(behaviors),
        "behaviors": [
            BehaviorRecord(
                behavior=b.behavior,
                confidence=b.confidence or 0.0,
                timestamp=b.started_at.isoformat() if b.started_at else "",
                duration=b.duration_seconds
            ).model_dump()
            for b in behaviors
        ]
    }


@router.get("/{animal_id}/health")
async def get_animal_health(
    animal_id: str,
    limit: int = Query(10, description="Son N kayıt")
):
    """
    Hayvan sağlık durumu.
    
    Args:
        animal_id: Hayvan ID
        limit: Son kayıt sayısı
        
    Returns:
        Sağlık bilgileri
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    health_records = db.get_health_records_for_animal(animal_id, limit=limit)
    alerts = db.get_alerts_for_animal(animal_id, limit=10)
    
    # Get latest health status
    latest = health_records[0] if health_records else None
    
    return {
        "animal_id": animal_id,
        "overall_status": latest.status if latest else animal.health_status,
        "bcs_score": latest.bcs_score if latest else animal.bcs_score,
        "lameness_score": latest.lameness_score if latest else animal.lameness_score,
        "last_checked": latest.recorded_at.isoformat() if latest and latest.recorded_at else None,
        "records": [
            HealthRecord(
                bcs_score=r.bcs_score,
                lameness_score=r.lameness_score,
                status=r.status or "unknown",
                timestamp=r.recorded_at.isoformat() if r.recorded_at else ""
            ).model_dump()
            for r in health_records
        ],
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "is_read": a.is_read,
                "timestamp": a.created_at.isoformat() if a.created_at else None
            }
            for a in alerts
        ]
    }


@router.get("/{animal_id}/trajectory")
async def get_animal_trajectory(
    animal_id: str,
    last_n: int = Query(100, description="Son N nokta")
):
    """
    Hayvan hareket geçmişi.
    
    Args:
        animal_id: Hayvan ID
        last_n: Son N nokta
        
    Returns:
        Koordinat listesi
    """
    db = get_db_service()
    
    # Find animal
    animal = db.get_animal(animal_id)
    
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found"
        )
    
    # Get recent detections for trajectory
    detections = db.get_detections_for_animal(animal_id, limit=last_n)
    
    # Extract center points
    points = []
    for d in detections:
        points.append({
            "x": d.center_x,
            "y": d.center_y,
            "timestamp": d.detected_at.isoformat() if d.detected_at else None
        })
    
    return {
        "animal_id": animal_id,
        "total": len(points),
        "points": points
    }
