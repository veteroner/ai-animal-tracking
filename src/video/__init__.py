"""
Video Kayıt Modülü.

Bu modül detection sonuçlarını video olarak kaydeder,
frame'lere annotation ekler ve çeşitli video formatlarını destekler.
"""

import cv2
import numpy as np
import logging
import threading
import queue
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

logger = logging.getLogger(__name__)


class VideoFormat(Enum):
    """Desteklenen video formatları."""
    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    MOV = "mov"


class VideoCodec(Enum):
    """Desteklenen video codec'leri."""
    H264 = "avc1"
    H265 = "hvc1"
    MJPEG = "MJPG"
    XVID = "XVID"
    MP4V = "mp4v"


@dataclass
class VideoConfig:
    """Video kayıt konfigürasyonu."""
    output_dir: str = "recordings"
    format: VideoFormat = VideoFormat.MP4
    codec: VideoCodec = VideoCodec.MP4V
    fps: float = 30.0
    resolution: Optional[Tuple[int, int]] = None  # None = orijinal çözünürlük
    quality: int = 95  # 0-100
    max_file_size_mb: int = 500  # Max dosya boyutu
    max_duration_seconds: int = 3600  # Max süre (1 saat)
    buffer_size: int = 100  # Frame buffer boyutu
    
    def __post_init__(self):
        """Değerleri doğrula."""
        self.quality = max(0, min(100, self.quality))
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class AnnotationStyle:
    """Annotation stilleri."""
    bbox_color: Tuple[int, int, int] = (0, 255, 0)  # BGR - Yeşil
    bbox_thickness: int = 2
    text_color: Tuple[int, int, int] = (255, 255, 255)  # Beyaz
    text_bg_color: Tuple[int, int, int] = (0, 0, 0)  # Siyah
    text_scale: float = 0.6
    text_thickness: int = 1
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    show_confidence: bool = True
    show_class_name: bool = True
    show_track_id: bool = True
    show_timestamp: bool = True
    timestamp_position: str = "top-left"  # top-left, top-right, bottom-left, bottom-right


