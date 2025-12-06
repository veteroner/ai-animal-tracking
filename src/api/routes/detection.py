"""
AI Animal Tracking System - Real-Time Detection WebSocket
=========================================================

Gerçek zamanlı hayvan tespiti ve OTOMATİK Re-ID için WebSocket endpoint.

Özellikler:
- Tam otomatik hayvan tanıma
- Kullanıcı müdahalesi YOK
- Yeni hayvanlar otomatik kaydedilir
- ID'ler otomatik atanır
"""

import asyncio
import base64
import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import Auto Re-ID System
try:
    from src.identification.auto_reid import AutoReID, AutoReIDConfig
    AUTO_REID_AVAILABLE = True
except ImportError:
    AUTO_REID_AVAILABLE = False
    AutoReID = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["detection"])


# ===========================================
# Global Auto Re-ID Instance
# ===========================================

# Otomatik Re-ID sistemi (global instance)
if AUTO_REID_AVAILABLE:
    config = AutoReIDConfig(
        similarity_threshold=0.65,  # Eşleşme için %65 benzerlik
        new_animal_threshold=0.50,  # %50 altında yeni hayvan
        max_age=50,  # 50 frame kaybolma toleransı
        min_hits=3,  # 3 tespitten sonra kaydet
        auto_save=True,
        save_interval=50,  # Her 50 frame'de kaydet
    )
    auto_reid = AutoReID(config)
    logger.info("✅ Otomatik Re-ID sistemi hazır")
else:
    auto_reid = None
    logger.warning("⚠️ Auto Re-ID kullanılamıyor")


# ===========================================
# Data Classes
# ===========================================

@dataclass
class TrackedAnimal:
    """Tespit edilen ve takip edilen hayvan"""
    track_id: int
    animal_id: str
    class_name: str
    bbox: List[int]
    confidence: float
    re_id_confidence: float = 0.0
    is_identified: bool = False
    is_new: bool = False
    velocity: tuple = (0, 0)
    direction: float = 0.0
    health_score: Optional[float] = None
    behavior: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "animal_id": self.animal_id,
            "class_name": self.class_name,
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 3),
            "re_id_confidence": round(self.re_id_confidence, 3),
            "is_identified": self.is_identified,
            "is_new": self.is_new,
            "velocity": self.velocity,
            "direction": round(self.direction, 1),
            "health_score": self.health_score,
            "behavior": self.behavior
        }


@dataclass
class DetectionResult:
    """Tespit sonucu"""
    frame_id: int
    timestamp: float
    fps: float
    animal_count: int
    animals: List[TrackedAnimal]
    frame_size: tuple
    total_registered: int = 0
    new_this_frame: int = 0
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "fps": round(self.fps, 1),
            "animal_count": self.animal_count,
            "total_registered": self.total_registered,
            "new_this_frame": self.new_this_frame,
            "animals": [a.to_dict() for a in self.animals],
            "frame_size": list(self.frame_size)
        }


# ===========================================
# Real-Time Detector (Using Auto Re-ID)
# ===========================================

