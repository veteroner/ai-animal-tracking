"""
AI Animal Tracking System - Video Capture
=========================================

Video yakalama sınıfı - USB kamera, IP kamera, RTSP stream ve video dosyası desteği.
"""

import time
import threading
from pathlib import Path
from typing import Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

import cv2
import numpy as np


logger = logging.getLogger("animal_tracking.camera")


class CameraType(Enum):
    """Kamera türleri"""
    USB = "usb"
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"
    UNKNOWN = "unknown"


class CameraState(Enum):
    """Kamera durumları"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class CameraConfig:
    """Kamera konfigürasyonu"""
    source: Union[int, str] = 0
    name: str = "Camera"
    width: int = 1280
    height: int = 720
    fps: int = 30
    buffer_size: int = 2
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 10
    auto_reconnect: bool = True


@dataclass
class FrameInfo:
    """Frame bilgileri"""
    frame: np.ndarray
    timestamp: float
    frame_id: int
    width: int
    height: int
    fps: float = 0.0


class VideoCapture:
    """
    Video yakalama sınıfı.
    
    USB webcam, IP kamera, RTSP stream ve video dosyası destekler.
    Otomatik yeniden bağlanma ve frame buffer özellikleri içerir.
    
    Kullanım:
        # USB webcam
        cap = VideoCapture(source=0)
        
        # IP kamera
        cap = VideoCapture(source="http://192.168.1.100:8080/video")
        
        # RTSP stream
        cap = VideoCapture(source="rtsp://user:pass@192.168.1.100:554/stream")
        
        # Video dosyası
        cap = VideoCapture(source="video.mp4")
        
        # Başlat ve frame oku
        cap.start()
        frame_info = cap.read()
        cap.stop()
    """
    
    def __init__(
        self,
        source: Union[int, str] = 0,
        name: str = "Camera",
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        buffer_size: int = 2,
        auto_reconnect: bool = True,
        on_frame_callback: Optional[Callable[[FrameInfo], None]] = None,
    ):
        """
        Args:
            source: Kamera kaynağı (index, URL, dosya yolu)
            name: Kamera ismi
            width: İstenen genişlik
            height: İstenen yükseklik
            fps: İstenen FPS
            buffer_size: Frame buffer boyutu
            auto_reconnect: Otomatik yeniden bağlanma
            on_frame_callback: Her frame'de çağrılacak fonksiyon
        """
        self.config = CameraConfig(
            source=source,
            name=name,
            width=width,
            height=height,
            fps=fps,
            buffer_size=buffer_size,
            auto_reconnect=auto_reconnect,
        )
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._state = CameraState.DISCONNECTED
        self._camera_type = self._detect_camera_type(source)
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Frame bilgileri
        self._frame: Optional[np.ndarray] = None
        self._frame_id: int = 0
        self._last_frame_time: float = 0.0
        self._fps_actual: float = 0.0
        
        # İstatistikler
        self._frames_read: int = 0
        self._frames_dropped: int = 0
        self._reconnect_count: int = 0
        
        # Callback
        self._on_frame_callback = on_frame_callback
        
        # Gerçek kamera özellikleri (bağlantı sonrası)
        self._actual_width: int = 0
        self._actual_height: int = 0
        self._actual_fps: float = 0.0
    
    @staticmethod
    def _detect_camera_type(source: Union[int, str]) -> CameraType:
        """Kamera türünü tespit et"""
        if isinstance(source, int):
            return CameraType.USB
        
        source_str = str(source).lower()
        
        if source_str.startswith("rtsp://"):
            return CameraType.RTSP
        elif source_str.startswith(("http://", "https://")):
            return CameraType.HTTP
        elif Path(source).exists() or source_str.endswith((".mp4", ".avi", ".mkv", ".mov")):
            return CameraType.FILE
        else:
            return CameraType.UNKNOWN
    
    @property
    def state(self) -> CameraState:
        """Kamera durumu"""
        return self._state
    
    @property
    def is_opened(self) -> bool:
        """Kamera açık mı"""
        return self._cap is not None and self._cap.isOpened()
    
    @property
    def is_streaming(self) -> bool:
        """Stream aktif mi"""
        return self._state == CameraState.STREAMING
    
    @property
    def frame_size(self) -> Tuple[int, int]:
        """Frame boyutu (width, height)"""
        return (self._actual_width, self._actual_height)
    
    @property
    def fps(self) -> float:
        """Gerçek FPS"""
        return self._fps_actual
    
    @property
    def camera_type(self) -> CameraType:
        """Kamera türü"""
        return self._camera_type
    
    @property
    def statistics(self) -> dict:
        """İstatistikler"""
        return {
            "frames_read": self._frames_read,
            "frames_dropped": self._frames_dropped,
            "reconnect_count": self._reconnect_count,
            "actual_fps": self._fps_actual,
            "frame_size": self.frame_size,
        }
    
    def _connect(self) -> bool:
        """Kameraya bağlan"""
        self._state = CameraState.CONNECTING
        logger.info(f"Connecting to {self.config.name} ({self.config.source})...")
        
        try:
            # OpenCV VideoCapture oluştur
            source = self.config.source
            
            if self._camera_type == CameraType.RTSP:
                # RTSP için özel ayarlar
                self._cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)
            elif self._camera_type == CameraType.HTTP:
                self._cap = cv2.VideoCapture(source)
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)
            else:
                self._cap = cv2.VideoCapture(source)
            
            if not self._cap.isOpened():
                logger.error(f"Failed to open camera: {self.config.source}")
                self._state = CameraState.ERROR
                return False
            
            # İstenen özellikleri ayarla
            if self._camera_type != CameraType.FILE:
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
                self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Gerçek özellikleri al
            self._actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
            
            if self._actual_fps <= 0:
                self._actual_fps = self.config.fps
            
            self._state = CameraState.CONNECTED
            logger.info(
                f"Connected to {self.config.name}: "
                f"{self._actual_width}x{self._actual_height} @ {self._actual_fps:.1f}fps"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self._state = CameraState.ERROR
            return False
    
    def _disconnect(self):
        """Bağlantıyı kes"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._state = CameraState.DISCONNECTED
        logger.info(f"Disconnected from {self.config.name}")
    
    def _capture_loop(self):
        """Frame yakalama döngüsü (thread)"""
        fps_time = time.time()
        fps_count = 0
        
        while not self._stop_event.is_set():
            if not self.is_opened:
                # Yeniden bağlanmayı dene
                if self.config.auto_reconnect:
                    if self._reconnect_count < self.config.max_reconnect_attempts:
                        logger.warning(f"Reconnecting... (attempt {self._reconnect_count + 1})")
                        time.sleep(self.config.reconnect_interval)
                        self._reconnect_count += 1
                        if self._connect():
                            self._reconnect_count = 0
                            continue
                    else:
                        logger.error("Max reconnection attempts reached")
                        self._state = CameraState.ERROR
                        break
                else:
                    break
            
            # Frame oku
            ret, frame = self._cap.read()
            
            if not ret or frame is None:
                self._frames_dropped += 1
                
                if self._camera_type == CameraType.FILE:
                    # Video dosyası bitti, başa sar
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Frame'i kaydet
            current_time = time.time()
            
            with self._lock:
                self._frame = frame
                self._frame_id += 1
                self._last_frame_time = current_time
                self._frames_read += 1
            
            # FPS hesapla
            fps_count += 1
            if current_time - fps_time >= 1.0:
                self._fps_actual = fps_count / (current_time - fps_time)
                fps_count = 0
                fps_time = current_time
            
            # Callback
            if self._on_frame_callback is not None:
                frame_info = FrameInfo(
                    frame=frame.copy(),
                    timestamp=current_time,
                    frame_id=self._frame_id,
                    width=self._actual_width,
                    height=self._actual_height,
                    fps=self._fps_actual,
                )
                try:
                    self._on_frame_callback(frame_info)
                except Exception as e:
                    logger.error(f"Frame callback error: {e}")
        
        self._state = CameraState.STOPPED
    
    def start(self) -> bool:
        """
        Kamerayı başlat ve streaming'i aktifleştir.
        
        Returns:
            Başarılı ise True
        """
        if self.is_streaming:
            logger.warning("Camera already streaming")
            return True
        
        # Bağlan
        if not self._connect():
            return False
        
        # Capture thread'i başlat
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self._state = CameraState.STREAMING
        
        logger.info(f"Started streaming from {self.config.name}")
        return True
    
    def stop(self):
        """Kamerayı durdur"""
        logger.info(f"Stopping {self.config.name}...")
        
        self._stop_event.set()
        
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        self._disconnect()
        
        logger.info(f"Stopped {self.config.name}")
    
    def read(self) -> Optional[FrameInfo]:
        """
        Son frame'i oku.
        
        Returns:
            FrameInfo veya None
        """
        with self._lock:
            if self._frame is None:
                return None
            
            return FrameInfo(
                frame=self._frame.copy(),
                timestamp=self._last_frame_time,
                frame_id=self._frame_id,
                width=self._actual_width,
                height=self._actual_height,
                fps=self._fps_actual,
            )
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Son frame'i numpy array olarak oku.
        
        Returns:
            Frame array veya None
        """
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()
    
    def grab_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Doğrudan kameradan frame al (senkron).
        
        Returns:
            (success, frame) tuple
        """
        if not self.is_opened:
            return False, None
        
        ret, frame = self._cap.read()
        return ret, frame
    
    def set_resolution(self, width: int, height: int) -> bool:
        """Çözünürlüğü değiştir"""
        if not self.is_opened:
            return False
        
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        self._actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return True
    
    def set_fps(self, fps: int) -> bool:
        """FPS değiştir"""
        if not self.is_opened:
            return False
        
        self._cap.set(cv2.CAP_PROP_FPS, fps)
        self._actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        
        return True
    
    def __enter__(self):
        """Context manager enter"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
    
    def __del__(self):
        """Destructor"""
        self.stop()


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Kamera kaynağını belirle
    source = 0  # USB webcam
    if len(sys.argv) > 1:
        source = sys.argv[1]
        if source.isdigit():
            source = int(source)
    
    print(f"Testing VideoCapture with source: {source}")
    
    # Test
    with VideoCapture(source=source, name="Test Camera") as cap:
        print(f"Camera type: {cap.camera_type}")
        print(f"Frame size: {cap.frame_size}")
        print(f"FPS: {cap.fps}")
        
        # Birkaç frame oku
        for i in range(100):
            frame_info = cap.read()
            
            if frame_info is not None:
                cv2.imshow("Test", frame_info.frame)
                print(f"\rFrame {frame_info.frame_id} - FPS: {frame_info.fps:.1f}", end="")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        print(f"\nStatistics: {cap.statistics}")
    
    cv2.destroyAllWindows()