@dataclass
class RecordingInfo:
    """Kayıt bilgileri."""
    filename: str
    filepath: str
    start_time: datetime
    end_time: Optional[datetime] = None
    frame_count: int = 0
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    resolution: Tuple[int, int] = (0, 0)
    fps: float = 0.0
    detection_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict formatına dönüştür."""
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "frame_count": self.frame_count,
            "duration_seconds": round(self.duration_seconds, 2),
            "file_size_mb": round(self.file_size_bytes / (1024 * 1024), 2),
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "fps": self.fps,
            "detection_count": self.detection_count,
        }


class FrameAnnotator:
    """
    Frame annotator sınıfı.
    
    Detection ve tracking sonuçlarını frame'lere çizer.
    """
    
    def __init__(self, style: Optional[AnnotationStyle] = None):
        """
        Annotator'ı başlat.
        
        Args:
            style: Annotation stilleri
        """
        self.style = style or AnnotationStyle()
        self._class_colors: Dict[str, Tuple[int, int, int]] = {}
    
    def get_color_for_class(self, class_name: str) -> Tuple[int, int, int]:
        """Sınıf için renk getir (tutarlı renkler için hash kullanır)."""
        if class_name not in self._class_colors:
            # Hash'e dayalı tutarlı renk
            hash_val = hash(class_name)
            r = (hash_val & 0xFF0000) >> 16
            g = (hash_val & 0x00FF00) >> 8
            b = hash_val & 0x0000FF
            # Renkler çok koyu olmasın
            r = max(100, r)
            g = max(100, g)
            b = max(100, b)
            self._class_colors[class_name] = (b, g, r)  # BGR
        return self._class_colors[class_name]
    
    def annotate_detection(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        class_name: str,
        confidence: float,
        track_id: Optional[int] = None,
        color: Optional[Tuple[int, int, int]] = None
    ) -> np.ndarray:
        """
        Tek bir detection'ı frame'e çiz.
        
        Args:
            frame: Input frame
            bbox: Bounding box (x1, y1, x2, y2)
            class_name: Sınıf adı
            confidence: Güven skoru
            track_id: Track ID (opsiyonel)
            color: Özel renk (opsiyonel)
        
        Returns:
            Annotated frame
        """
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        # Renk belirle
        box_color = color or self.get_color_for_class(class_name)
        
        # Bounding box çiz
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, self.style.bbox_thickness)
        
        # Label oluştur
        label_parts = []
        
        if self.style.show_class_name:
            label_parts.append(class_name)
        
        if self.style.show_track_id and track_id is not None:
            label_parts.append(f"ID:{track_id}")
        
        if self.style.show_confidence:
            label_parts.append(f"{confidence:.1%}")
        
        if label_parts:
            label = " ".join(label_parts)
            
            # Label boyutunu hesapla
            (label_w, label_h), baseline = cv2.getTextSize(
                label, self.style.font, self.style.text_scale, self.style.text_thickness
            )
            
            # Label arka planı
            cv2.rectangle(
                frame,
                (x1, y1 - label_h - baseline - 5),
                (x1 + label_w + 5, y1),
                self.style.text_bg_color,
                -1
            )
            
            # Label text
            cv2.putText(
                frame,
                label,
                (x1 + 2, y1 - baseline - 2),
                self.style.font,
                self.style.text_scale,
                self.style.text_color,
                self.style.text_thickness
            )
        
        return frame
    
    def annotate_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Birden fazla detection'ı frame'e çiz.
        
        Args:
            frame: Input frame
            detections: Detection listesi (her biri bbox, class_name, confidence içermeli)
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for det in detections:
            bbox = det.get("bbox", det.get("box", (0, 0, 0, 0)))
            class_name = det.get("class_name", det.get("label", "unknown"))
            confidence = det.get("confidence", det.get("score", 0.0))
            track_id = det.get("track_id", det.get("id"))
            
            annotated = self.annotate_detection(
                annotated, bbox, class_name, confidence, track_id
            )
        
        return annotated
    
    def add_timestamp(
        self,
        frame: np.ndarray,
        timestamp: Optional[datetime] = None,
        custom_text: str = ""
    ) -> np.ndarray:
        """
        Frame'e timestamp ekle.
        
        Args:
            frame: Input frame
            timestamp: Zaman damgası (None = şimdiki zaman)
            custom_text: Ek metin
        
        Returns:
            Timestamped frame
        """
        if not self.style.show_timestamp:
            return frame
        
        ts = timestamp or datetime.now()
        ts_text = ts.strftime("%Y-%m-%d %H:%M:%S")
        
        if custom_text:
            ts_text = f"{ts_text} | {custom_text}"
        
        h, w = frame.shape[:2]
        
        # Text boyutunu hesapla
        (text_w, text_h), baseline = cv2.getTextSize(
            ts_text, self.style.font, self.style.text_scale * 0.8, self.style.text_thickness
        )
        
        # Pozisyon belirle
        margin = 10
        position = self.style.timestamp_position
        
        if position == "top-left":
            x, y = margin, text_h + margin
        elif position == "top-right":
            x, y = w - text_w - margin, text_h + margin
        elif position == "bottom-left":
            x, y = margin, h - margin
        else:  # bottom-right
            x, y = w - text_w - margin, h - margin
        
        # Arka plan
        cv2.rectangle(
            frame,
            (x - 2, y - text_h - 2),
            (x + text_w + 2, y + baseline + 2),
            self.style.text_bg_color,
            -1
        )
        
        # Text
        cv2.putText(
            frame,
            ts_text,
            (x, y),
            self.style.font,
            self.style.text_scale * 0.8,
            self.style.text_color,
            self.style.text_thickness
        )
        
        return frame
    
    def add_info_overlay(
        self,
        frame: np.ndarray,
        info: Dict[str, Any],
        position: str = "top-right"
    ) -> np.ndarray:
        """
        Frame'e bilgi overlay'i ekle.
        
        Args:
            frame: Input frame
            info: Gösterilecek bilgiler (key-value pairs)
            position: Overlay pozisyonu
        
        Returns:
            Frame with overlay
        """
        h, w = frame.shape[:2]
        
        lines = [f"{k}: {v}" for k, v in info.items()]
        
        # Text boyutlarını hesapla
        line_height = 20
        max_width = 0
        
        for line in lines:
            (text_w, _), _ = cv2.getTextSize(
                line, self.style.font, self.style.text_scale * 0.7, 1
            )
            max_width = max(max_width, text_w)
        
        total_height = len(lines) * line_height + 10
        
        # Pozisyon belirle
        margin = 10
        if position == "top-left":
            x, y = margin, margin + line_height
        elif position == "top-right":
            x, y = w - max_width - margin - 10, margin + line_height
        elif position == "bottom-left":
            x, y = margin, h - total_height
        else:  # bottom-right
            x, y = w - max_width - margin - 10, h - total_height
        
        # Yarı saydam arka plan
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x - 5, y - line_height),
            (x + max_width + 10, y + (len(lines) - 1) * line_height + 5),
            (0, 0, 0),
            -1
        )
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Text'leri çiz
        for i, line in enumerate(lines):
            cv2.putText(
                frame,
                line,
                (x, y + i * line_height),
                self.style.font,
                self.style.text_scale * 0.7,
                (255, 255, 255),
                1
            )
        
        return frame


class VideoRecorder:
    """
    Video kayıt sınıfı.
    
    Frame'leri video dosyasına kaydeder, annotation desteği sunar.
    """
    
    def __init__(self, config: Optional[VideoConfig] = None):
        """
        Recorder'ı başlat.
        
        Args:
            config: Video konfigürasyonu
        """
        self.config = config or VideoConfig()
        self.annotator = FrameAnnotator()
        
        self._writer: Optional[cv2.VideoWriter] = None
        self._is_recording = False
        self._current_recording: Optional[RecordingInfo] = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=self.config.buffer_size)
        self._writer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._recordings: List[RecordingInfo] = []
        self._lock = threading.Lock()
        
        logger.info(f"VideoRecorder başlatıldı - Output: {self.config.output_dir}")
    
    @property
    def is_recording(self) -> bool:
        """Kayıt yapılıyor mu?"""
        return self._is_recording
    
    @property
    def current_recording(self) -> Optional[RecordingInfo]:
        """Mevcut kayıt bilgisi."""
        return self._current_recording
    
    def start_recording(
        self,
        filename: Optional[str] = None,
        resolution: Optional[Tuple[int, int]] = None
    ) -> str:
        """
        Video kaydını başlat.
        
        Args:
            filename: Dosya adı (opsiyonel, otomatik oluşturulur)
            resolution: Video çözünürlüğü
        
        Returns:
            Dosya yolu
        """
        if self._is_recording:
            logger.warning("Zaten kayıt yapılıyor")
            return self._current_recording.filepath if self._current_recording else ""
        
        # Dosya adı oluştur
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.{self.config.format.value}"
        
        filepath = str(Path(self.config.output_dir) / filename)
        
        # Resolution
        res = resolution or self.config.resolution or (1920, 1080)
        
        # Codec seç
        fourcc = cv2.VideoWriter_fourcc(*self.config.codec.value)
        
        # Writer oluştur
        self._writer = cv2.VideoWriter(
            filepath,
            fourcc,
            self.config.fps,
            res
        )
        
        if not self._writer.isOpened():
            logger.error(f"Video writer açılamadı: {filepath}")
            raise RuntimeError(f"Video writer açılamadı: {filepath}")
        
        # Kayıt bilgisi oluştur
        self._current_recording = RecordingInfo(
            filename=filename,
            filepath=filepath,
            start_time=datetime.now(),
            resolution=res,
            fps=self.config.fps
        )
        
        # Thread'i başlat
        self._stop_event.clear()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()
        
        self._is_recording = True
        logger.info(f"Video kaydı başlatıldı: {filepath}")
        
        return filepath
    
    def stop_recording(self) -> Optional[RecordingInfo]:
        """
        Video kaydını durdur.
        
        Returns:
            Kayıt bilgisi
        """
        if not self._is_recording:
            logger.warning("Kayıt yapılmıyor")
            return None
        
        self._is_recording = False
        self._stop_event.set()
        
        # Thread'in bitmesini bekle
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=5.0)
        
        # Writer'ı kapat
        if self._writer:
            self._writer.release()
            self._writer = None
        
        # Kayıt bilgisini güncelle
        if self._current_recording:
            self._current_recording.end_time = datetime.now()
            self._current_recording.duration_seconds = (
                self._current_recording.end_time - self._current_recording.start_time
            ).total_seconds()
            
            # Dosya boyutunu al
            filepath = Path(self._current_recording.filepath)
            if filepath.exists():
                self._current_recording.file_size_bytes = filepath.stat().st_size
            
            self._recordings.append(self._current_recording)
            result = self._current_recording
            
            logger.info(
                f"Video kaydı tamamlandı: {result.filepath} "
                f"({result.frame_count} frame, {result.duration_seconds:.1f}s)"
            )
            
            self._current_recording = None
            return result
        
        return None
    
    def write_frame(
        self,
        frame: np.ndarray,
        detections: Optional[List[Dict[str, Any]]] = None,
        annotate: bool = True,
        timestamp: bool = True,
        info_overlay: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Frame'i kaydet.
        
        Args:
            frame: Video frame'i
            detections: Detection listesi (annotation için)
            annotate: Detection'ları çiz
            timestamp: Timestamp ekle
            info_overlay: Ek bilgi overlay'i
        
        Returns:
            Başarılı mı?
        """
        if not self._is_recording:
            return False
        
        # Frame'i kopyala
        processed_frame = frame.copy()
        
        # Annotation ekle
        if annotate and detections:
            processed_frame = self.annotator.annotate_detections(processed_frame, detections)
            
            if self._current_recording:
                self._current_recording.detection_count += len(detections)
        
        # Timestamp ekle
        if timestamp:
            processed_frame = self.annotator.add_timestamp(processed_frame)
        
        # Info overlay ekle
        if info_overlay:
            processed_frame = self.annotator.add_info_overlay(processed_frame, info_overlay)
        
        # Çözünürlük ayarla
        if self._current_recording and processed_frame.shape[:2][::-1] != self._current_recording.resolution:
            processed_frame = cv2.resize(processed_frame, self._current_recording.resolution)
        
        # Queue'ya ekle
        try:
            self._frame_queue.put_nowait(processed_frame)
            return True
        except queue.Full:
            logger.warning("Frame buffer dolu, frame atlandı")
            return False
    
    def _writer_loop(self):
        """Background writer thread loop."""
        while not self._stop_event.is_set() or not self._frame_queue.empty():
            try:
                frame = self._frame_queue.get(timeout=0.1)
                
                if self._writer and self._writer.isOpened():
                    self._writer.write(frame)
                    
                    with self._lock:
                        if self._current_recording:
                            self._current_recording.frame_count += 1
                
                self._frame_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Frame yazma hatası: {e}")
    
    def get_recordings(self) -> List[RecordingInfo]:
        """Tüm kayıtları getir."""
        return self._recordings.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Kayıt istatistiklerini getir."""
        total_frames = sum(r.frame_count for r in self._recordings)
        total_duration = sum(r.duration_seconds for r in self._recordings)
        total_size = sum(r.file_size_bytes for r in self._recordings)
        
        return {
            "total_recordings": len(self._recordings),
            "total_frames": total_frames,
            "total_duration_seconds": round(total_duration, 2),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "is_recording": self._is_recording,
            "current_recording": self._current_recording.to_dict() if self._current_recording else None,
            "buffer_usage": self._frame_queue.qsize(),
            "buffer_capacity": self.config.buffer_size,
        }


class VideoClipExtractor:
    """
    Video klip çıkarıcı.
    
    Belirli olaylar için kısa video klipleri çıkarır.
    """
    
    def __init__(self, config: Optional[VideoConfig] = None):
        """
        Extractor'ı başlat.
        
        Args:
            config: Video konfigürasyonu
        """
        self.config = config or VideoConfig()
        self.config.output_dir = str(Path(self.config.output_dir) / "clips")
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        
        self._frame_buffer: List[Tuple[np.ndarray, datetime]] = []
        self._max_buffer_seconds: float = 30.0
        self._buffer_lock = threading.Lock()
    
    def add_frame(self, frame: np.ndarray, timestamp: Optional[datetime] = None):
        """
        Frame'i buffer'a ekle.
        
        Args:
            frame: Video frame'i
            timestamp: Zaman damgası
        """
        ts = timestamp or datetime.now()
        
        with self._buffer_lock:
            self._frame_buffer.append((frame.copy(), ts))
            
            # Eski frame'leri temizle
            cutoff = ts.timestamp() - self._max_buffer_seconds
            self._frame_buffer = [
                (f, t) for f, t in self._frame_buffer
                if t.timestamp() > cutoff
            ]
    
    def extract_clip(
        self,
        event_time: datetime,
        before_seconds: float = 5.0,
        after_seconds: float = 5.0,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Olay zamanı etrafında klip çıkar.
        
        Args:
            event_time: Olay zamanı
            before_seconds: Olaydan önce kaç saniye
            after_seconds: Olaydan sonra kaç saniye
            filename: Dosya adı
        
        Returns:
            Dosya yolu veya None
        """
        with self._buffer_lock:
            # İlgili frame'leri seç
            start_time = event_time.timestamp() - before_seconds
            end_time = event_time.timestamp() + after_seconds
            
            clip_frames = [
                (f, t) for f, t in self._frame_buffer
                if start_time <= t.timestamp() <= end_time
            ]
        
        if not clip_frames:
            logger.warning("Klip için yeterli frame yok")
            return None
        
        # Dosya adı
        if not filename:
            ts = event_time.strftime("%Y%m%d_%H%M%S")
            filename = f"clip_{ts}.{self.config.format.value}"
        
        filepath = str(Path(self.config.output_dir) / filename)
        
        # Video oluştur
        first_frame = clip_frames[0][0]
        h, w = first_frame.shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*self.config.codec.value)
        writer = cv2.VideoWriter(filepath, fourcc, self.config.fps, (w, h))
        
        for frame, _ in clip_frames:
            if frame.shape[:2] != (h, w):
                frame = cv2.resize(frame, (w, h))
            writer.write(frame)
        
        writer.release()
        
        logger.info(f"Klip çıkarıldı: {filepath} ({len(clip_frames)} frame)")
        return filepath
    
    def clear_buffer(self):
        """Buffer'ı temizle."""
        with self._buffer_lock:
            self._frame_buffer.clear()


