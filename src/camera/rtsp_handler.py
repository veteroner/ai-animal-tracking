"""
RTSP Stream Handler
RTSP stream bağlantısı ve yönetimi
"""

import cv2
import time
import threading
import logging
from queue import Queue, Empty
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Stream durumu"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class RTSPConfig:
    """RTSP konfigürasyonu"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    transport: str = "tcp"  # tcp veya udp
    buffer_size: int = 10
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10
    connection_timeout: float = 10.0
    frame_timeout: float = 5.0


class RTSPHandler:
    """RTSP Stream Handler sınıfı"""
    
    def __init__(self, config: RTSPConfig):
        """
        Args:
            config: RTSP konfigürasyonu
        """
        self.config = config
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_queue: Queue = Queue(maxsize=config.buffer_size)
        self._status = StreamStatus.DISCONNECTED
        self._running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._reconnect_count = 0
        self._last_frame_time = 0.0
        self._lock = threading.Lock()
        self._status_callback: Optional[Callable[[StreamStatus], None]] = None
        
        # İstatistikler
        self._stats = {
            "frames_received": 0,
            "frames_dropped": 0,
            "reconnects": 0,
            "errors": 0,
            "start_time": None
        }
    
    @property
    def status(self) -> StreamStatus:
        """Stream durumu"""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Bağlantı durumu"""
        return self._status == StreamStatus.CONNECTED
    
    @property
    def stats(self) -> dict:
        """İstatistikler"""
        return self._stats.copy()
    
    def set_status_callback(self, callback: Callable[[StreamStatus], None]) -> None:
        """Durum değişikliği callback'i ayarla"""
        self._status_callback = callback
    
    def _set_status(self, status: StreamStatus) -> None:
        """Durumu güncelle ve callback'i çağır"""
        self._status = status
        if self._status_callback:
            try:
                self._status_callback(status)
            except Exception as e:
                logger.error(f"Status callback hatası: {e}")
    
    def _build_url(self) -> str:
        """Kimlik bilgileriyle URL oluştur"""
        url = self.config.url
        
        if self.config.username and self.config.password:
            # rtsp://user:pass@host:port/path formatı
            if "://" in url:
                protocol, rest = url.split("://", 1)
                url = f"{protocol}://{self.config.username}:{self.config.password}@{rest}"
        
        return url
    
    def connect(self) -> bool:
        """RTSP stream'e bağlan"""
        if self._status == StreamStatus.CONNECTED:
            return True
        
        self._set_status(StreamStatus.CONNECTING)
        logger.info(f"RTSP bağlantısı başlatılıyor: {self.config.url}")
        
        try:
            url = self._build_url()
            
            # OpenCV VideoCapture ayarları
            self._cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            
            # RTSP transport protokolü (TCP daha güvenilir)
            if self.config.transport == "tcp":
                self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            
            # Buffer boyutu
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Bağlantı timeout'u
            start_time = time.time()
            while not self._cap.isOpened():
                if time.time() - start_time > self.config.connection_timeout:
                    raise TimeoutError("RTSP bağlantı timeout'u")
                time.sleep(0.1)
            
            # İlk frame'i oku
            ret, frame = self._cap.read()
            if not ret:
                raise ConnectionError("İlk frame okunamadı")
            
            self._set_status(StreamStatus.CONNECTED)
            self._reconnect_count = 0
            self._last_frame_time = time.time()
            self._stats["start_time"] = time.time()
            
            logger.info("RTSP bağlantısı başarılı")
            return True
            
        except Exception as e:
            logger.error(f"RTSP bağlantı hatası: {e}")
            self._set_status(StreamStatus.ERROR)
            self._stats["errors"] += 1
            return False
    
    def disconnect(self) -> None:
        """Bağlantıyı kapat"""
        self._running = False
        
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
        
        # Kuyruğu temizle
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except Empty:
                break
        
        self._set_status(StreamStatus.DISCONNECTED)
        logger.info("RTSP bağlantısı kapatıldı")
    
    def _reconnect(self) -> bool:
        """Yeniden bağlanmayı dene"""
        if self._reconnect_count >= self.config.max_reconnect_attempts:
            logger.error("Maksimum yeniden bağlanma denemesi aşıldı")
            self._set_status(StreamStatus.ERROR)
            return False
        
        self._reconnect_count += 1
        self._stats["reconnects"] += 1
        self._set_status(StreamStatus.RECONNECTING)
        
        logger.info(f"Yeniden bağlanma denemesi {self._reconnect_count}/{self.config.max_reconnect_attempts}")
        
        # Mevcut bağlantıyı kapat
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
        
        # Bekle ve tekrar dene
        time.sleep(self.config.reconnect_delay)
        return self.connect()
    
    def _capture_loop(self) -> None:
        """Frame yakalama döngüsü"""
        while self._running:
            if not self.is_connected:
                if not self._reconnect():
                    break
                continue
            
            try:
                with self._lock:
                    if self._cap is None:
                        continue
                    ret, frame = self._cap.read()
                
                if not ret:
                    logger.warning("Frame okunamadı, yeniden bağlanılıyor...")
                    if not self._reconnect():
                        break
                    continue
                
                self._last_frame_time = time.time()
                self._stats["frames_received"] += 1
                
                # Kuyruğa ekle
                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()
                        self._stats["frames_dropped"] += 1
                    except Empty:
                        pass
                
                self._frame_queue.put(frame)
                
            except Exception as e:
                logger.error(f"Frame yakalama hatası: {e}")
                self._stats["errors"] += 1
                if not self._reconnect():
                    break
    
    def start_capture(self) -> bool:
        """Asenkron frame yakalamayı başlat"""
        if self._running:
            return True
        
        if not self.connect():
            return False
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        logger.info("RTSP capture başlatıldı")
        return True
    
    def stop_capture(self) -> None:
        """Frame yakalamayı durdur"""
        self.disconnect()
        logger.info("RTSP capture durduruldu")
    
    def read(self) -> Tuple[bool, Optional['np.ndarray']]:
        """
        En son frame'i oku
        
        Returns:
            (success, frame) tuple'ı
        """
        try:
            frame = self._frame_queue.get(timeout=self.config.frame_timeout)
            return True, frame
        except Empty:
            # Timeout kontrolü
            if time.time() - self._last_frame_time > self.config.frame_timeout:
                logger.warning("Frame timeout, yeniden bağlanma gerekebilir")
            return False, None
    
    def read_latest(self) -> Tuple[bool, Optional['np.ndarray']]:
        """
        En son frame'i al (ara frame'leri atla)
        
        Returns:
            (success, frame) tuple'ı
        """
        frame = None
        
        # Kuyruktaki tüm frame'leri oku, en sonuncusunu al
        while not self._frame_queue.empty():
            try:
                frame = self._frame_queue.get_nowait()
            except Empty:
                break
        
        if frame is not None:
            return True, frame
        
        # Kuyruk boşsa bekle
        return self.read()
    
    def get_stream_info(self) -> dict:
        """Stream bilgilerini al"""
        info = {
            "url": self.config.url,
            "status": self._status.value,
            "width": 0,
            "height": 0,
            "fps": 0,
            "codec": "",
            "stats": self._stats
        }
        
        with self._lock:
            if self._cap and self._cap.isOpened():
                info["width"] = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info["height"] = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info["fps"] = self._cap.get(cv2.CAP_PROP_FPS)
                info["codec"] = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        
        return info
    
    def health_check(self) -> bool:
        """Stream sağlık kontrolü"""
        if not self.is_connected:
            return False
        
        # Son frame zamanını kontrol et
        if time.time() - self._last_frame_time > self.config.frame_timeout:
            return False
        
        return True


