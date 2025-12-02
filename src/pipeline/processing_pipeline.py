"""
AI Animal Tracking System - Processing Pipeline
===============================================

Tüm modülleri birleştiren ana işleme pipeline'ı.
Video akışından tespit, takip, tanımlama, davranış ve sağlık analizine.
"""

import time
import logging
import threading
from queue import Queue, Empty
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

import numpy as np
import cv2

from src.camera import CameraManager, FrameInfo
from src.detection import YOLODetector, DetectionResult
from src.tracking import ObjectTracker, TrackingResult
from src.identification import AnimalIdentifier, IdentificationResult
from src.behavior import BehaviorAnalyzer, BehaviorAnalysisResult
from src.health import HealthMonitor, HealthMetrics


logger = logging.getLogger("animal_tracking.pipeline")


# ===========================================
# Pipeline State
# ===========================================

class PipelineState(Enum):
    """Pipeline durumu"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


# ===========================================
# Data Classes
# ===========================================

@dataclass
class PipelineConfig:
    """Pipeline konfigürasyonu"""
    # Model
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    only_animals: bool = True
    
    # Tracking
    enable_tracking: bool = True
    tracker_type: str = "bytetrack"
    
    # Identification
    enable_identification: bool = True
    
    # Behavior
    enable_behavior: bool = True
    
    # Health
    enable_health: bool = True
    
    # Processing
    process_every_n_frames: int = 1  # Her N frame'de bir işle
    max_queue_size: int = 30
    
    # Output
    draw_detections: bool = True
    draw_trajectories: bool = True
    draw_info: bool = True
    
    # Database
    save_to_db: bool = False
    db_url: str = "sqlite:///data/animal_tracking.db"


@dataclass
class FrameResult:
    """Tek bir frame'in işleme sonucu"""
    frame_id: int
    timestamp: float
    camera_id: str
    
    # Orijinal frame
    frame: np.ndarray
    
    # İşlenmiş frame (çizimler ile)
    processed_frame: Optional[np.ndarray] = None
    
    # Sonuçlar
    detection_result: Optional[DetectionResult] = None
    tracking_result: Optional[TrackingResult] = None
    identifications: List[IdentificationResult] = field(default_factory=list)
    behaviors: List[BehaviorAnalysisResult] = field(default_factory=list)
    health_metrics: List[HealthMetrics] = field(default_factory=list)
    
    # Performans
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "camera_id": self.camera_id,
            "detection_count": self.detection_result.count if self.detection_result else 0,
            "track_count": self.tracking_result.count if self.tracking_result else 0,
            "processing_time_ms": round(self.processing_time_ms, 2),
        }


@dataclass
class PipelineStats:
    """Pipeline istatistikleri"""
    session_id: str = ""
    started_at: Optional[datetime] = None
    
    # Sayaçlar
    total_frames: int = 0
    processed_frames: int = 0
    total_detections: int = 0
    total_animals: int = 0
    
    # Performans
    avg_fps: float = 0.0
    avg_processing_time_ms: float = 0.0
    
    # Son değerler
    last_fps: float = 0.0
    last_processing_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "total_detections": self.total_detections,
            "total_animals": self.total_animals,
            "avg_fps": round(self.avg_fps, 2),
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 2),
            "last_fps": round(self.last_fps, 2),
        }


# ===========================================
# Processing Pipeline
# ===========================================

