# src/api/services/tracking_service.py
"""
Tracking Service - Manages real-time animal tracking pipeline.

Singleton service that handles:
- Frame processing pipeline
- Detection and tracking
- Alert generation
- WebSocket broadcasting
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrackingStats:
    """Statistics for tracking service."""
    frames_processed: int = 0
    detections_total: int = 0
    animals_tracked: int = 0
    alerts_generated: int = 0
    avg_fps: float = 0.0
    avg_inference_ms: float = 0.0
    started_at: Optional[str] = None
    last_update: Optional[str] = None


class TrackingService:
    """
    Singleton service for managing the tracking pipeline.
    
    Usage:
        service = TrackingService.get_instance()
        service.start_camera("cam1", 0)
        
        # Get current stats
        stats = service.get_stats()
        
        # Get tracked animals
        animals = service.get_tracked_animals()
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Import modules lazily
        self._detector = None
        self._tracker = None
        self._identifier = None
        self._behavior_analyzer = None
        self._health_monitor = None
        self._alert_manager = None
        
        # Active cameras and their threads
        self._cameras: Dict[str, dict] = {}
        self._camera_threads: Dict[str, threading.Thread] = {}
        
        # Current tracking state
        self._tracked_animals: Dict[str, dict] = {}
        self._stats = TrackingStats()
        
        # Callbacks for WebSocket broadcasting
        self._frame_callbacks: List[Callable] = []
        self._alert_callbacks: List[Callable] = []
        
        # Control
        self._running = False
        
        logger.info("TrackingService initialized")
    
    @classmethod
    def get_instance(cls) -> 'TrackingService':
        """Get singleton instance."""
        return cls()
    
    def _init_modules(self):
        """Initialize AI modules (lazy loading)."""
        if self._detector is not None:
            return
        
        from src.detection import YOLODetector
        from src.tracking import ObjectTracker
        from src.identification import AnimalIdentifier
        from src.behavior import BehaviorAnalyzer
        from src.health import HealthMonitor
        from src.alerts import AlertManager
        
        self._detector = YOLODetector()
        self._tracker = ObjectTracker()
        self._identifier = AnimalIdentifier()
        self._behavior_analyzer = BehaviorAnalyzer()
        self._health_monitor = HealthMonitor()
        self._alert_manager = AlertManager()
        
        logger.info("AI modules loaded")
    
    def start_camera(self, camera_id: str, source: Any) -> bool:
        """Start processing for a camera."""
        if camera_id in self._cameras:
            logger.warning(f"Camera {camera_id} already running")
            return False
        
        self._init_modules()
        
        self._cameras[camera_id] = {
            "source": source,
            "running": True,
            "frame_count": 0,
            "started_at": datetime.now().isoformat()
        }
        
        # Start processing thread
        thread = threading.Thread(
            target=self._camera_loop,
            args=(camera_id, source),
            daemon=True
        )
        thread.start()
        self._camera_threads[camera_id] = thread
        
        if not self._running:
            self._running = True
            self._stats.started_at = datetime.now().isoformat()
        
        logger.info(f"Started camera {camera_id} with source {source}")
        return True
    
    def stop_camera(self, camera_id: str) -> bool:
        """Stop processing for a camera."""
        if camera_id not in self._cameras:
            return False
        
        self._cameras[camera_id]["running"] = False
        
        # Wait for thread to finish
        if camera_id in self._camera_threads:
            self._camera_threads[camera_id].join(timeout=2.0)
            del self._camera_threads[camera_id]
        
        del self._cameras[camera_id]
        
        logger.info(f"Stopped camera {camera_id}")
        return True
    
    def stop_all(self):
        """Stop all cameras."""
        camera_ids = list(self._cameras.keys())
        for cam_id in camera_ids:
            self.stop_camera(cam_id)
        self._running = False
    
    def _camera_loop(self, camera_id: str, source: Any):
        """Main processing loop for a camera."""
        from src.camera import VideoCapture
        
        cap = VideoCapture(source)
        
        try:
            cap.start()
            fps_counter = []
            
            while self._cameras.get(camera_id, {}).get("running", False):
                start_time = time.time()
                
                frame = cap.read()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Process frame
                result = self._process_frame(camera_id, frame)
                
                # Update stats
                self._cameras[camera_id]["frame_count"] += 1
                self._stats.frames_processed += 1
                
                # FPS calculation
                elapsed = time.time() - start_time
                fps_counter.append(1.0 / max(elapsed, 0.001))
                if len(fps_counter) > 30:
                    fps_counter.pop(0)
                self._stats.avg_fps = sum(fps_counter) / len(fps_counter)
                
                # Notify callbacks
                for callback in self._frame_callbacks:
                    try:
                        callback(camera_id, frame, result)
                    except Exception as e:
                        logger.error(f"Frame callback error: {e}")
                
                # Rate limiting
                target_fps = 30
                sleep_time = max(0, (1.0 / target_fps) - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            logger.error(f"Camera loop error for {camera_id}: {e}")
        finally:
            cap.stop()
    
    def _process_frame(self, camera_id: str, frame: np.ndarray) -> dict:
        """Process a single frame through the pipeline."""
        result = {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "detections": [],
            "tracks": [],
            "behaviors": [],
            "alerts": []
        }
        
        # Detection
        detection_result = self._detector.detect(frame)
        self._stats.avg_inference_ms = (
            self._stats.avg_inference_ms * 0.9 + 
            detection_result.inference_time * 0.1
        )
        
        # Tracking
        tracking_result = self._tracker.update(detection_result)
        self._stats.detections_total += detection_result.count
        
        # Process each track
        for track in tracking_result.tracks:
            if not track.is_confirmed:
                continue
            
            # Identification
            animal_id = self._identifier.identify(
                track,
                frame,
                camera_id
            )
            
            # Behavior analysis
            behavior = self._behavior_analyzer.analyze(track, frame)
            
            # Health monitoring
            health = self._health_monitor.update(track, behavior)
            
            # Update tracked animals
            self._update_tracked_animal(
                animal_id, track, behavior, health, camera_id
            )
            
            # Add to result
            result["tracks"].append({
                "track_id": track.track_id,
                "animal_id": animal_id,
                "bbox": track.bbox,
                "class_name": track.class_name,
                "confidence": track.confidence
            })
            
            if behavior:
                result["behaviors"].append({
                    "animal_id": animal_id,
                    "behavior": behavior.behavior.value,
                    "confidence": behavior.confidence
                })
            
            # Check for alerts
            self._check_alerts(animal_id, health, behavior, camera_id, result)
        
        self._stats.animals_tracked = len(self._tracked_animals)
        self._stats.last_update = datetime.now().isoformat()
        
        return result
    
    def _update_tracked_animal(
        self,
        animal_id: str,
        track,
        behavior,
        health,
        camera_id: str
    ):
        """Update tracked animal information."""
        if animal_id not in self._tracked_animals:
            self._tracked_animals[animal_id] = {
                "id": animal_id,
                "first_seen": datetime.now().isoformat(),
                "species": track.class_name
            }
        
        animal = self._tracked_animals[animal_id]
        animal.update({
            "last_seen": datetime.now().isoformat(),
            "camera_id": camera_id,
            "bbox": track.bbox,
            "center": track.center,
            "behavior": behavior.behavior.value if behavior else "unknown",
            "health_status": health.overall_status.value if health else "unknown",
            "confidence": track.confidence
        })
    
    def _check_alerts(
        self,
        animal_id: str,
        health,
        behavior,
        camera_id: str,
        result: dict
    ):
        """Check and generate alerts."""
        if health:
            # Health alerts
            alert = self._alert_manager.check_health_alert(
                animal_id,
                health.overall_score if hasattr(health, 'overall_score') else 70,
                camera_id
            )
            if alert:
                result["alerts"].append(alert.to_dict())
                self._stats.alerts_generated += 1
                self._notify_alert(alert)
    
    def _notify_alert(self, alert):
        """Notify alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    # Public API
    
    def add_frame_callback(self, callback: Callable):
        """Add callback for processed frames."""
        self._frame_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts."""
        self._alert_callbacks.append(callback)
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "frames_processed": self._stats.frames_processed,
            "detections_total": self._stats.detections_total,
            "animals_tracked": self._stats.animals_tracked,
            "alerts_generated": self._stats.alerts_generated,
            "avg_fps": round(self._stats.avg_fps, 1),
            "avg_inference_ms": round(self._stats.avg_inference_ms, 1),
            "started_at": self._stats.started_at,
            "last_update": self._stats.last_update,
            "active_cameras": list(self._cameras.keys())
        }
    
    def get_tracked_animals(self) -> List[dict]:
        """Get list of currently tracked animals."""
        return list(self._tracked_animals.values())
    
    def get_animal(self, animal_id: str) -> Optional[dict]:
        """Get specific animal by ID."""
        return self._tracked_animals.get(animal_id)
    
    def get_active_cameras(self) -> List[str]:
        """Get list of active camera IDs."""
        return list(self._cameras.keys())
    
    def is_camera_active(self, camera_id: str) -> bool:
        """Check if camera is active."""
        return camera_id in self._cameras
