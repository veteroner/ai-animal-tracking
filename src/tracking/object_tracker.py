"""
AI Animal Tracking System - Object Tracker
===========================================

Multi-object tracking için ByteTrack tabanlı tracker.
YOLOv8'in dahili tracker'ını kullanır.
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from src.detection.yolo_detector import Detection, DetectionResult


logger = logging.getLogger("animal_tracking.tracking")


# ===========================================
# Data Classes
# ===========================================

@dataclass
class TrackState:
    """Track durumu"""
    TENTATIVE = 1      # Yeni, doğrulanmamış
    CONFIRMED = 2      # Doğrulanmış, aktif
    DELETED = 3        # Silindi


@dataclass
class TrackerConfig:
    """Tracker konfigürasyonu"""
    tracker_type: str = "bytetrack"  # bytetrack, botsort
    track_high_thresh: float = 0.5   # Yüksek güvenli tespit eşiği
    track_low_thresh: float = 0.1    # Düşük güvenli tespit eşiği
    new_track_thresh: float = 0.6    # Yeni track oluşturma eşiği
    track_buffer: int = 30           # Kayıp track'leri tutma süresi (frame)
    match_thresh: float = 0.8        # IOU matching eşiği
    max_time_lost: int = 30          # Max kayıp süre (frame)
    min_hits: int = 3                # Min doğrulama için hit sayısı


@dataclass
class Track:
    """Tek bir track nesnesi"""
    track_id: int
    class_id: int
    class_name: str
    
    # Son konum
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    confidence: float
    
    # Geçmiş
    history: List[Tuple[int, int]] = field(default_factory=list)  # Merkez noktaları
    
    # İstatistikler
    first_seen_frame: int = 0
    last_seen_frame: int = 0
    total_frames: int = 0
    
    # Durum
    state: int = TrackState.TENTATIVE
    time_since_update: int = 0
    hits: int = 0
    
    # Hareket bilgileri
    velocity: Optional[Tuple[float, float]] = None  # vx, vy
    direction: Optional[float] = None  # Derece cinsinden yön
    
    @property
    def is_confirmed(self) -> bool:
        return self.state == TrackState.CONFIRMED
    
    @property
    def is_active(self) -> bool:
        return self.state != TrackState.DELETED
    
    @property
    def age(self) -> int:
        """Track yaşı (frame sayısı)"""
        return self.last_seen_frame - self.first_seen_frame
    
    @property
    def track_length(self) -> int:
        """Trajectory uzunluğu"""
        return len(self.history)
    
    def update_velocity(self):
        """Hız ve yön hesapla"""
        if len(self.history) < 2:
            self.velocity = (0.0, 0.0)
            self.direction = 0.0
            return
        
        # Son iki nokta arasındaki fark
        p1 = self.history[-2]
        p2 = self.history[-1]
        
        vx = p2[0] - p1[0]
        vy = p2[1] - p1[1]
        
        self.velocity = (float(vx), float(vy))
        
        # Yön (derece)
        if vx != 0 or vy != 0:
            self.direction = float(np.degrees(np.arctan2(vy, vx)))
        else:
            self.direction = 0.0
    
    def to_dict(self) -> dict:
        """Dictionary'e dönüştür"""
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "bbox": self.bbox,
            "center": self.center,
            "confidence": round(self.confidence, 4),
            "age": self.age,
            "total_frames": self.total_frames,
            "track_length": self.track_length,
            "velocity": self.velocity,
            "direction": round(self.direction, 2) if self.direction else None,
            "is_confirmed": self.is_confirmed,
        }


@dataclass
class TrackingResult:
    """Tracking sonuçları"""
    tracks: List[Track]
    frame_id: int
    timestamp: float
    
    # Detection sonuçları (opsiyonel)
    detections: Optional[List[Detection]] = None
    
    @property
    def count(self) -> int:
        return len(self.tracks)
    
    @property
    def active_tracks(self) -> List[Track]:
        return [t for t in self.tracks if t.is_active]
    
    @property
    def confirmed_tracks(self) -> List[Track]:
        return [t for t in self.tracks if t.is_confirmed]
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """Track ID'ye göre track bul"""
        for track in self.tracks:
            if track.track_id == track_id:
                return track
        return None
    
    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "active_count": len(self.active_tracks),
            "confirmed_count": len(self.confirmed_tracks),
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "tracks": [t.to_dict() for t in self.tracks],
        }


# ===========================================
# Object Tracker Class
# ===========================================