class RealTimeDetector:
    """
    Gerçek zamanlı hayvan tespit ve TAM OTOMATİK tanıma sistemi.
    
    Kullanıcı müdahalesi YOK:
    - Yeni hayvanlar otomatik kaydedilir
    - ID'ler otomatik atanır
    - Aynı hayvanlar otomatik tanınır
    """
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        
        # FPS hesaplama
        self._frame_count = 0
        self._fps_history: List[float] = []
        self._last_time = time.time()
        
        # Model yüklenme durumu
        self._initialized = False
    
    def initialize(self):
        """Model ve tracker'ı yükle"""
        if self._initialized:
            return
        
        try:
            # Auto Re-ID sistemini initialize et
            if auto_reid:
                auto_reid.initialize()
                logger.info("🚀 Otomatik Re-ID sistemi başlatıldı")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Detector initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._initialized = True
    
    def process_frame(self, frame: Any) -> DetectionResult:
        """
        Tek bir frame'i işle - TAM OTOMATİK.
        
        Her şey otomatik:
        1. Hayvanları tespit et
        2. Yeni hayvanları kaydet
        3. Daha önce görülenleri tanı
        4. Sonuç döndür
        """
        if not CV2_AVAILABLE:
            return DetectionResult(
                frame_id=0, timestamp="", detections=[],
                total_registered=0, new_this_frame=0,
                processing_time_ms=0, frame_size=(0, 0)
            )
            
        start_time = time.time()
        self._frame_count += 1
        h, w = frame.shape[:2]
        
        tracked_animals: List[TrackedAnimal] = []
        total_registered = 0
        new_this_frame = 0
        
        # Lazy initialization
        if not self._initialized:
            self.initialize()
        
        try:
            if auto_reid:
                # Otomatik Re-ID sistemi ile işle
                result = auto_reid.process(frame)
                
                total_registered = result.total_registered
                new_this_frame = result.new_this_frame
                
                for animal in result.animals:
                    tracked = TrackedAnimal(
                        track_id=animal.track_id,
                        animal_id=animal.animal_id,
                        class_name=animal.class_name,
                        bbox=animal.bbox,
                        confidence=animal.confidence,
                        re_id_confidence=animal.similarity,
                        is_identified=not animal.animal_id.startswith("TEMP_"),
                        is_new=animal.is_new,
                        velocity=animal.velocity,
                        direction=0.0,
                    )
                    tracked_animals.append(tracked)
                    
                    if animal.is_new:
                        logger.info(f"🆕 Yeni hayvan kaydedildi: {animal.animal_id} ({animal.class_name})")
            else:
                logger.warning("Auto Re-ID kullanılamıyor")
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # FPS hesapla
        process_time = time.time() - start_time
        current_fps = 1.0 / process_time if process_time > 0 else 0
        self._fps_history.append(current_fps)
        if len(self._fps_history) > 30:
            self._fps_history.pop(0)
        avg_fps = sum(self._fps_history) / len(self._fps_history)
        
        return DetectionResult(
            frame_id=self._frame_count,
            timestamp=time.time(),
            fps=avg_fps,
            animal_count=len(tracked_animals),
            animals=tracked_animals,
            frame_size=(w, h),
            total_registered=total_registered,
            new_this_frame=new_this_frame,
        )
    
    def get_gallery_info(self) -> dict:
        """Galeri bilgisi"""
        if auto_reid:
            stats = auto_reid.get_stats()
            animals = auto_reid.get_all_animals()
            return {
                "count": stats["gallery"]["total_animals"],
                "by_class": stats["gallery"]["by_class"],
                "animals": animals,
            }
        return {"count": 0, "animals": []}
    
    def reset(self):
        """Tracker'ı sıfırla (galeri korunur)"""
        self._frame_count = 0
        self._fps_history.clear()
        if auto_reid:
            auto_reid.track_manager = type(auto_reid.track_manager)(auto_reid.config)
        logger.info("Detector reset (galeri korundu)")
    
    def reset_all(self):
        """Galeri dahil her şeyi sıfırla"""
        self.reset()
        if auto_reid:
            auto_reid.reset()
        logger.warning("⚠️ Galeri dahil her şey sıfırlandı!")
    
    def save_gallery(self):
        """Galeriyi kaydet"""
        if auto_reid:
            auto_reid.save()


# Global detector instance
detector = RealTimeDetector()


# ===========================================
# WebSocket Manager
# ===========================================

class DetectionConnectionManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"Detection WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"Detection WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Tüm bağlantılara mesaj gönder"""
        if not self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        for conn in disconnected:
            await self.disconnect(conn)


manager = DetectionConnectionManager()


# ===========================================
# Camera Stream Handler
# ===========================================

class CameraStream:
    """Kamera stream yöneticisi"""
    
    def __init__(self):
        self.cap: Optional[Any] = None  # cv2.VideoCapture
        self.source: Optional[Any] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    def open(self, source: int = 0):
        """Kamera aç"""
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV (cv2) is not available")
            
        self.source = source
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {source}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info(f"Camera opened: {source}")
    
    def read(self) -> Optional[Any]:
        """Frame oku"""
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def close(self):
        """Kamera kapat"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_running = False
        logger.info("Camera closed")
    
    async def stream_loop(self, source: int = 0, fps_limit: int = 30):
        """Kamera stream döngüsü"""
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV (cv2) is not available")
            
        try:
            self.open(source)
            self.is_running = True
            detector.initialize()
            
            frame_interval = 1.0 / fps_limit
            
            while self.is_running:
                start = time.time()
                
                frame = self.read()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                result = detector.process_frame(frame)
                await manager.broadcast(result.to_dict())
                
                elapsed = time.time() - start
                if elapsed < frame_interval:
                    await asyncio.sleep(frame_interval - elapsed)
                else:
                    await asyncio.sleep(0.001)
                    
        except Exception as e:
            logger.error(f"Stream error: {e}")
        finally:
            self.close()


camera_stream = CameraStream()


# ===========================================
# REST Endpoints
# ===========================================

@router.get("/status")
async def get_status():
    """Detector durumu"""
    gallery_info = detector.get_gallery_info()
    return {
        "initialized": detector._initialized,
        "frame_count": detector._frame_count,
        "gallery_size": gallery_info.get("count", 0),
        "gallery_by_class": gallery_info.get("by_class", {}),
        "active_connections": len(manager.active_connections),
        "camera_running": camera_stream.is_running,
        "auto_reid_available": AUTO_REID_AVAILABLE,
    }


@router.get("/gallery")
async def get_gallery():
    """Tüm kayıtlı hayvanlar listesi"""
    return detector.get_gallery_info()


@router.get("/animals")
async def get_all_animals():
    """Tüm hayvanların detaylı listesi"""
    if auto_reid:
        return {
            "count": auto_reid.gallery.size,
            "animals": auto_reid.get_all_animals(),
            "stats": auto_reid.get_stats(),
        }
    return {"count": 0, "animals": [], "stats": {}}


@router.post("/reset")
async def reset_detector():
    """Tracker'ı sıfırla (galeri korunur)"""
    detector.reset()
    return {"status": "ok", "message": "Detector reset (galeri korundu)"}


@router.post("/reset-all")
async def reset_all():
    """Galeri dahil her şeyi sıfırla"""
    detector.reset_all()
    return {"status": "ok", "message": "Galeri dahil her şey sıfırlandı!"}


@router.post("/save")
async def save_gallery():
    """Galeriyi kaydet"""
    detector.save_gallery()
    return {"status": "ok", "message": "Galeri kaydedildi"}


@router.post("/start/{camera_id}")
async def start_camera(camera_id: int = 0):
    """Kamera stream'i başlat"""
    if camera_stream.is_running:
        return {"status": "already_running"}
    
    camera_stream._task = asyncio.create_task(
        camera_stream.stream_loop(camera_id)
    )
    
    return {"status": "started", "camera_id": camera_id}


@router.post("/stop")
async def stop_camera():
    """Kamera stream'i durdur"""
    camera_stream.is_running = False
    if camera_stream._task:
        camera_stream._task.cancel()
    return {"status": "stopped"}


# ===========================================
# HTTP Frame Processing Endpoint (Multipart - for Mobile)
# ===========================================

from fastapi import File, UploadFile

