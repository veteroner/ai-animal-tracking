"""
AI Animal Tracking System - Farm Monitor
=========================================

Çiftlik kameralarını 7/24 izleyen ve otomatik analiz yapan modül.

Özellikler:
- Çoklu IP kamera desteği
- Otomatik hayvan tespiti ve kaydı
- Kızgınlık tespiti
- Sağlık durumu izleme
- Davranış analizi
- Otomatik alarm oluşturma
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json
from pathlib import Path

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger("animal_tracking.farm_monitor")


class CameraStatus(Enum):
    """Kamera durumu"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"
    PAUSED = "paused"


class AlertType(Enum):
    """Alarm tipleri"""
    NEW_ANIMAL = "new_animal"           # Yeni hayvan tespit edildi
    ANIMAL_MISSING = "animal_missing"   # Hayvan kayıp
    ESTRUS_DETECTED = "estrus_detected" # Kızgınlık tespit edildi
    HEALTH_WARNING = "health_warning"   # Sağlık uyarısı
    BEHAVIOR_ANOMALY = "behavior_anomaly" # Davranış anomalisi
    CAMERA_ERROR = "camera_error"       # Kamera hatası
    BIRTH_DETECTED = "birth_detected"   # Doğum tespit edildi


@dataclass
class FarmCamera:
    """Çiftlik kamerası"""
    id: str
    name: str
    url: str  # RTSP, HTTP veya dosya yolu
    location: str  # Hangi bölgede (ahır, mera, vs)
    farm_id: str
    is_active: bool = True
    status: CameraStatus = CameraStatus.DISCONNECTED
    last_frame_time: Optional[datetime] = None
    fps: float = 0.0
    resolution: tuple = (0, 0)
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "location": self.location,
            "farm_id": self.farm_id,
            "is_active": self.is_active,
            "status": self.status.value,
            "last_frame_time": self.last_frame_time.isoformat() if self.last_frame_time else None,
            "fps": self.fps,
            "resolution": list(self.resolution),
            "error_count": self.error_count,
        }


@dataclass
class FarmAlert:
    """Çiftlik alarmı"""
    id: str
    farm_id: str
    camera_id: str
    alert_type: AlertType
    severity: str  # low, medium, high, critical
    title: str
    message: str
    animal_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "camera_id": self.camera_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "animal_id": self.animal_id,
            "data": self.data,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DetectionStats:
    """Tespit istatistikleri"""
    total_detections: int = 0
    unique_animals: int = 0
    new_animals_today: int = 0
    estrus_detections: int = 0
    health_warnings: int = 0
    behavior_anomalies: int = 0
    last_detection: Optional[datetime] = None