class ProcessingPipeline:
    """
    Ana işleme pipeline'ı.
    
    Akış:
    1. Video frame al (CameraManager)
    2. YOLO ile tespit (YOLODetector)
    3. Object tracking (ObjectTracker)
    4. Hayvan tanımlama (AnimalIdentifier)
    5. Davranış analizi (BehaviorAnalyzer)
    6. Sağlık izleme (HealthMonitor)
    7. Sonuçları çiz ve döndür
    
    Kullanım:
        pipeline = ProcessingPipeline()
        pipeline.add_camera("cam1", source=0)
        pipeline.start()
        
        while pipeline.is_running:
            result = pipeline.get_result()
            if result:
                cv2.imshow("Output", result.processed_frame)
        
        pipeline.stop()
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Args:
            config: Pipeline konfigürasyonu
        """
        self.config = config or PipelineConfig()
        
        # State
        self._state = PipelineState.IDLE
        self._lock = threading.RLock()
        
        # Session
        self._session_id = ""
        self._stats = PipelineStats()
        
        # Bileşenler (lazy init)
        self._camera_manager: Optional[CameraManager] = None
        self._detector: Optional[YOLODetector] = None
        self._tracker: Optional[ObjectTracker] = None
        self._identifier: Optional[AnimalIdentifier] = None
        self._behavior_analyzer: Optional[BehaviorAnalyzer] = None
        self._health_monitor: Optional[HealthMonitor] = None
        
        # Threading
        self._processing_thread: Optional[threading.Thread] = None
        self._result_queue: Queue = Queue(maxsize=self.config.max_queue_size)
        self._stop_event = threading.Event()
        
        # Callbacks
        self._on_result_callbacks: List[Callable[[FrameResult], None]] = []
        self._on_alert_callbacks: List[Callable[[dict], None]] = []
        
        # Frame counter
        self._frame_counter = 0
        self._fps_counter = 0
        self._fps_time = time.time()
    
    # ===========================================
    # Properties
    # ===========================================
    
    @property
    def state(self) -> PipelineState:
        return self._state
    
    @property
    def is_running(self) -> bool:
        return self._state == PipelineState.RUNNING
    
    @property
    def stats(self) -> PipelineStats:
        return self._stats
    
    @property
    def camera_manager(self) -> CameraManager:
        if self._camera_manager is None:
            self._camera_manager = CameraManager()
        return self._camera_manager
    
    @property
    def detector(self) -> YOLODetector:
        if self._detector is None:
            self._detector = YOLODetector(
                model_path=self.config.model_path,
                confidence_threshold=self.config.confidence_threshold,
                only_animals=self.config.only_animals,
            )
        return self._detector
    
    @property
    def tracker(self) -> ObjectTracker:
        if self._tracker is None:
            self._tracker = ObjectTracker()
        return self._tracker
    
    @property
    def identifier(self) -> AnimalIdentifier:
        if self._identifier is None:
            self._identifier = AnimalIdentifier()
        return self._identifier
    
    @property
    def behavior_analyzer(self) -> BehaviorAnalyzer:
        if self._behavior_analyzer is None:
            self._behavior_analyzer = BehaviorAnalyzer()
        return self._behavior_analyzer
    
    @property
    def health_monitor(self) -> HealthMonitor:
        if self._health_monitor is None:
            self._health_monitor = HealthMonitor()
        return self._health_monitor
    
    # ===========================================
    # Camera Management
    # ===========================================
    
    def add_camera(
        self,
        camera_id: str,
        source: Any,
        name: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Kamera ekle"""
        return self.camera_manager.add_camera(
            camera_id=camera_id,
            source=source,
            name=name,
            **kwargs
        )
    
    def remove_camera(self, camera_id: str) -> bool:
        """Kamera kaldır"""
        return self.camera_manager.remove_camera(camera_id)
    
    # ===========================================
    # Callbacks
    # ===========================================
    
    def on_result(self, callback: Callable[[FrameResult], None]):
        """Sonuç callback'i ekle"""
        self._on_result_callbacks.append(callback)
    
    def on_alert(self, callback: Callable[[dict], None]):
        """Uyarı callback'i ekle"""
        self._on_alert_callbacks.append(callback)
    
    # ===========================================
    # Pipeline Control
    # ===========================================
    
    def start(self) -> bool:
        """Pipeline'ı başlat"""
        with self._lock:
            if self._state == PipelineState.RUNNING:
                logger.warning("Pipeline is already running")
                return False
            
            if self.camera_manager.camera_count == 0:
                logger.error("No cameras added")
                return False
            
            self._state = PipelineState.STARTING
            
            # Session başlat
            self._session_id = str(uuid.uuid4())[:8]
            self._stats = PipelineStats(
                session_id=self._session_id,
                started_at=datetime.now(),
            )
            
            # Reset
            self._stop_event.clear()
            self._frame_counter = 0
            
            # Detector warmup
            logger.info("Warming up detector...")
            self.detector.warmup()
            
            # Kameraları başlat
            logger.info("Starting cameras...")
            results = self.camera_manager.start_all()
            
            if not any(results.values()):
                logger.error("Failed to start any camera")
                self._state = PipelineState.ERROR
                return False
            
            # Processing thread başlat
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True,
            )
            self._processing_thread.start()
            
            self._state = PipelineState.RUNNING
            logger.info(f"Pipeline started (session: {self._session_id})")
            
            return True
    
    def stop(self):
        """Pipeline'ı durdur"""
        with self._lock:
            if self._state not in [PipelineState.RUNNING, PipelineState.PAUSED]:
                return
            
            self._state = PipelineState.STOPPING
            logger.info("Stopping pipeline...")
            
            # Thread'i durdur
            self._stop_event.set()
            
            if self._processing_thread:
                self._processing_thread.join(timeout=5.0)
            
            # Kameraları durdur
            self.camera_manager.stop_all()
            
            self._state = PipelineState.STOPPED
            logger.info("Pipeline stopped")
    
    def pause(self):
        """Pipeline'ı duraklat"""
        with self._lock:
            if self._state == PipelineState.RUNNING:
                self._state = PipelineState.PAUSED
                logger.info("Pipeline paused")
    
    def resume(self):
        """Pipeline'ı devam ettir"""
        with self._lock:
            if self._state == PipelineState.PAUSED:
                self._state = PipelineState.RUNNING
                logger.info("Pipeline resumed")
    
    # ===========================================
    # Processing Loop
    # ===========================================
    
    def _processing_loop(self):
        """Ana işleme döngüsü"""
        logger.info("Processing loop started")
        
        while not self._stop_event.is_set():
            if self._state == PipelineState.PAUSED:
                time.sleep(0.1)
                continue
            
            try:
                # Tüm kameralardan frame al
                frames = self.camera_manager.get_all_frames()
                
                for camera_id, frame_info in frames.items():
                    if frame_info is None:
                        continue
                    
                    self._frame_counter += 1
                    
                    # N frame'de bir işle
                    if self._frame_counter % self.config.process_every_n_frames != 0:
                        continue
                    
                    # Frame'i işle
                    result = self._process_frame(camera_id, frame_info)
                    
                    if result:
                        # Queue'ya ekle
                        try:
                            self._result_queue.put_nowait(result)
                        except:
                            # Queue dolu, eski frame'i at
                            try:
                                self._result_queue.get_nowait()
                                self._result_queue.put_nowait(result)
                            except:
                                pass
                        
                        # Callbacks
                        for callback in self._on_result_callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                
            except Exception as e:
                logger.error(f"Processing error: {e}")
                time.sleep(0.1)
        
        logger.info("Processing loop ended")
    
    def _process_frame(self, camera_id: str, frame_info: FrameInfo) -> Optional[FrameResult]:
        """Tek bir frame'i işle"""
        start_time = time.time()
        
        frame = frame_info.frame
        if frame is None:
            return None
        
        # Sonuç nesnesi
        result = FrameResult(
            frame_id=frame_info.frame_id,
            timestamp=frame_info.timestamp,
            camera_id=camera_id,
            frame=frame.copy(),
        )
        
        # 1. Detection + Tracking
        if self.config.enable_tracking:
            detection_result = self.detector.track(frame, tracker=self.config.tracker_type)
        else:
            detection_result = self.detector.detect(frame)
        
        result.detection_result = detection_result
        self._stats.total_detections += detection_result.count
        
        # 2. Object Tracking update
        if self.config.enable_tracking:
            tracking_result = self.tracker.update(detection_result)
            result.tracking_result = tracking_result
        
        # 3. Identification
        if self.config.enable_identification and tracking_result:
            for track in tracking_result.tracks:
                id_result = self.identifier.identify(frame, track)
                result.identifications.append(id_result)
                
                if id_result.is_new:
                    self._stats.total_animals += 1
        
        # 4. Behavior Analysis
        if self.config.enable_behavior and tracking_result:
            for track in tracking_result.tracks:
                behavior_result = self.behavior_analyzer.analyze(track)
                result.behaviors.append(behavior_result)
        
        # 5. Health Monitoring
        if self.config.enable_health and tracking_result:
            for i, track in enumerate(tracking_result.tracks):
                behavior = result.behaviors[i] if i < len(result.behaviors) else None
                animal_id = result.identifications[i].animal_id if i < len(result.identifications) else None
                
                health = self.health_monitor.update(track, behavior, animal_id)
                result.health_metrics.append(health)
                
                # Alert callbacks
                if health.alerts:
                    for alert in health.alerts:
                        for callback in self._on_alert_callbacks:
                            try:
                                callback(alert.to_dict())
                            except:
                                pass
        
        # 6. Draw output
        if self.config.draw_detections:
            result.processed_frame = self._draw_output(frame, result)
        else:
            result.processed_frame = frame
        
        # Stats güncelle
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        self._stats.processed_frames += 1
        self._stats.last_processing_time_ms = processing_time
        self._update_fps()
        
        return result
    
    def _draw_output(self, frame: np.ndarray, result: FrameResult) -> np.ndarray:
        """Sonuçları frame üzerine çiz"""
        output = frame.copy()
        
        # Detections
        if result.detection_result:
            output = self.detector.draw_detections(
                output,
                result.detection_result,
                show_labels=True,
                show_confidence=True,
                show_track_id=True,
            )
        
        # Trajectories
        if self.config.draw_trajectories and result.tracking_result:
            for track in result.tracking_result.tracks:
                if len(track.history) > 1:
                    points = np.array(track.history[-50:], dtype=np.int32)
                    cv2.polylines(output, [points], False, (0, 255, 255), 2)
        
        # Behavior & Health labels
        for i, (behavior, health) in enumerate(zip(result.behaviors, result.health_metrics)):
            if i < len(result.tracking_result.tracks if result.tracking_result else []):
                track = result.tracking_result.tracks[i]
                x1, y1, x2, y2 = track.bbox
                
                # Behavior
                behavior_text = behavior.behavior.value
                cv2.putText(output, behavior_text, (x1, y2 + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Health status
                status_color = {
                    "healthy": (0, 255, 0),
                    "attention": (0, 255, 255),
                    "warning": (0, 165, 255),
                    "critical": (0, 0, 255),
                }.get(health.overall_status.value, (128, 128, 128))
                
                cv2.circle(output, (x2 - 10, y1 + 10), 5, status_color, -1)
        
        # Info panel
        if self.config.draw_info:
            self._draw_info_panel(output, result)
        
        return output
    
    def _draw_info_panel(self, frame: np.ndarray, result: FrameResult):
        """Bilgi paneli çiz"""
        h, w = frame.shape[:2]
        
        # Background
        cv2.rectangle(frame, (10, 10), (250, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (250, 100), (100, 100, 100), 1)
        
        # Text
        fps = self._stats.last_fps
        det_count = result.detection_result.count if result.detection_result else 0
        track_count = result.tracking_result.count if result.tracking_result else 0
        
        lines = [
            f"FPS: {fps:.1f}",
            f"Detections: {det_count}",
            f"Tracks: {track_count}",
            f"Animals: {self._stats.total_animals}",
        ]
        
        y = 30
        for line in lines:
            cv2.putText(frame, line, (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            y += 18
    
    def _update_fps(self):
        """FPS hesapla"""
        self._fps_counter += 1
        elapsed = time.time() - self._fps_time
        
        if elapsed >= 1.0:
            self._stats.last_fps = self._fps_counter / elapsed
            self._fps_counter = 0
            self._fps_time = time.time()
            
            # Ortalama FPS
            if self._stats.processed_frames > 0:
                total_time = (datetime.now() - self._stats.started_at).total_seconds()
                self._stats.avg_fps = self._stats.processed_frames / total_time if total_time > 0 else 0
    
    # ===========================================
    # Result Access
    # ===========================================
    
    def get_result(self, timeout: float = 0.1) -> Optional[FrameResult]:
        """
        Son işlenen frame sonucunu al.
        
        Args:
            timeout: Bekleme süresi
            
        Returns:
            FrameResult veya None
        """
        try:
            return self._result_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_latest_result(self) -> Optional[FrameResult]:
        """Queue'daki en son sonucu al (diğerlerini at)"""
        result = None
        while True:
            try:
                result = self._result_queue.get_nowait()
            except Empty:
                break
        return result
    
    # ===========================================
    # Reset
    # ===========================================
    
    def reset(self):
        """Pipeline'ı sıfırla"""
        if self.is_running:
            self.stop()
        
        self._tracker.reset()
        self._identifier.reset()
        self._behavior_analyzer.reset()
        self._health_monitor.reset()
        self._detector.reset_tracker()
        
        self._stats = PipelineStats()
        self._frame_counter = 0
        
        logger.info("Pipeline reset")
    
    # ===========================================
    # Context Manager
    # ===========================================
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Pipeline oluştur
    config = PipelineConfig(
        model_path="yolov8n.pt",
        only_animals=False,  # Test için tüm nesneler
        enable_tracking=True,
        enable_identification=True,
        enable_behavior=True,
        enable_health=True,
    )
    
    pipeline = ProcessingPipeline(config)
    
    # Webcam ekle
    source = 0
    if len(sys.argv) > 1:
        source = sys.argv[1]
        if source.isdigit():
            source = int(source)
    
    pipeline.add_camera("cam1", source=source, name="Test Camera")
    
    # Callbacks
    def on_alert(alert):
        print(f"🚨 ALERT: {alert['message']}")
    
    pipeline.on_alert(on_alert)
    
    # Başlat
    if not pipeline.start():
        print("Failed to start pipeline")
        sys.exit(1)
    
    print("\nPipeline running. Press 'q' to quit.")
    
    try:
        while pipeline.is_running:
            result = pipeline.get_result()
            
            if result and result.processed_frame is not None:
                cv2.imshow("AI Animal Tracking Pipeline", result.processed_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                pipeline.reset()
                pipeline.start()
    
    except KeyboardInterrupt:
        pass
    
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        
        print("\n" + "="*50)
        print("Pipeline Statistics")
        print("="*50)
        for k, v in pipeline.stats.to_dict().items():
            print(f"{k}: {v}")
