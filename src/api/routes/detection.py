"""
AI Animal Tracking System - Real-Time Detection WebSocket
=========================================================

Gerçek zamanlı hayvan tespiti ve Re-ID için WebSocket endpoint.
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

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["detection"])


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
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "fps": round(self.fps, 1),
            "animal_count": self.animal_count,
            "animals": [a.to_dict() for a in self.animals],
            "frame_size": list(self.frame_size)
        }


# ===========================================
# Real-Time Detector
# ===========================================

class RealTimeDetector:
    """
    Gerçek zamanlı hayvan tespit ve takip sistemi.
    
    - YOLOv8 ile tespit
    - ByteTrack ile takip
    - Feature extraction ile Re-ID
    """
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.detector = None
        self.tracker = None
        self.identifier = None
        self.gallery = {}  # animal_id -> features
        
        # Track ID -> Animal ID mapping
        self._track_to_animal: Dict[int, str] = {}
        self._animal_counter: Dict[str, int] = {}  # class -> counter
        
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
            # YOLO Detector
            from src.detection.yolo_detector import YOLODetector, DetectorConfig
            config = DetectorConfig(
                model_path=self.model_path,
                conf_threshold=0.4,
                iou_threshold=0.5
            )
            self.detector = YOLODetector(config=config)
            logger.info("✅ YOLOv8 detector loaded")
            
            # Object Tracker
            from src.tracking.object_tracker import ObjectTracker, TrackerConfig
            tracker_config = TrackerConfig(
                track_high_thresh=0.5,
                track_buffer=30,
                match_thresh=0.8
            )
            self.tracker = ObjectTracker(config=tracker_config)
            logger.info("✅ Object tracker loaded")
            
            # Animal Identifier (Re-ID)
            try:
                from src.identification.animal_identifier import (
                    AnimalIdentifier, 
                    IdentifierConfig
                )
                identifier_config = IdentifierConfig(
                    similarity_threshold=0.65,
                    save_gallery=False
                )
                self.identifier = AnimalIdentifier(config=identifier_config)
                logger.info("✅ Animal identifier (Re-ID) loaded")
            except Exception as e:
                logger.warning(f"⚠️ Re-ID yüklenemedi: {e}")
                self.identifier = None
            
            self._initialized = True
            logger.info("🚀 Real-time detector initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Detector initialization failed: {e}")
            raise
    
    def _generate_animal_id(self, class_name: str) -> str:
        """Hayvan sınıfına göre benzersiz ID oluştur"""
        # Sınıf kısaltmaları
        class_prefixes = {
            'cow': 'BOV', 'cattle': 'BOV', 'inek': 'BOV',
            'sheep': 'SHP', 'koyun': 'SHP',
            'goat': 'GOT', 'keçi': 'GOT',
            'horse': 'EQN', 'at': 'EQN',
            'chicken': 'CHK', 'tavuk': 'CHK',
            'dog': 'DOG', 'köpek': 'DOG',
            'cat': 'CAT', 'kedi': 'CAT',
            'bird': 'BRD', 'kuş': 'BRD',
            'person': 'PER', 'insan': 'PER',
        }
        
        prefix = class_prefixes.get(class_name.lower(), 'ANM')
        
        if prefix not in self._animal_counter:
            self._animal_counter[prefix] = 0
        
        self._animal_counter[prefix] += 1
        return f"{prefix}_{self._animal_counter[prefix]:04d}"
    
    def _extract_features(self, frame: np.ndarray, bbox: tuple) -> Optional[np.ndarray]:
        """Basit özellik çıkarma (Re-ID için)"""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        # Sınır kontrolü
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        
        # Resize to fixed size
        crop = cv2.resize(crop, (64, 128))
        
        # Color histogram (HSV)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def _match_identity(self, features: np.ndarray, class_name: str) -> tuple:
        """
        Özellikler ile galeri eşleştirmesi.
        Returns: (animal_id, confidence, is_new)
        """
        if features is None or len(self.gallery) == 0:
            return None, 0.0, True
        
        best_match = None
        best_score = 0.0
        
        for animal_id, (stored_features, stored_class) in self.gallery.items():
            # Aynı sınıfla eşleştir
            if stored_class != class_name:
                continue
            
            # Histogram karşılaştırması
            score = cv2.compareHist(
                features.astype(np.float32), 
                stored_features.astype(np.float32), 
                cv2.HISTCMP_CORREL
            )
            
            if score > best_score:
                best_score = score
                best_match = animal_id
        
        # Eşik kontrolü
        if best_score > 0.65:  # Similarity threshold
            return best_match, best_score, False
        
        return None, best_score, True
    
    def process_frame(self, frame: np.ndarray) -> DetectionResult:
        """
        Tek bir frame'i işle.
        
        Args:
            frame: BGR görüntü (OpenCV formatı)
            
        Returns:
            DetectionResult
        """
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        self._frame_count += 1
        h, w = frame.shape[:2]
        
        tracked_animals: List[TrackedAnimal] = []
        
        try:
            # 1. YOLO Detection
            detection_result = self.detector.detect(frame)
            
            # 2. Object Tracking
            if hasattr(detection_result, 'detections') and detection_result.detections:
                # Tracker'ı güncelle
                tracking_result = self.tracker.update(detection_result)
                
                # 3. Her track için işlem yap
                tracks = getattr(tracking_result, 'confirmed_tracks', []) or \
                         getattr(tracking_result, 'tracks', [])
                
                for track in tracks:
                    track_id = track.track_id
                    bbox = track.bbox if hasattr(track, 'bbox') else track.tlbr
                    class_name = getattr(track, 'class_name', 'animal')
                    confidence = getattr(track, 'confidence', 0.8)
                    
                    # Track -> Animal ID eşlemesi
                    if track_id in self._track_to_animal:
                        animal_id = self._track_to_animal[track_id]
                        re_id_conf = 1.0
                        is_identified = True
                    else:
                        # Yeni track, Re-ID dene
                        features = self._extract_features(frame, bbox)
                        matched_id, match_score, is_new = self._match_identity(features, class_name)
                        
                        if is_new or matched_id is None:
                            # Yeni hayvan
                            animal_id = self._generate_animal_id(class_name)
                            if features is not None:
                                self.gallery[animal_id] = (features, class_name)
                            re_id_conf = 0.0
                            is_identified = False
                        else:
                            # Mevcut hayvan
                            animal_id = matched_id
                            re_id_conf = match_score
                            is_identified = True
                        
                        self._track_to_animal[track_id] = animal_id
                    
                    # TrackedAnimal oluştur
                    velocity = getattr(track, 'velocity', (0, 0)) or (0, 0)
                    direction = getattr(track, 'direction', 0.0) or 0.0
                    
                    tracked = TrackedAnimal(
                        track_id=track_id,
                        animal_id=animal_id,
                        class_name=class_name,
                        bbox=[int(v) for v in bbox],
                        confidence=float(confidence),
                        re_id_confidence=float(re_id_conf),
                        is_identified=is_identified,
                        velocity=velocity,
                        direction=float(direction)
                    )
                    tracked_animals.append(tracked)
            
            else:
                # Tespit yok ama tracking yapabiliriz
                logger.debug(f"Frame {self._frame_count}: No detections")
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
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
            frame_size=(w, h)
        )
    
    def get_gallery_info(self) -> dict:
        """Galeri bilgisi"""
        return {
            "count": len(self.gallery),
            "animals": [
                {"animal_id": aid, "class": cls}
                for aid, (_, cls) in self.gallery.items()
            ]
        }
    
    def reset(self):
        """Tracker ve galeriyi sıfırla"""
        self._track_to_animal.clear()
        self._animal_counter.clear()
        self.gallery.clear()
        self._frame_count = 0
        self._fps_history.clear()
        if self.tracker:
            self.tracker.reset()


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
        self.cap: Optional[cv2.VideoCapture] = None
        self.source: Optional[Any] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    def open(self, source: int = 0):
        """Kamera aç"""
        self.source = source
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {source}")
        
        # Kamera ayarları
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info(f"Camera opened: {source}")
    
    def read(self) -> Optional[np.ndarray]:
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
        """
        Kamera stream döngüsü.
        Her frame'i işleyip WebSocket'e gönderir.
        """
        try:
            self.open(source)
            self.is_running = True
            
            # Detector'ı initialize et
            detector.initialize()
            
            frame_interval = 1.0 / fps_limit
            
            while self.is_running:
                start = time.time()
                
                frame = self.read()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Tespit yap
                result = detector.process_frame(frame)
                
                # WebSocket'e gönder
                await manager.broadcast(result.to_dict())
                
                # FPS limiti
                elapsed = time.time() - start
                if elapsed < frame_interval:
                    await asyncio.sleep(frame_interval - elapsed)
                else:
                    await asyncio.sleep(0.001)  # Minimal sleep
                    
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
    return {
        "initialized": detector._initialized,
        "frame_count": detector._frame_count,
        "gallery_size": len(detector.gallery),
        "active_connections": len(manager.active_connections),
        "camera_running": camera_stream.is_running
    }


@router.get("/gallery")
async def get_gallery():
    """Tanınan hayvanlar listesi"""
    return detector.get_gallery_info()


@router.post("/reset")
async def reset_detector():
    """Detector'ı sıfırla"""
    detector.reset()
    return {"status": "ok", "message": "Detector reset"}