@router.post("/process-frame")
async def process_frame_multipart(file: UploadFile = File(...)):
    """
    Multipart form-data üzerinden frame işleme - MOBİL UYGULAMALAR İÇİN.
    
    Request:
        file: JPEG/PNG image file
    
    Returns:
    {
        "frame_id": 1,
        "fps": 15.0,
        "animal_count": 2,
        "total_registered": 5,
        "new_this_frame": 1,
        "animals": [...]
    }
    """
    try:
        # Dosyayı oku
        contents = await file.read()
        
        # Numpy array'e dönüştür
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid image data"}
            )
        
        # Frame'i işle - TAM OTOMATİK
        result = detector.process_frame(frame)
        
        # Mobil uygulamaya uygun format döndür
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Frame processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.post("/process-frame-base64")
async def process_frame_base64(request_data: dict):
    """
    HTTP üzerinden frame işleme - TAM OTOMATİK.
    
    Request body:
    {
        "frame": "base64 encoded JPEG image"
    }
    
    Returns:
    {
        "success": true,
        "result": {
            "frame_id": 1,
            "animal_count": 2,
            "total_registered": 5,
            "new_this_frame": 1,
            "animals": [...]
        }
    }
    """
    try:
        frame_data = request_data.get("frame", "")
        
        if not frame_data:
            return {"success": False, "error": "No frame data provided"}
        
        # Base64 decode
        if "base64," in frame_data:
            frame_data = frame_data.split("base64,")[1]
        
        try:
            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return {"success": False, "error": f"Failed to decode image: {str(e)}"}
        
        if frame is None:
            return {"success": False, "error": "Invalid image data"}
        
        # Frame'i işle - TAM OTOMATİK
        result = detector.process_frame(frame)
        
        return {
            "success": True,
            "result": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Frame processing error: {e}")
        return {"success": False, "error": str(e)}


# ===========================================
# WebSocket Endpoint
# ===========================================

@router.websocket("/ws")
async def detection_websocket(websocket: WebSocket):
    """
    Gerçek zamanlı tespit WebSocket endpoint'i.
    
    TAM OTOMATİK:
    - Yeni hayvanlar otomatik kaydedilir
    - ID'ler otomatik atanır
    - Kullanıcı müdahalesi yok
    """
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Otomatik Re-ID sistemi bağlandı",
            "auto_reid": AUTO_REID_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif msg_type == "start":
                    camera_id = message.get("camera", 0)
                    if not camera_stream.is_running:
                        camera_stream._task = asyncio.create_task(
                            camera_stream.stream_loop(camera_id)
                        )
                    await websocket.send_json({
                        "type": "status",
                        "status": "streaming",
                        "camera": camera_id
                    })
                
                elif msg_type == "stop":
                    camera_stream.is_running = False
                    await websocket.send_json({
                        "type": "status",
                        "status": "stopped"
                    })
                
                elif msg_type == "frame":
                    # Client'tan gelen frame - TAM OTOMATİK işle
                    frame_data = message.get("data", "")
                    if frame_data:
                        try:
                            if "," in frame_data:
                                frame_data = frame_data.split(",")[1]
                            
                            img_bytes = base64.b64decode(frame_data)
                            nparr = np.frombuffer(img_bytes, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                result = detector.process_frame(frame)
                                await websocket.send_json(result.to_dict())
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Invalid frame data"
                                })
                        except Exception as e:
                            logger.error(f"Frame decode error: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })
                
                elif msg_type == "reset":
                    detector.reset()
                    await websocket.send_json({
                        "type": "status",
                        "status": "reset",
                        "message": "Tracker sıfırlandı (galeri korundu)"
                    })
                
                elif msg_type == "gallery":
                    gallery = detector.get_gallery_info()
                    await websocket.send_json({
                        "type": "gallery",
                        "data": gallery
                    })
                
                elif msg_type == "stats":
                    if auto_reid:
                        stats = auto_reid.get_stats()
                        await websocket.send_json({
                            "type": "stats",
                            "data": stats
                        })
                
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Detection WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


# ===========================================
# Single Frame Analysis
# ===========================================

@router.post("/analyze")
async def analyze_frame(frame_data: dict):
    """Tek bir frame analizi"""
    try:
        frame_b64 = frame_data.get("frame", "")
        
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        
        img_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        if not detector._initialized:
            detector.initialize()
        
        result = detector.process_frame(frame)
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