class RTSPStreamManager:
    """Birden fazla RTSP stream yönetimi"""
    
    def __init__(self):
        self._streams: dict[str, RTSPHandler] = {}
        self._lock = threading.Lock()
    
    def add_stream(self, stream_id: str, config: RTSPConfig) -> RTSPHandler:
        """Yeni stream ekle"""
        with self._lock:
            if stream_id in self._streams:
                raise ValueError(f"Stream zaten mevcut: {stream_id}")
            
            handler = RTSPHandler(config)
            self._streams[stream_id] = handler
            return handler
    
    def remove_stream(self, stream_id: str) -> None:
        """Stream'i kaldır"""
        with self._lock:
            if stream_id in self._streams:
                self._streams[stream_id].disconnect()
                del self._streams[stream_id]
    
    def get_stream(self, stream_id: str) -> Optional[RTSPHandler]:
        """Stream'i al"""
        return self._streams.get(stream_id)
    
    def start_all(self) -> None:
        """Tüm stream'leri başlat"""
        for handler in self._streams.values():
            handler.start_capture()
    
    def stop_all(self) -> None:
        """Tüm stream'leri durdur"""
        for handler in self._streams.values():
            handler.stop_capture()
    
    def get_all_status(self) -> dict[str, StreamStatus]:
        """Tüm stream durumlarını al"""
        return {sid: handler.status for sid, handler in self._streams.items()}
