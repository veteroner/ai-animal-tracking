"""
AI Animal Tracking System - Farm Monitor API Routes
====================================================

Çiftlik izleme sistemi API endpoint'leri.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/farm-monitor", tags=["farm-monitor"])


# ==========================================
# Pydantic Models
# ==========================================

class CameraCreate(BaseModel):
    """Kamera oluşturma isteği"""
    camera_id: str = Field(..., description="Benzersiz kamera ID'si")
    name: str = Field(..., description="Kamera adı")
    url: str = Field(..., description="Kamera URL'si (RTSP, HTTP veya webcam index)")
    location: str = Field("unknown", description="Kamera konumu (ahır, mera, vs)")


class CameraResponse(BaseModel):
    """Kamera yanıtı"""
    id: str
    name: str
    url: str
    location: str
    farm_id: str
    is_active: bool
    status: str
    fps: float
    resolution: List[int]
    error_count: int


class FarmStatusResponse(BaseModel):
    """Çiftlik durumu yanıtı"""
    farm_id: str
    is_running: bool
    cameras: Dict[str, Any]
    stats: Dict[str, Any]
    alerts_count: int


class AlertResponse(BaseModel):
    """Alarm yanıtı"""
    id: str
    farm_id: str
    camera_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    animal_id: Optional[str]
    is_read: bool
    created_at: str


class AnimalResponse(BaseModel):
    """Hayvan yanıtı"""
    animal_id: str
    track_id: int
    class_name: str
    bbox: List[int]
    confidence: float
    is_new: bool


class EstrusResponse(BaseModel):
    """Kızgınlık yanıtı"""
    animal_id: str
    detected_at: str
    hours_ago: float


# ==========================================
# Global State (Demo için)
# ==========================================

# Gerçek uygulamada database kullanılmalı
_farm_monitors: Dict[str, Any] = {}

def _get_or_create_monitor(farm_id: str):
    """Farm monitor al veya oluştur"""
    try:
        from src.camera.farm_monitor import get_farm_monitor
        return get_farm_monitor(farm_id)
    except ImportError:
        # Demo mode - basit bir mock döndür
        if farm_id not in _farm_monitors:
            _farm_monitors[farm_id] = {
                "farm_id": farm_id,
                "is_running": False,
                "cameras": {},
                "alerts": [],
                "animals": {},
                "estrus_candidates": {},
                "stats": {
                    "total_detections": 0,
                    "unique_animals": 0,
                    "new_animals_today": 0,
                    "estrus_detections": 0,
                    "health_warnings": 0,
                }
            }
        return _farm_monitors[farm_id]


# ==========================================
# Endpoints
# ==========================================

@router.post("/farms/{farm_id}/cameras", response_model=Dict[str, Any])
async def add_camera(
    farm_id: str,
    camera: CameraCreate,
):
    """
    Çiftliğe yeni kamera ekle
    
    - **camera_id**: Benzersiz kamera ID'si
    - **name**: Kamera adı (örn: "Ahır Kamera 1")
    - **url**: Kamera URL'si
      - RTSP: `rtsp://kullanici:sifre@192.168.1.100:554/stream`
      - HTTP: `http://192.168.1.100:8080/video`
      - Webcam: `0` (dahili webcam)
    - **location**: Kamera konumu (örn: "Ahır", "Mera", "Yem Deposu")
    """
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        # Demo mode
        monitor["cameras"][camera.camera_id] = {
            "id": camera.camera_id,
            "name": camera.name,
            "url": camera.url,
            "location": camera.location,
            "farm_id": farm_id,
            "is_active": True,
            "status": "disconnected",
            "fps": 0,
            "resolution": [0, 0],
            "error_count": 0,
        }
        return {"success": True, "camera": monitor["cameras"][camera.camera_id]}
    else:
        # Real mode
        cam = monitor.add_camera(
            camera_id=camera.camera_id,
            name=camera.name,
            url=camera.url,
            location=camera.location,
        )
        return {"success": True, "camera": cam.to_dict()}


@router.delete("/farms/{farm_id}/cameras/{camera_id}")
async def remove_camera(farm_id: str, camera_id: str):
    """Kamerayı kaldır"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        if camera_id in monitor["cameras"]:
            del monitor["cameras"][camera_id]
            return {"success": True, "message": "Kamera kaldırıldı"}
        raise HTTPException(status_code=404, detail="Kamera bulunamadı")
    else:
        if monitor.remove_camera(camera_id):
            return {"success": True, "message": "Kamera kaldırıldı"}
        raise HTTPException(status_code=404, detail="Kamera bulunamadı")


