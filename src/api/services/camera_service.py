# src/api/services/camera_service.py
"""
Camera Service - Manages camera connections and streams.
"""

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CameraService:
    """
    Singleton service for managing cameras.
    
    Usage:
        service = CameraService.get_instance()
        service.add_camera("cam1", "rtsp://...")
        service.start_camera("cam1")
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._cameras: Dict[str, dict] = {}
        self._captures: Dict[str, Any] = {}
        
        logger.info("CameraService initialized")
    
    @classmethod
    def get_instance(cls) -> 'CameraService':
        """Get singleton instance."""
        return cls()
    
    def add_camera(
        self,
        camera_id: str,
        source: Any,
        name: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Add a new camera."""
        if camera_id in self._cameras:
            raise ValueError(f"Camera {camera_id} already exists")
        
        camera = {
            "id": camera_id,
            "name": name or camera_id,
            "source": source,
            "status": "stopped",
            "is_streaming": False,
            "fps": kwargs.get("fps", 30),
            "resolution": kwargs.get("resolution"),
            "created_at": datetime.now().isoformat(),
            "last_frame_at": None,
            "frame_count": 0,
            "error": None
        }
        
        self._cameras[camera_id] = camera
        logger.info(f"Camera added: {camera_id}")
        
        return camera
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera."""
        if camera_id not in self._cameras:
            return False
        
        # Stop if streaming
        if self._cameras[camera_id]["is_streaming"]:
            self.stop_camera(camera_id)
        
        del self._cameras[camera_id]
        
        if camera_id in self._captures:
            del self._captures[camera_id]
        
        logger.info(f"Camera removed: {camera_id}")
        return True
    
    def get_camera(self, camera_id: str) -> Optional[dict]:
        """Get camera by ID."""
        return self._cameras.get(camera_id)
    
    def get_cameras(self) -> List[dict]:
        """Get all cameras."""
        return list(self._cameras.values())
    
    def start_camera(self, camera_id: str) -> bool:
        """Start camera streaming."""
        if camera_id not in self._cameras:
            return False
        
        camera = self._cameras[camera_id]
        
        if camera["is_streaming"]:
            return True
        
        try:
            from src.camera import VideoCapture
            
            capture = VideoCapture(camera["source"])
            capture.start()
            
            self._captures[camera_id] = capture
            camera["status"] = "streaming"
            camera["is_streaming"] = True
            camera["error"] = None
            
            logger.info(f"Camera started: {camera_id}")
            return True
            
        except Exception as e:
            camera["status"] = "error"
            camera["error"] = str(e)
            logger.error(f"Failed to start camera {camera_id}: {e}")
            return False
    
    def stop_camera(self, camera_id: str) -> bool:
        """Stop camera streaming."""
        if camera_id not in self._cameras:
            return False
        
        camera = self._cameras[camera_id]
        
        if not camera["is_streaming"]:
            return True
        
        try:
            if camera_id in self._captures:
                self._captures[camera_id].stop()
                del self._captures[camera_id]
            
            camera["status"] = "stopped"
            camera["is_streaming"] = False
            
            logger.info(f"Camera stopped: {camera_id}")
            return True
            
        except Exception as e:
            camera["error"] = str(e)
            logger.error(f"Failed to stop camera {camera_id}: {e}")
            return False
    
    def read_frame(self, camera_id: str):
        """Read a frame from camera."""
        if camera_id not in self._captures:
            return None
        
        frame = self._captures[camera_id].read()
        
        if frame is not None:
            self._cameras[camera_id]["last_frame_at"] = datetime.now().isoformat()
            self._cameras[camera_id]["frame_count"] += 1
        
        return frame
    
    def get_status(self, camera_id: str) -> Optional[dict]:
        """Get camera status."""
        camera = self._cameras.get(camera_id)
        if not camera:
            return None
        
        return {
            "id": camera["id"],
            "name": camera["name"],
            "status": camera["status"],
            "is_streaming": camera["is_streaming"],
            "fps": camera["fps"],
            "frame_count": camera["frame_count"],
            "last_frame_at": camera["last_frame_at"],
            "error": camera["error"]
        }
    
    def get_all_status(self) -> List[dict]:
        """Get status of all cameras."""
        return [self.get_status(cam_id) for cam_id in self._cameras]