class ObjectTracker:
    """
    Multi-object tracker.
    
    YOLO'nun dahili ByteTrack/BoTSORT tracker'ını kullanır ve
    ek track yönetimi sağlar.
    
    Kullanım:
        from src.detection import YOLODetector
        
        detector = YOLODetector()
        tracker = ObjectTracker()
        
        # Frame işle
        detection_result = detector.track(frame)  # YOLO tracking
        tracking_result = tracker.update(detection_result)
        
        for track in tracking_result.tracks:
            print(f"Track {track.track_id}: {track.class_name}")
    """
    
    def __init__(self, config: Optional[TrackerConfig] = None):
        """
        Args:
            config: TrackerConfig nesnesi
        """
        self.config = config or TrackerConfig()
        
        # Track'ler
        self._tracks: Dict[int, Track] = {}
        self._deleted_tracks: Dict[int, Track] = {}
        
        # ID yönetimi
        self._next_id: int = 1
        
        # Frame sayacı
        self._frame_id: int = 0
        
        # İstatistikler
        self._total_tracks_created: int = 0
        self._total_tracks_deleted: int = 0
    
    @property
    def active_track_count(self) -> int:
        """Aktif track sayısı"""
        return sum(1 for t in self._tracks.values() if t.is_active)
    
    @property
    def confirmed_track_count(self) -> int:
        """Doğrulanmış track sayısı"""
        return sum(1 for t in self._tracks.values() if t.is_confirmed)
    
    @property
    def statistics(self) -> dict:
        """Tracker istatistikleri"""
        return {
            "active_tracks": self.active_track_count,
            "confirmed_tracks": self.confirmed_track_count,
            "total_tracks_created": self._total_tracks_created,
            "total_tracks_deleted": self._total_tracks_deleted,
            "frame_count": self._frame_id,
        }
    
    def update(self, detection_result: DetectionResult) -> TrackingResult:
        """
        Track'leri güncelle.
        
        Args:
            detection_result: YOLO detection/tracking sonucu
            
        Returns:
            TrackingResult
        """
        self._frame_id += 1
        timestamp = time.time()
        
        # Mevcut track'leri güncelle
        seen_ids = set()
        
        for det in detection_result.detections:
            track_id = det.track_id
            
            if track_id is None:
                continue
            
            seen_ids.add(track_id)
            
            if track_id in self._tracks:
                # Mevcut track'i güncelle
                self._update_track(track_id, det)
            else:
                # Yeni track oluştur
                self._create_track(track_id, det)
        
        # Görülmeyen track'leri işle
        self._handle_missing_tracks(seen_ids)
        
        # Eski track'leri sil
        self._cleanup_tracks()
        
        # Sonuç
        tracks = list(self._tracks.values())
        
        return TrackingResult(
            tracks=tracks,
            frame_id=self._frame_id,
            timestamp=timestamp,
            detections=detection_result.detections,
        )
    
    def _create_track(self, track_id: int, detection: Detection):
        """Yeni track oluştur"""
        track = Track(
            track_id=track_id,
            class_id=detection.class_id,
            class_name=detection.class_name,
            bbox=detection.bbox,
            center=detection.center,
            confidence=detection.confidence,
            history=[detection.center],
            first_seen_frame=self._frame_id,
            last_seen_frame=self._frame_id,
            total_frames=1,
            state=TrackState.TENTATIVE,
            hits=1,
        )
        
        self._tracks[track_id] = track
        self._total_tracks_created += 1
        self._next_id = max(self._next_id, track_id + 1)
        
        logger.debug(f"Created new track: {track_id} ({detection.class_name})")
    
    def _update_track(self, track_id: int, detection: Detection):
        """Mevcut track'i güncelle"""
        track = self._tracks[track_id]
        
        # Konum güncelle
        track.bbox = detection.bbox
        track.center = detection.center
        track.confidence = detection.confidence
        
        # Geçmiş ekle
        track.history.append(detection.center)
        
        # Max history uzunluğu (performans için)
        max_history = 300
        if len(track.history) > max_history:
            track.history = track.history[-max_history:]
        
        # İstatistikler
        track.last_seen_frame = self._frame_id
        track.total_frames += 1
        track.time_since_update = 0
        track.hits += 1
        
        # Durum güncelle
        if track.hits >= self.config.min_hits:
            track.state = TrackState.CONFIRMED
        
        # Velocity güncelle
        track.update_velocity()
    
    def _handle_missing_tracks(self, seen_ids: set):
        """Görülmeyen track'leri işle"""
        for track_id, track in self._tracks.items():
            if track_id not in seen_ids and track.is_active:
                track.time_since_update += 1
    
    def _cleanup_tracks(self):
        """Eski track'leri temizle"""
        to_delete = []
        
        for track_id, track in self._tracks.items():
            if track.time_since_update > self.config.max_time_lost:
                track.state = TrackState.DELETED
                to_delete.append(track_id)
        
        for track_id in to_delete:
            self._deleted_tracks[track_id] = self._tracks.pop(track_id)
            self._total_tracks_deleted += 1
            logger.debug(f"Deleted track: {track_id}")
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """
        Track ID'ye göre track al.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track veya None
        """
        return self._tracks.get(track_id) or self._deleted_tracks.get(track_id)
    
    def get_track_history(self, track_id: int) -> Optional[List[Tuple[int, int]]]:
        """
        Track'in hareket geçmişini al.
        
        Args:
            track_id: Track ID
            
        Returns:
            Merkez noktaları listesi veya None
        """
        track = self.get_track(track_id)
        return track.history if track else None
    
    def reset(self):
        """Tracker'ı sıfırla"""
        self._tracks.clear()
        self._deleted_tracks.clear()
        self._next_id = 1
        self._frame_id = 0
        self._total_tracks_created = 0
        self._total_tracks_deleted = 0
        logger.info("Tracker reset")