@router.get("/farms/{farm_id}/cameras", response_model=List[Dict[str, Any]])
async def list_cameras(farm_id: str):
    """Çiftlikteki tüm kameraları listele"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        return list(monitor["cameras"].values())
    else:
        return [cam.to_dict() for cam in monitor.cameras.values()]


@router.post("/farms/{farm_id}/cameras/{camera_id}/connect")
async def connect_camera(farm_id: str, camera_id: str):
    """Kameraya bağlan"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        if camera_id in monitor["cameras"]:
            monitor["cameras"][camera_id]["status"] = "connected"
            return {"success": True, "message": "Kameraya bağlandı"}
        raise HTTPException(status_code=404, detail="Kamera bulunamadı")
    else:
        if monitor.connect_camera(camera_id):
            return {"success": True, "message": "Kameraya bağlandı"}
        raise HTTPException(status_code=500, detail="Bağlantı başarısız")


@router.post("/farms/{farm_id}/cameras/{camera_id}/disconnect")
async def disconnect_camera(farm_id: str, camera_id: str):
    """Kamera bağlantısını kes"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        if camera_id in monitor["cameras"]:
            monitor["cameras"][camera_id]["status"] = "disconnected"
            return {"success": True, "message": "Bağlantı kesildi"}
        raise HTTPException(status_code=404, detail="Kamera bulunamadı")
    else:
        monitor.disconnect_camera(camera_id)
        return {"success": True, "message": "Bağlantı kesildi"}


@router.post("/farms/{farm_id}/start")
async def start_monitoring(farm_id: str, background_tasks: BackgroundTasks):
    """
    Çiftlik izlemeyi başlat
    
    Tüm kameralardan görüntü alınır ve AI analizi yapılır:
    - Hayvan tespiti
    - Re-ID (bireysel tanıma)
    - Davranış analizi
    - Sağlık izleme
    - Kızgınlık tespiti
    """
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        monitor["is_running"] = True
        return {
            "success": True, 
            "message": "İzleme başlatıldı (Demo Mode)",
            "note": "Gerçek izleme için backend'in lokal makinede çalışması gerekiyor."
        }
    else:
        background_tasks.add_task(monitor.start)
        return {"success": True, "message": "İzleme başlatıldı"}


@router.post("/farms/{farm_id}/stop")
async def stop_monitoring(farm_id: str):
    """Çiftlik izlemeyi durdur"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        monitor["is_running"] = False
        return {"success": True, "message": "İzleme durduruldu"}
    else:
        monitor.stop()
        return {"success": True, "message": "İzleme durduruldu"}


@router.get("/farms/{farm_id}/status", response_model=Dict[str, Any])
async def get_farm_status(farm_id: str):
    """Çiftlik izleme durumunu al"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        return {
            "farm_id": farm_id,
            "is_running": monitor["is_running"],
            "cameras": monitor["cameras"],
            "stats": monitor["stats"],
            "alerts_count": len([a for a in monitor["alerts"] if not a.get("is_read", False)]),
        }
    else:
        return monitor.get_status()


@router.get("/farms/{farm_id}/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    farm_id: str,
    unread_only: bool = Query(False, description="Sadece okunmamış alarmlar"),
):
    """Çiftlik alarmlarını al"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        alerts = monitor["alerts"]
        if unread_only:
            alerts = [a for a in alerts if not a.get("is_read", False)]
        return alerts
    else:
        return monitor.get_alerts(unread_only=unread_only)


