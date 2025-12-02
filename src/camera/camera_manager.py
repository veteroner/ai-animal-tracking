"""
AI Animal Tracking System - Camera Manager
==========================================

Çoklu kamera yönetimi.
"""

import threading
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

import yaml
import numpy as np

from src.camera.video_capture import VideoCapture, CameraState, CameraType, FrameInfo


logger = logging.getLogger("animal_tracking.camera")


@dataclass
class CameraInfo:
    """Kamera bilgileri"""
    id: str
    name: str
    source: Any
    type: CameraType
    state: CameraState
    resolution: tuple
    fps: float
    statistics: dict = field(default_factory=dict)


class CameraManager:
    """
    Çoklu kamera yönetici sınıfı.
    
    Birden fazla kamerayı aynı anda yönetir, frame'leri senkronize eder
    ve merkezi erişim sağlar.
    
    Kullanım:
        manager = CameraManager()
        manager.add_camera("cam1", source=0, name="Webcam")
        manager.add_camera("cam2", source="rtsp://...", name="IP Camera")
        manager.start_all()
        
        frame = manager.get_frame("cam1")
        
        manager.stop_all()
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        on_frame_callback: Optional[Callable[[str, FrameInfo], None]] = None,
    ):
        """
        Args:
            config_path: Kamera konfigürasyon dosyası yolu
            on_frame_callback: Her frame'de çağrılacak fonksiyon (camera_id, frame_info)
        """
        self._cameras: Dict[str, VideoCapture] = {}
        self._lock = threading.RLock()
        self._on_frame_callback = on_frame_callback
        
        # Config dosyasından yükle
        if config_path:
            self.load_config(config_path)
    
    @property
    def camera_ids(self) -> List[str]:
        """Kamera ID listesi"""
        with self._lock:
            return list(self._cameras.keys())
    
    @property
    def camera_count(self) -> int:
        """Kamera sayısı"""
        return len(self._cameras)
    
    @property
    def active_cameras(self) -> List[str]:
        """Aktif (streaming) kamera ID'leri"""
        with self._lock:
            return [
                cam_id for cam_id, cam in self._cameras.items()
                if cam.is_streaming
            ]
    
    def load_config(self, config_path: str) -> bool:
        """
        Konfigürasyon dosyasından kameraları yükle.
        
        Args:
            config_path: YAML config dosya yolu
            
        Returns:
            Başarılı ise True
        """
        try:
            config_path = Path(config_path)
            if not config_path.exists():
                logger.error(f"Config file not found: {config_path}")
                return False
            
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if not config or "cameras" not in config:
                logger.warning("No cameras defined in config")
                return True
            
            # Varsayılan ayarlar
            defaults = config.get("defaults", {})
            default_resolution = defaults.get("resolution", {})
            default_width = default_resolution.get("width", 1280)
            default_height = default_resolution.get("height", 720)
            default_fps = defaults.get("fps", 30)
            
            # Kameraları ekle
            for cam_config in config["cameras"]:
                if not cam_config.get("enabled", True):
                    continue
                
                cam_id = cam_config.get("id")
                if not cam_id:
                    continue
                
                resolution = cam_config.get("resolution", {})
                
                self.add_camera(
                    camera_id=cam_id,
                    source=cam_config.get("source", 0),
                    name=cam_config.get("name", cam_id),
                    width=resolution.get("width", default_width),
                    height=resolution.get("height", default_height),
                    fps=cam_config.get("fps", default_fps),
                )
            
            logger.info(f"Loaded {self.camera_count} cameras from config")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def add_camera(
        self,
        camera_id: str,
        source: Any,
        name: Optional[str] = None,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        auto_start: bool = False,
    ) -> bool:
        """
        Kamera ekle.
        
        Args:
            camera_id: Benzersiz kamera ID'si
            source: Kamera kaynağı
            name: Kamera ismi
            width: İstenen genişlik
            height: İstenen yükseklik
            fps: İstenen FPS
            auto_start: Hemen başlat
            
        Returns:
            Başarılı ise True
        """
        with self._lock:
            if camera_id in self._cameras:
                logger.warning(f"Camera {camera_id} already exists")
                return False
            
            # Callback wrapper
            def frame_callback(frame_info: FrameInfo):
                if self._on_frame_callback:
                    self._on_frame_callback(camera_id, frame_info)
            
            # VideoCapture oluştur
            camera = VideoCapture(
                source=source,
                name=name or camera_id,
                width=width,
                height=height,
                fps=fps,
                on_frame_callback=frame_callback if self._on_frame_callback else None,
            )
            
            self._cameras[camera_id] = camera
            logger.info(f"Added camera: {camera_id} ({source})")
            
            if auto_start:
                return camera.start()
            
            return True
    
    def remove_camera(self, camera_id: str) -> bool:
        """
        Kamerayı kaldır.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            Başarılı ise True
        """
        with self._lock:
            if camera_id not in self._cameras:
                logger.warning(f"Camera {camera_id} not found")
                return False
            
            camera = self._cameras[camera_id]
            camera.stop()
            del self._cameras[camera_id]
            
            logger.info(f"Removed camera: {camera_id}")
            return True
    
    def get_camera(self, camera_id: str) -> Optional[VideoCapture]:
        """
        Kamera nesnesini al.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            VideoCapture veya None
        """
        with self._lock:
            return self._cameras.get(camera_id)
    
    def get_camera_info(self, camera_id: str) -> Optional[CameraInfo]:
        """
        Kamera bilgilerini al.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            CameraInfo veya None
        """
        with self._lock:
            camera = self._cameras.get(camera_id)
            if camera is None:
                return None
            
            return CameraInfo(
                id=camera_id,
                name=camera.config.name,
                source=camera.config.source,
                type=camera.camera_type,
                state=camera.state,
                resolution=camera.frame_size,
                fps=camera.fps,
                statistics=camera.statistics,
            )
    
    def get_all_camera_info(self) -> List[CameraInfo]:
        """Tüm kameraların bilgilerini al"""
        return [
            self.get_camera_info(cam_id)
            for cam_id in self.camera_ids
        ]
    
    def start_camera(self, camera_id: str) -> bool:
        """
        Tek bir kamerayı başlat.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            Başarılı ise True
        """
        camera = self.get_camera(camera_id)
        if camera is None:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        return camera.start()
    
    def stop_camera(self, camera_id: str) -> bool:
        """
        Tek bir kamerayı durdur.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            Başarılı ise True
        """
        camera = self.get_camera(camera_id)
        if camera is None:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        camera.stop()
        return True
    
    def start_all(self) -> Dict[str, bool]:
        """
        Tüm kameraları başlat.
        
        Returns:
            {camera_id: success} dictionary
        """
        results = {}
        for camera_id in self.camera_ids:
            results[camera_id] = self.start_camera(camera_id)
        return results
    
    def stop_all(self):
        """Tüm kameraları durdur"""
        for camera_id in self.camera_ids:
            self.stop_camera(camera_id)
        logger.info("All cameras stopped")
    
    def get_frame(self, camera_id: str) -> Optional[FrameInfo]:
        """
        Kameradan frame al.
        
        Args:
            camera_id: Kamera ID'si
            
        Returns:
            FrameInfo veya None
        """
        camera = self.get_camera(camera_id)
        if camera is None:
            return None
        return camera.read()
    
    def get_all_frames(self) -> Dict[str, Optional[FrameInfo]]:
        """
        Tüm kameralardan frame al.
        
        Returns:
            {camera_id: FrameInfo} dictionary
        """
        return {
            cam_id: self.get_frame(cam_id)
            for cam_id in self.camera_ids
        }
    
    def __enter__(self):
        """Context manager enter"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_all()
    
    def __del__(self):
        """Destructor"""
        self.stop_all()


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import sys
    import cv2
    
    logging.basicConfig(level=logging.INFO)
    
    # Frame callback
    def on_frame(camera_id: str, frame_info: FrameInfo):
        print(f"\r{camera_id}: Frame {frame_info.frame_id}, FPS: {frame_info.fps:.1f}", end="")
    
    # Manager oluştur
    manager = CameraManager(on_frame_callback=on_frame)
    
    # Kamera ekle
    source = 0
    if len(sys.argv) > 1:
        source = sys.argv[1]
        if source.isdigit():
            source = int(source)
    
    manager.add_camera("cam1", source=source, name="Test Camera")
    
    # Başlat
    manager.start_all()
    
    print("\nPress 'q' to quit")
    
    try:
        while True:
            frame_info = manager.get_frame("cam1")
            
            if frame_info is not None:
                cv2.imshow("Camera Manager Test", frame_info.frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        manager.stop_all()
        cv2.destroyAllWindows()
