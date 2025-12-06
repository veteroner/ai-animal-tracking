"""
Mobile Camera Handler
Mobil telefon kamera bağlantısı (IP Webcam, DroidCam vb.)
"""

import cv2
import time
import threading
import logging
import socket
import requests
from queue import Queue, Empty
from typing import Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import qrcode
from io import BytesIO

logger = logging.getLogger(__name__)


class MobileCameraType(Enum):
    """Mobil kamera türleri"""
    IP_WEBCAM = "ip_webcam"  # Android IP Webcam
    DROIDCAM = "droidcam"    # DroidCam
    IRIUN = "iriun"          # Iriun Webcam
    EPOCCAM = "epoccam"      # EpocCam (iOS)
    GENERIC_HTTP = "generic_http"  # Genel HTTP stream


@dataclass
class MobileCameraConfig:
    """Mobil kamera konfigürasyonu"""
    host: str
    port: int = 8080
    camera_type: MobileCameraType = MobileCameraType.IP_WEBCAM
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = False
    resolution: str = "720p"  # 480p, 720p, 1080p
    quality: int = 50  # 0-100
    autofocus: bool = True
    flash: bool = False
    buffer_size: int = 5
    reconnect_delay: float = 3.0
    connection_timeout: float = 10.0


class MobileCameraHandler:
    """Mobil kamera bağlantı sınıfı"""
    
    # Çözünürlük mapping
    RESOLUTION_MAP = {
        "480p": (640, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "4k": (3840, 2160)
    }
    
    def __init__(self, config: MobileCameraConfig):
        """
        Args:
            config: Mobil kamera konfigürasyonu
        """
        self.config = config
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_queue: Queue = Queue(maxsize=config.buffer_size)
        self._connected = False
        self._running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # İstatistikler
        self._stats = {
            "frames_received": 0,
            "frames_dropped": 0,
            "errors": 0,
            "start_time": None,
            "last_frame_time": None
        }
    
    @property
    def is_connected(self) -> bool:
        """Bağlantı durumu"""
        return self._connected
    
    @property
    def stats(self) -> dict:
        """İstatistikler"""
        return self._stats.copy()
    
    def _get_base_url(self) -> str:
        """Temel URL'i oluştur"""
        protocol = "https" if self.config.use_ssl else "http"
        return f"{protocol}://{self.config.host}:{self.config.port}"
    
    def _get_stream_url(self) -> str:
        """Stream URL'ini kamera türüne göre oluştur"""
        base_url = self._get_base_url()
        
        if self.config.camera_type == MobileCameraType.IP_WEBCAM:
            # IP Webcam Android
            return f"{base_url}/video"
        
        elif self.config.camera_type == MobileCameraType.DROIDCAM:
            # DroidCam
            return f"{base_url}/video"
        
        elif self.config.camera_type == MobileCameraType.IRIUN:
            # Iriun Webcam
            return f"{base_url}/video"
        
        elif self.config.camera_type == MobileCameraType.EPOCCAM:
            # EpocCam
            return f"{base_url}/video"
        
        else:
            # Genel HTTP stream
            return f"{base_url}/video"
    
    def _get_snapshot_url(self) -> str:
        """Snapshot URL'ini al"""
        base_url = self._get_base_url()
        
        if self.config.camera_type == MobileCameraType.IP_WEBCAM:
            return f"{base_url}/shot.jpg"
        else:
            return f"{base_url}/snapshot"
    
    def _check_server_available(self) -> bool:
        """Sunucu erişilebilirlik kontrolü"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.host, self.config.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def connect(self) -> bool:
        """Mobil kameraya bağlan"""
        if self._connected:
            return True
        
        logger.info(f"Mobil kameraya bağlanılıyor: {self.config.host}:{self.config.port}")
        
        # Sunucu kontrolü
        if not self._check_server_available():
            logger.error("Mobil kamera sunucusuna erişilemiyor")
            return False
        
        try:
            stream_url = self._get_stream_url()
            
            # OpenCV VideoCapture
            self._cap = cv2.VideoCapture(stream_url)
            
            if not self._cap.isOpened():
                raise ConnectionError("Stream açılamadı")
            
            # İlk frame kontrolü
            ret, frame = self._cap.read()
            if not ret:
                raise ConnectionError("İlk frame okunamadı")
            
            self._connected = True
            self._stats["start_time"] = time.time()
            self._stats["last_frame_time"] = time.time()
            
            logger.info(f"Mobil kamera bağlantısı başarılı: {stream_url}")
            return True
            
        except Exception as e:
            logger.error(f"Mobil kamera bağlantı hatası: {e}")
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
        
        self._connected = False
        logger.info("Mobil kamera bağlantısı kapatıldı")
    
    def _capture_loop(self) -> None:
        """Frame yakalama döngüsü"""
        while self._running:
            if not self._connected:
                time.sleep(self.config.reconnect_delay)
                self.connect()
                continue
            
            try:
                with self._lock:
                    if self._cap is None:
                        continue
                    ret, frame = self._cap.read()
                
                if not ret:
                    logger.warning("Frame okunamadı")
                    self._connected = False
                    continue
                
                self._stats["last_frame_time"] = time.time()
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
                self._connected = False
    
    def start_capture(self) -> bool:
        """Asenkron yakalamayı başlat"""
        if self._running:
            return True
        
        if not self.connect():
            return False
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        logger.info("Mobil kamera capture başlatıldı")
        return True
    
    def stop_capture(self) -> None:
        """Yakalamayı durdur"""
        self.disconnect()
    
    def read(self, timeout: float = 5.0) -> Tuple[bool, Optional[np.ndarray]]:
        """Frame oku"""
        try:
            frame = self._frame_queue.get(timeout=timeout)
            return True, frame
        except Empty:
            return False, None
    
    def read_latest(self) -> Tuple[bool, Optional[np.ndarray]]:
        """En son frame'i al"""
        frame = None
        
        while not self._frame_queue.empty():
            try:
                frame = self._frame_queue.get_nowait()
            except Empty:
                break
        
        if frame is not None:
            return True, frame
        
        return self.read()
    
    def capture_snapshot(self) -> Optional[np.ndarray]:
        """Anlık görüntü al (HTTP üzerinden)"""
        try:
            url = self._get_snapshot_url()
            auth = None
            
            if self.config.username and self.config.password:
                auth = (self.config.username, self.config.password)
            
            response = requests.get(url, auth=auth, timeout=5)
            
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                return frame
                
        except Exception as e:
            logger.error(f"Snapshot hatası: {e}")
        
        return None
    
    def set_camera_setting(self, setting: str, value: Any) -> bool:
        """
        Kamera ayarını değiştir (IP Webcam için)
        
        Args:
            setting: Ayar adı (focus, flash, zoom, quality vb.)
            value: Ayar değeri
        """
        if self.config.camera_type != MobileCameraType.IP_WEBCAM:
            logger.warning("Bu ayar sadece IP Webcam için desteklenir")
            return False
        
        try:
            base_url = self._get_base_url()
            url = f"{base_url}/settings/{setting}?set={value}"
            
            auth = None
            if self.config.username and self.config.password:
                auth = (self.config.username, self.config.password)
            
            response = requests.get(url, auth=auth, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Kamera ayarı değiştirme hatası: {e}")
            return False
    
    def toggle_flash(self, enabled: bool) -> bool:
        """Flash'ı aç/kapat"""
        return self.set_camera_setting("flash", "on" if enabled else "off")
    
    def set_focus_mode(self, mode: str = "auto") -> bool:
        """Focus modunu ayarla"""
        return self.set_camera_setting("focus_mode", mode)
    
    def set_quality(self, quality: int) -> bool:
        """Görüntü kalitesini ayarla (0-100)"""
        return self.set_camera_setting("quality", min(100, max(0, quality)))
    
    def get_camera_info(self) -> dict:
        """Kamera bilgilerini al"""
        info = {
            "host": self.config.host,
            "port": self.config.port,
            "type": self.config.camera_type.value,
            "connected": self._connected,
            "width": 0,
            "height": 0,
            "fps": 0,
            "stats": self._stats
        }
        
        with self._lock:
            if self._cap and self._cap.isOpened():
                info["width"] = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info["height"] = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info["fps"] = self._cap.get(cv2.CAP_PROP_FPS)
        
        return info


class QRCodeGenerator:
    """Hızlı bağlantı için QR kod oluşturucu"""
    
    @staticmethod
    def generate_connection_qr(
        server_ip: str,
        server_port: int,
        protocol: str = "http"
    ) -> np.ndarray:
        """
        Bağlantı bilgilerini içeren QR kod oluştur
        
        Args:
            server_ip: Sunucu IP adresi
            server_port: Sunucu portu
            protocol: Protokol (http/https)
            
        Returns:
            QR kod görüntüsü (numpy array)
        """
        connection_url = f"{protocol}://{server_ip}:{server_port}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(connection_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # PIL Image'ı numpy array'e çevir
        img_array = np.array(img.convert('RGB'))
        return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def get_local_ip() -> str:
        """Yerel IP adresini al"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


class MobileCameraDiscovery:
    """Ağdaki mobil kameraları otomatik keşfet"""
    
    COMMON_PORTS = [8080, 4747, 8081, 8082]
    
    @classmethod
    def scan_network(
        cls,
        network_prefix: str = None,
        ports: list = None,
        timeout: float = 0.5
    ) -> list[dict]:
        """
        Ağda mobil kamera ara
        
        Args:
            network_prefix: Ağ prefix'i (örn: "192.168.1")
            ports: Taranacak portlar
            timeout: Bağlantı timeout'u
            
        Returns:
            Bulunan kameraların listesi
        """
        if network_prefix is None:
            local_ip = QRCodeGenerator.get_local_ip()
            network_prefix = ".".join(local_ip.split(".")[:-1])
        
        if ports is None:
            ports = cls.COMMON_PORTS
        
        found_cameras = []
        
        def check_host(ip: str, port: int):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    camera_info = cls._identify_camera(ip, port)
                    if camera_info:
                        found_cameras.append(camera_info)
                        
            except Exception:
                pass
        
        threads = []
        for i in range(1, 255):
            ip = f"{network_prefix}.{i}"
            for port in ports:
                t = threading.Thread(target=check_host, args=(ip, port))
                t.start()
                threads.append(t)
        
        for t in threads:
            t.join()
        
        return found_cameras
    
    @classmethod
    def _identify_camera(cls, ip: str, port: int) -> Optional[dict]:
        """Kamera türünü belirle"""
        try:
            # IP Webcam kontrolü
            response = requests.get(f"http://{ip}:{port}/status.json", timeout=2)
            if response.status_code == 200:
                return {
                    "ip": ip,
                    "port": port,
                    "type": MobileCameraType.IP_WEBCAM,
                    "name": "IP Webcam"
                }
        except Exception:
            pass
        
        try:
            # Genel video stream kontrolü
            response = requests.get(f"http://{ip}:{port}/video", timeout=2, stream=True)
            if response.status_code == 200:
                return {
                    "ip": ip,
                    "port": port,
                    "type": MobileCameraType.GENERIC_HTTP,
                    "name": "HTTP Camera"
                }
        except Exception:
            pass
        
        return None