@router.get("/farms/{farm_id}/animals", response_model=List[Dict[str, Any]])
async def get_detected_animals(farm_id: str):
    """Tespit edilen hayvanları al"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        return list(monitor["animals"].values())
    else:
        return monitor.get_animals()


@router.get("/farms/{farm_id}/estrus", response_model=List[Dict[str, Any]])
async def get_estrus_detections(farm_id: str):
    """Kızgınlık tespitlerini al"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        return [
            {
                "animal_id": aid,
                "detected_at": dt,
                "hours_ago": 0,
            }
            for aid, dt in monitor["estrus_candidates"].items()
        ]
    else:
        return monitor.get_estrus_candidates()


@router.get("/farms/{farm_id}/stats", response_model=Dict[str, Any])
async def get_detection_stats(farm_id: str):
    """Tespit istatistiklerini al"""
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        return monitor["stats"]
    else:
        status = monitor.get_status()
        return status.get("stats", {})


# ==========================================
# Demo Data Endpoint
# ==========================================

@router.post("/farms/{farm_id}/demo/generate")
async def generate_demo_data(farm_id: str):
    """
    Demo veri oluştur (Test için)
    
    Gerçek kamera olmadan sistemi test etmek için örnek veri oluşturur.
    """
    monitor = _get_or_create_monitor(farm_id)
    
    if isinstance(monitor, dict):
        # Demo kameralar
        monitor["cameras"] = {
            "cam-001": {
                "id": "cam-001",
                "name": "Ahır Kamera 1",
                "url": "rtsp://192.168.1.100:554/stream",
                "location": "Ahır",
                "farm_id": farm_id,
                "is_active": True,
                "status": "streaming",
                "fps": 25,
                "resolution": [1920, 1080],
                "error_count": 0,
            },
            "cam-002": {
                "id": "cam-002",
                "name": "Mera Kamera",
                "url": "rtsp://192.168.1.101:554/stream",
                "location": "Mera",
                "farm_id": farm_id,
                "is_active": True,
                "status": "streaming",
                "fps": 25,
                "resolution": [1920, 1080],
                "error_count": 0,
            },
        }
        
        # Demo hayvanlar
        monitor["animals"] = {
            f"INEK-{i:03d}": {
                "animal_id": f"INEK-{i:03d}",
                "track_id": i,
                "class_name": "cow",
                "bbox": [100 + i*50, 100 + i*30, 200 + i*50, 250 + i*30],
                "confidence": 0.85 + (i % 10) * 0.01,
                "is_new": i > 45,
            }
            for i in range(1, 51)
        }
        
        # Demo alarmlar
        from datetime import datetime, timedelta
        monitor["alerts"] = [
            {
                "id": "alert-001",
                "farm_id": farm_id,
                "camera_id": "cam-001",
                "alert_type": "estrus_detected",
                "severity": "high",
                "title": "🔥 Kızgınlık Tespit Edildi!",
                "message": "INEK-012 için kızgınlık belirtileri tespit edildi.",
                "animal_id": "INEK-012",
                "is_read": False,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "alert-002",
                "farm_id": farm_id,
                "camera_id": "cam-001",
                "alert_type": "health_warning",
                "severity": "medium",
                "title": "Sağlık Uyarısı",
                "message": "INEK-023 için topallık tespit edildi.",
                "animal_id": "INEK-023",
                "is_read": False,
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
            {
                "id": "alert-003",
                "farm_id": farm_id,
                "camera_id": "cam-002",
                "alert_type": "new_animal",
                "severity": "low",
                "title": "Yeni Hayvan",
                "message": "INEK-050 sisteme kaydedildi.",
                "animal_id": "INEK-050",
                "is_read": True,
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        ]
        
        # Demo kızgınlık tespitleri
        monitor["estrus_candidates"] = {
            "INEK-012": datetime.now().isoformat(),
            "INEK-028": (datetime.now() - timedelta(hours=12)).isoformat(),
        }
        
        # Demo istatistikler
        monitor["stats"] = {
            "total_detections": 15420,
            "unique_animals": 50,
            "new_animals_today": 2,
            "estrus_detections": 5,
            "health_warnings": 3,
        }
        
        monitor["is_running"] = True
        
        return {
            "success": True,
            "message": "Demo veriler oluşturuldu",
            "cameras": 2,
            "animals": 50,
            "alerts": 3,
        }
    
    return {"success": False, "message": "Real mode'da demo veri oluşturulamaz"}