class FarmMonitor:
    """
    Çiftlik İzleme Sistemi
    
    Özellikleri:
    - Çoklu kamera yönetimi
    - Otomatik hayvan tespiti
    - Kızgınlık tespiti
    - Sağlık izleme
    - Davranış analizi
    - Alarm oluşturma
    """
    
    def __init__(
        self,
        farm_id: str,
        detection_interval: float = 1.0,  # Her 1 saniyede bir frame işle
        auto_save: bool = True,
        alert_callback: Optional[Callable[[FarmAlert], None]] = None,
    ):
        self.farm_id = farm_id
        self.detection_interval = detection_interval
        self.auto_save = auto_save
        self.alert_callback = alert_callback
        
        # Kameralar
        self.cameras: Dict[str, FarmCamera] = {}
        self.camera_captures: Dict[str, Any] = {}  # cv2.VideoCapture instances
        
        # İzleme durumu
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Tespit modülleri (lazy loading)
        self._detector = None
        self._tracker = None
        self._behavior_analyzer = None
        self._health_monitor = None
        self._auto_reid = None
        
        # İstatistikler
        self.stats = DetectionStats()
        self.alerts: List[FarmAlert] = []
        
        # Hayvan takibi
        self.tracked_animals: Dict[str, Dict] = {}  # animal_id -> info
        self.last_seen: Dict[str, datetime] = {}  # animal_id -> last seen time
        
        # Kızgınlık tespiti için
        self.activity_history: Dict[str, List[float]] = defaultdict(list)
        self.estrus_candidates: Dict[str, datetime] = {}
        
        logger.info(f"🚜 Farm Monitor başlatıldı: {farm_id}")
    
    def _load_detector(self):
        """Tespit modülünü yükle"""
        if self._detector is None:
            try:
                from src.detection.yolo_detector import YOLODetector
                self._detector = YOLODetector()
                logger.info("✅ YOLO Detector yüklendi")
            except Exception as e:
                logger.error(f"❌ Detector yüklenemedi: {e}")
        return self._detector
    
    def _load_tracker(self):
        """Takip modülünü yükle"""
        if self._tracker is None:
            try:
                from src.tracking.object_tracker import ObjectTracker
                self._tracker = ObjectTracker()
                logger.info("✅ Object Tracker yüklendi")
            except Exception as e:
                logger.error(f"❌ Tracker yüklenemedi: {e}")
        return self._tracker
    
    def _load_behavior_analyzer(self):
        """Davranış analiz modülünü yükle"""
        if self._behavior_analyzer is None:
            try:
                from src.behavior.behavior_analyzer import BehaviorAnalyzer
                self._behavior_analyzer = BehaviorAnalyzer()
                logger.info("✅ Behavior Analyzer yüklendi")
            except Exception as e:
                logger.error(f"❌ Behavior Analyzer yüklenemedi: {e}")
        return self._behavior_analyzer
    
    def _load_health_monitor(self):
        """Sağlık izleme modülünü yükle"""
        if self._health_monitor is None:
            try:
                from src.health.health_monitor import HealthMonitor
                self._health_monitor = HealthMonitor()
                logger.info("✅ Health Monitor yüklendi")
            except Exception as e:
                logger.error(f"❌ Health Monitor yüklenemedi: {e}")
        return self._health_monitor
    
    def _load_auto_reid(self):
        """Otomatik Re-ID modülünü yükle"""
        if self._auto_reid is None:
            try:
                from src.identification.auto_reid import AutoReID, AutoReIDConfig
                config = AutoReIDConfig(
                    similarity_threshold=0.65,
                    new_animal_threshold=0.50,
                    auto_save=True,
                )
                self._auto_reid = AutoReID(config)
                logger.info("✅ Auto Re-ID yüklendi")
            except Exception as e:
                logger.error(f"❌ Auto Re-ID yüklenemedi: {e}")
        return self._auto_reid
    
    # ==========================================
    # Kamera Yönetimi
    # ==========================================
    
    def add_camera(
        self,
        camera_id: str,
        name: str,
        url: str,
        location: str = "unknown",
    ) -> FarmCamera:
        """Kamera ekle"""
        camera = FarmCamera(
            id=camera_id,
            name=name,
            url=url,
            location=location,
            farm_id=self.farm_id,
        )
        self.cameras[camera_id] = camera
        logger.info(f"📷 Kamera eklendi: {name} ({url})")
        return camera
    
    def remove_camera(self, camera_id: str) -> bool:
        """Kamera kaldır"""
        if camera_id in self.cameras:
            # Capture'ı kapat
            if camera_id in self.camera_captures:
                self.camera_captures[camera_id].release()
                del self.camera_captures[camera_id]
            del self.cameras[camera_id]
            logger.info(f"📷 Kamera kaldırıldı: {camera_id}")
            return True
        return False
    
    def connect_camera(self, camera_id: str) -> bool:
        """Kameraya bağlan"""
        if not CV2_AVAILABLE:
            logger.error("OpenCV yüklü değil!")
            return False
        
        camera = self.cameras.get(camera_id)
        if not camera:
            return False
        
        camera.status = CameraStatus.CONNECTING
        
        try:
            # URL'yi ayrıştır
            url = camera.url
            
            # Webcam
            if url.isdigit():
                cap = cv2.VideoCapture(int(url))
            # RTSP veya HTTP stream
            else:
                cap = cv2.VideoCapture(url)
            
            if cap.isOpened():
                # Çözünürlük ve FPS al
                camera.resolution = (
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                )
                camera.fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                camera.status = CameraStatus.CONNECTED
                camera.error_count = 0
                
                self.camera_captures[camera_id] = cap
                logger.info(f"✅ Kamera bağlandı: {camera.name} ({camera.resolution})")
                return True
            else:
                camera.status = CameraStatus.ERROR
                camera.error_count += 1
                logger.error(f"❌ Kamera bağlanamadı: {camera.name}")
                return False
                
        except Exception as e:
            camera.status = CameraStatus.ERROR
            camera.error_count += 1
            logger.error(f"❌ Kamera hatası: {e}")
            return False
    
    def disconnect_camera(self, camera_id: str):
        """Kamera bağlantısını kes"""
        if camera_id in self.camera_captures:
            self.camera_captures[camera_id].release()
            del self.camera_captures[camera_id]
        
        if camera_id in self.cameras:
            self.cameras[camera_id].status = CameraStatus.DISCONNECTED
    
    # ==========================================
    # Frame İşleme
    # ==========================================
    
    def process_frame(self, camera_id: str, frame: np.ndarray) -> Dict[str, Any]:
        """
        Tek bir frame'i işle
        
        Returns:
            {
                "detections": [...],
                "animals": [...],
                "behaviors": [...],
                "health": [...],
                "alerts": [...]
            }
        """
        result = {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "detections": [],
            "animals": [],
            "behaviors": [],
            "health": [],
            "alerts": [],
        }
        
        # 1. Hayvan Tespiti
        detector = self._load_detector()
        if detector:
            detections = detector.detect(frame)
            result["detections"] = [d.to_dict() if hasattr(d, 'to_dict') else d for d in detections]
            self.stats.total_detections += len(detections)
        
        # 2. Takip ve Re-ID
        tracker = self._load_tracker()
        auto_reid = self._load_auto_reid()
        
        if tracker and auto_reid and result["detections"]:
            # Takip et
            tracking_result = tracker.update(result["detections"])
            
            # Re-ID ile hayvanları tanımla
            for track in tracking_result.tracks if hasattr(tracking_result, 'tracks') else []:
                # Crop al
                x1, y1, x2, y2 = map(int, track.bbox)
                crop = frame[y1:y2, x1:x2]
                
                if crop.size > 0:
                    # Re-ID
                    animal_id, confidence, is_new = auto_reid.identify(
                        crop, 
                        track.class_name if hasattr(track, 'class_name') else 'unknown'
                    )
                    
                    animal_info = {
                        "animal_id": animal_id,
                        "track_id": track.track_id,
                        "class_name": track.class_name if hasattr(track, 'class_name') else 'unknown',
                        "bbox": [x1, y1, x2, y2],
                        "confidence": confidence,
                        "is_new": is_new,
                    }
                    result["animals"].append(animal_info)
                    
                    # Yeni hayvan alarmı
                    if is_new:
                        self.stats.new_animals_today += 1
                        self._create_alert(
                            camera_id=camera_id,
                            alert_type=AlertType.NEW_ANIMAL,
                            severity="medium",
                            title="Yeni Hayvan Tespit Edildi",
                            message=f"{animal_id} ID'li yeni bir hayvan sisteme kaydedildi.",
                            animal_id=animal_id,
                        )
                    
                    # Son görülme zamanını güncelle
                    self.last_seen[animal_id] = datetime.now()
                    self.tracked_animals[animal_id] = animal_info
        
        # 3. Davranış Analizi
        behavior_analyzer = self._load_behavior_analyzer()
        if behavior_analyzer and result["animals"]:
            for animal in result["animals"]:
                behavior = behavior_analyzer.analyze_single(
                    animal.get("track_id"),
                    animal.get("bbox"),
                )
                if behavior:
                    behavior_info = {
                        "animal_id": animal.get("animal_id"),
                        "behavior": behavior.behavior_type.value if hasattr(behavior, 'behavior_type') else str(behavior),
                        "confidence": behavior.confidence if hasattr(behavior, 'confidence') else 0.5,
                    }
                    result["behaviors"].append(behavior_info)
                    
                    # Aktivite geçmişine ekle (kızgınlık tespiti için)
                    activity = behavior.activity_level if hasattr(behavior, 'activity_level') else 0.5
                    self.activity_history[animal.get("animal_id")].append(activity)
                    
                    # Son 100 kaydı tut
                    if len(self.activity_history[animal.get("animal_id")]) > 100:
                        self.activity_history[animal.get("animal_id")].pop(0)
        
        # 4. Sağlık Kontrolü
        health_monitor = self._load_health_monitor()
        if health_monitor and result["animals"]:
            for animal in result["animals"]:
                health = health_monitor.check_single(
                    animal.get("track_id"),
                    animal.get("bbox"),
                )
                if health:
                    health_info = {
                        "animal_id": animal.get("animal_id"),
                        "health_score": health.score if hasattr(health, 'score') else 0.8,
                        "status": health.status.value if hasattr(health, 'status') else "healthy",
                        "issues": health.issues if hasattr(health, 'issues') else [],
                    }
                    result["health"].append(health_info)
                    
                    # Sağlık uyarısı
                    if health_info["status"] in ["warning", "critical"]:
                        self.stats.health_warnings += 1
                        self._create_alert(
                            camera_id=camera_id,
                            alert_type=AlertType.HEALTH_WARNING,
                            severity="high" if health_info["status"] == "critical" else "medium",
                            title="Sağlık Uyarısı",
                            message=f"{animal.get('animal_id')} için sağlık uyarısı: {health_info['issues']}",
                            animal_id=animal.get("animal_id"),
                            data=health_info,
                        )
        
        # 5. Kızgınlık Tespiti (aktivite bazlı)
        self._check_estrus_detection(result)
        
        # İstatistikleri güncelle
        self.stats.unique_animals = len(self.tracked_animals)
        self.stats.last_detection = datetime.now()
        
        # Frame işleme zamanını güncelle
        camera = self.cameras.get(camera_id)
        if camera:
            camera.last_frame_time = datetime.now()
            camera.status = CameraStatus.STREAMING
        
        return result
    
    def _check_estrus_detection(self, result: Dict):
        """Kızgınlık tespiti yap"""
        for animal in result.get("animals", []):
            animal_id = animal.get("animal_id")
            if not animal_id:
                continue
            
            history = self.activity_history.get(animal_id, [])
            if len(history) < 20:
                continue
            
            # Son 20 kaydın ortalaması
            recent_avg = np.mean(history[-20:])
            # Genel ortalama
            overall_avg = np.mean(history)
            
            # Aktivite %50'den fazla artmışsa kızgınlık olabilir
            if overall_avg > 0 and recent_avg > overall_avg * 1.5:
                # Daha önce tespit edilmediyse
                if animal_id not in self.estrus_candidates:
                    self.estrus_candidates[animal_id] = datetime.now()
                    self.stats.estrus_detections += 1
                    
                    self._create_alert(
                        camera_id=result.get("camera_id", ""),
                        alert_type=AlertType.ESTRUS_DETECTED,
                        severity="high",
                        title="🔥 Kızgınlık Tespit Edildi!",
                        message=f"{animal_id} için kızgınlık belirtileri tespit edildi. Aktivite seviyesi normalin %{int((recent_avg/overall_avg - 1) * 100)} üzerinde.",
                        animal_id=animal_id,
                        data={
                            "activity_level": recent_avg,
                            "normal_level": overall_avg,
                            "increase_percent": ((recent_avg / overall_avg) - 1) * 100,
                        }
                    )
    
    def _create_alert(
        self,
        camera_id: str,
        alert_type: AlertType,
        severity: str,
        title: str,
        message: str,
        animal_id: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> FarmAlert:
        """Alarm oluştur"""
        alert = FarmAlert(
            id=f"alert_{int(time.time() * 1000)}",
            farm_id=self.farm_id,
            camera_id=camera_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            animal_id=animal_id,
            data=data or {},
        )
        
        self.alerts.append(alert)
        
        # Callback varsa çağır
        if self.alert_callback:
            self.alert_callback(alert)
        
        logger.info(f"🚨 Alarm: {title}")
        return alert
    
    # ==========================================
    # İzleme Döngüsü
    # ==========================================
    
    def start(self):
        """İzlemeyi başlat"""
        if self.is_running:
            logger.warning("Monitor zaten çalışıyor")
            return
        
        # Tüm kameralara bağlan
        for camera_id in self.cameras:
            self.connect_camera(camera_id)
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🟢 Farm Monitor başlatıldı")
    
    def stop(self):
        """İzlemeyi durdur"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Tüm kameraları kapat
        for camera_id in list(self.camera_captures.keys()):
            self.disconnect_camera(camera_id)
        
        logger.info("🔴 Farm Monitor durduruldu")
    
    def _monitor_loop(self):
        """Ana izleme döngüsü"""
        last_process_time = {}
        
        while self.is_running:
            for camera_id, cap in list(self.camera_captures.items()):
                try:
                    # Frame oku
                    ret, frame = cap.read()
                    
                    if not ret:
                        # Bağlantı kopmuş, yeniden bağlan
                        camera = self.cameras.get(camera_id)
                        if camera:
                            camera.error_count += 1
                            if camera.error_count > 10:
                                self._create_alert(
                                    camera_id=camera_id,
                                    alert_type=AlertType.CAMERA_ERROR,
                                    severity="high",
                                    title="Kamera Bağlantı Hatası",
                                    message=f"{camera.name} kamerası ile bağlantı kesildi.",
                                )
                            self.connect_camera(camera_id)
                        continue
                    
                    # İşleme aralığını kontrol et
                    current_time = time.time()
                    last_time = last_process_time.get(camera_id, 0)
                    
                    if current_time - last_time >= self.detection_interval:
                        # Frame'i işle
                        self.process_frame(camera_id, frame)
                        last_process_time[camera_id] = current_time
                
                except Exception as e:
                    logger.error(f"Frame işleme hatası: {e}")
            
            # CPU'yu çok yormamak için kısa bekle
            time.sleep(0.01)
    
    # ==========================================
    # API Metodları
    # ==========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Sistem durumunu döndür"""
        return {
            "farm_id": self.farm_id,
            "is_running": self.is_running,
            "cameras": {cid: cam.to_dict() for cid, cam in self.cameras.items()},
            "stats": {
                "total_detections": self.stats.total_detections,
                "unique_animals": self.stats.unique_animals,
                "new_animals_today": self.stats.new_animals_today,
                "estrus_detections": self.stats.estrus_detections,
                "health_warnings": self.stats.health_warnings,
                "last_detection": self.stats.last_detection.isoformat() if self.stats.last_detection else None,
            },
            "alerts_count": len([a for a in self.alerts if not a.is_read]),
        }
    
    def get_alerts(self, unread_only: bool = False) -> List[Dict]:
        """Alarmları döndür"""
        alerts = self.alerts
        if unread_only:
            alerts = [a for a in alerts if not a.is_read]
        return [a.to_dict() for a in alerts]
    
    def get_animals(self) -> List[Dict]:
        """Takip edilen hayvanları döndür"""
        return list(self.tracked_animals.values())
    
    def get_estrus_candidates(self) -> List[Dict]:
        """Kızgınlık adaylarını döndür"""
        return [
            {
                "animal_id": aid,
                "detected_at": dt.isoformat(),
                "hours_ago": (datetime.now() - dt).total_seconds() / 3600,
            }
            for aid, dt in self.estrus_candidates.items()
        ]


# ==========================================
# Global Instance
# ==========================================

_farm_monitors: Dict[str, FarmMonitor] = {}


def get_farm_monitor(farm_id: str) -> FarmMonitor:
    """Farm monitor instance'ı al veya oluştur"""
    if farm_id not in _farm_monitors:
        _farm_monitors[farm_id] = FarmMonitor(farm_id)
    return _farm_monitors[farm_id]


def list_farm_monitors() -> List[str]:
    """Aktif farm monitor'ları listele"""
    return list(_farm_monitors.keys())