class VideoPlayer:
    """
    Basit video player sınıfı.
    
    OpenCV ile video oynatma ve kontrol.
    """
    
    def __init__(self):
        """Player'ı başlat."""
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_playing = False
        self._current_frame = 0
        self._total_frames = 0
        self._fps = 30.0
    
    def open(self, filepath: str) -> bool:
        """
        Video dosyasını aç.
        
        Args:
            filepath: Video dosya yolu
        
        Returns:
            Başarılı mı?
        """
        self._cap = cv2.VideoCapture(filepath)
        
        if not self._cap.isOpened():
            logger.error(f"Video açılamadı: {filepath}")
            return False
        
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._current_frame = 0
        
        logger.info(f"Video açıldı: {filepath} ({self._total_frames} frame, {self._fps} FPS)")
        return True
    
    def close(self):
        """Video'yu kapat."""
        if self._cap:
            self._cap.release()
            self._cap = None
        self._is_playing = False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Sonraki frame'i oku."""
        if not self._cap or not self._cap.isOpened():
            return None
        
        ret, frame = self._cap.read()
        if ret:
            self._current_frame = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
            return frame
        return None
    
    def seek(self, frame_number: int) -> bool:
        """Belirli bir frame'e git."""
        if not self._cap:
            return False
        
        frame_number = max(0, min(frame_number, self._total_frames - 1))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self._current_frame = frame_number
        return True
    
    def seek_time(self, seconds: float) -> bool:
        """Belirli bir zamana git."""
        frame_number = int(seconds * self._fps)
        return self.seek(frame_number)
    
    @property
    def position(self) -> int:
        """Mevcut frame pozisyonu."""
        return self._current_frame
    
    @property
    def total_frames(self) -> int:
        """Toplam frame sayısı."""
        return self._total_frames
    
    @property
    def duration(self) -> float:
        """Video süresi (saniye)."""
        return self._total_frames / self._fps if self._fps > 0 else 0
    
    @property
    def fps(self) -> float:
        """Video FPS değeri."""
        return self._fps
    
    def get_info(self) -> Dict[str, Any]:
        """Video bilgilerini getir."""
        if not self._cap:
            return {}
        
        return {
            "total_frames": self._total_frames,
            "fps": self._fps,
            "duration_seconds": round(self.duration, 2),
            "current_frame": self._current_frame,
            "current_time_seconds": round(self._current_frame / self._fps, 2) if self._fps > 0 else 0,
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