# ===========================================
# Trajectory Analyzer
# ===========================================

class TrajectoryAnalyzer:
    """
    Track trajectory'lerini analiz eder.
    
    - Hareket paterni tespiti
    - Hız hesaplama
    - Yön değişimi tespiti
    - Bölge giriş/çıkış tespiti
    """
    
    def __init__(self, fps: float = 30.0):
        """
        Args:
            fps: Video FPS değeri (hız hesabı için)
        """
        self.fps = fps
    
    def calculate_speed(self, track: Track, pixels_per_meter: float = 100.0) -> float:
        """
        Track'in hızını hesapla (m/s).
        
        Args:
            track: Track nesnesi
            pixels_per_meter: Piksel/metre dönüşümü
            
        Returns:
            Hız (m/s)
        """
        if track.velocity is None:
            return 0.0
        
        vx, vy = track.velocity
        pixel_speed = np.sqrt(vx**2 + vy**2)  # pixel/frame
        
        # m/s'ye dönüştür
        speed_mps = (pixel_speed * self.fps) / pixels_per_meter
        
        return float(speed_mps)
    
    def calculate_total_distance(
        self,
        track: Track,
        pixels_per_meter: float = 100.0
    ) -> float:
        """
        Track'in toplam kat ettiği mesafeyi hesapla (metre).
        
        Args:
            track: Track nesnesi
            pixels_per_meter: Piksel/metre dönüşümü
            
        Returns:
            Toplam mesafe (metre)
        """
        if len(track.history) < 2:
            return 0.0
        
        total_pixels = 0.0
        for i in range(1, len(track.history)):
            p1 = track.history[i-1]
            p2 = track.history[i]
            dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_pixels += dist
        
        return total_pixels / pixels_per_meter
    
    def detect_stationary(
        self,
        track: Track,
        threshold_pixels: float = 10.0,
        min_frames: int = 30
    ) -> bool:
        """
        Track'in durağan olup olmadığını tespit et.
        
        Args:
            track: Track nesnesi
            threshold_pixels: Hareket eşiği (piksel)
            min_frames: Minimum frame sayısı
            
        Returns:
            Durağan ise True
        """
        if len(track.history) < min_frames:
            return False
        
        recent = track.history[-min_frames:]
        
        # Bounding box hesapla
        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]
        
        movement = max(max(xs) - min(xs), max(ys) - min(ys))
        
        return movement < threshold_pixels
    
    def is_in_zone(
        self,
        track: Track,
        zone: Tuple[int, int, int, int]  # x1, y1, x2, y2
    ) -> bool:
        """
        Track'in belirtilen bölgede olup olmadığını kontrol et.
        
        Args:
            track: Track nesnesi
            zone: Bölge koordinatları (x1, y1, x2, y2)
            
        Returns:
            Bölgedeyse True
        """
        cx, cy = track.center
        x1, y1, x2, y2 = zone
        
        return x1 <= cx <= x2 and y1 <= cy <= y2


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import sys
    import cv2
    
    sys.path.insert(0, "/Users/onerozbey/Desktop/ai_goruntu_isleme")
    
    from src.detection import YOLODetector
    
    logging.basicConfig(level=logging.INFO)
    
    # Detector ve Tracker oluştur
    detector = YOLODetector(
        model_path="yolov8n.pt",
        confidence_threshold=0.5,
        only_animals=False,
    )
    
    tracker = ObjectTracker()
    analyzer = TrajectoryAnalyzer(fps=30)
    
    # Warmup
    detector.warmup()
    
    # Webcam
    cap = cv2.VideoCapture(0)
    
    print("\nPress 'q' to quit, 'r' to reset tracker")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # YOLO tracking
            detection_result = detector.track(frame)
            
            # Object tracker update
            tracking_result = tracker.update(detection_result)
            
            # Çiz
            output = detector.draw_detections(frame, detection_result)
            
            # Trajectory'leri çiz
            for track in tracking_result.tracks:
                if len(track.history) > 1:
                    points = np.array(track.history, dtype=np.int32)
                    cv2.polylines(output, [points], False, (0, 255, 255), 2)
            
            # Bilgi
            info = f"Tracks: {tracking_result.count} | " \
                   f"Confirmed: {len(tracking_result.confirmed_tracks)} | " \
                   f"FPS: {1000/detection_result.inference_time:.1f}"
            
            cv2.putText(output, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow("Object Tracking Test", output)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                tracker.reset()
                detector.reset_tracker()
                print("Tracker reset")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        print("\n=== Tracker Statistics ===")
        for k, v in tracker.statistics.items():
            print(f"{k}: {v}")