@router.post("/start/{camera_id}")
async def start_camera(camera_id: int = 0):
    """Kamera stream'i başlat"""
    if camera_stream.is_running:
        return {"status": "already_running"}
    
    # Background task olarak başlat
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
# HTTP Frame Processing Endpoint (Polling Alternative)
# ===========================================

@router.post("/process-frame")
async def process_frame_http(request_data: dict):
    """
    HTTP üzerinden frame işleme endpoint'i.
    WebSocket alternatifi olarak çalışır.
    
    Request body:
    {
        "frame": "base64 encoded JPEG image",
        "camera_id": 0 (optional)
    }
    
    Returns:
    {
        "success": true,
        "result": DetectionResult
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
        
        # Frame'i işle
        result = detector.process_frame(frame)
        
        if result:
            return {
                "success": True,
                "result": result.to_dict()
            }
        else:
            return {
                "success": True,
                "result": {
                    "frame_id": detector.frame_count,
                    "timestamp": time.time(),
                    "fps": 0,
                    "animal_count": 0,
                    "animals": [],
                    "frame_size": [frame.shape[1], frame.shape[0]]
                }
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
    
    Client'tan gelen komutlar:
    - {"type": "start", "camera": 0} - Kamera başlat
    - {"type": "stop"} - Kamera durdur
    - {"type": "ping"} - Heartbeat
    - {"type": "frame", "data": "base64..."} - Client'tan frame (webcam)
    
    Server'dan gönderilen mesajlar:
    - DetectionResult (her frame için)
    """
    await manager.connect(websocket)
    
    try:
        # Bağlantı durumu
        await websocket.send_json({
            "type": "connected",
            "message": "Detection WebSocket connected",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                # Client'tan mesaj bekle
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
                    # Server kamerasını başlat
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
                    # Stream durdur
                    camera_stream.is_running = False
                    await websocket.send_json({
                        "type": "status",
                        "status": "stopped"
                    })
                
                elif msg_type == "frame":
                    # Client'tan gelen frame (webcam modunda)
                    frame_data = message.get("data", "")
                    if frame_data:
                        # Base64 decode
                        try:
                            # data:image/jpeg;base64, prefix'i varsa kaldır
                            if "," in frame_data:
                                frame_data = frame_data.split(",")[1]
                            
                            img_bytes = base64.b64decode(frame_data)
                            nparr = np.frombuffer(img_bytes, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                # Tespit yap
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
                    # Galeri ve tracker sıfırla
                    detector.reset()
                    await websocket.send_json({
                        "type": "status",
                        "status": "reset",
                        "message": "Detector reset complete"
                    })
                
                elif msg_type == "gallery":
                    # Galeri bilgisi
                    await websocket.send_json({
                        "type": "gallery",
                        **detector.get_gallery_info()
                    })
                
            except asyncio.TimeoutError:
                # Heartbeat gönder
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "gallery_size": len(detector.gallery),
                    "frame_count": detector._frame_count
                })
                
    except WebSocketDisconnect:
        logger.info("Detection WebSocket disconnected")
    except Exception as e:
        logger.error(f"Detection WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


# ===========================================
# Single Frame Analysis
# ===========================================

@router.post("/analyze")
async def analyze_frame(frame_data: dict):
    """
    Tek bir frame analizi.
    
    Request body:
    {
        "frame": "base64 encoded image",
        "format": "jpeg" | "png"
    }
    """
    try:
        frame_b64 = frame_data.get("frame", "")
        
        # data URL prefix varsa kaldır
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        
        img_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Initialize if needed
        if not detector._initialized:
            detector.initialize()
        
        result = detector.process_frame(frame)
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
