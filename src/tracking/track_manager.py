"""
Track Manager
Track yönetimi ve koordinasyonu
"""

import logging
import time
from typing import List, Optional, Dict, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cv2
import threading

from .tracker_base import TrackerBase, TrackerConfig, Track, TrackState
from .deep_sort import DeepSORTTracker, DeepSORTConfig
from .byte_track import ByteTracker, ByteTrackConfig
from .re_identification import FeatureExtractor, ReIDMatcher, ReIDConfig

logger = logging.getLogger(__name__)


class TrackerType(Enum):
    """Tracker türleri"""
    DEEPSORT = "deepsort"
    BYTETRACK = "bytetrack"
    SIMPLE_IOU = "simple_iou"


@dataclass
class TrackManagerConfig:
    """Track Manager konfigürasyonu"""
    tracker_type: TrackerType = TrackerType.BYTETRACK
    enable_reid: bool = True
    reid_interval: int = 5          # Re-ID kontrol aralığı (frame)
    min_track_length: int = 5       # Minimum track uzunluğu
    save_trajectories: bool = True
    trajectory_buffer: int = 100    # Trajectory buffer boyutu
    enable_zone_tracking: bool = False
    zones: List[Dict] = field(default_factory=list)  # ROI bölgeleri


class SimpleIOUTracker(TrackerBase):
    """Basit IOU tabanlı tracker"""
    
    def __init__(self, config: TrackerConfig):
        super().__init__(config)
    
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        frame: Optional[np.ndarray] = None
    ) -> List[Track]:
        """IOU tabanlı güncelleme"""
        self.increment_frame()
        
        # Basit IOU eşleştirme
        matches, unmatched_tracks, unmatched_dets = self._match_detections(detections)
        
        # Eşleşmeleri güncelle
        track_ids = list(self._tracks.keys())
        for track_idx, det_idx in matches:
            track_id = track_ids[track_idx]
            bbox, conf, class_id = detections[det_idx]
            self.update_track(track_id, bbox, conf)
        
        # Kayıpları işaretle
        for track_idx in unmatched_tracks:
            track_id = track_ids[track_idx]
            self.mark_missed(track_id)
        
        # Yeni track'ler
        for det_idx in unmatched_dets:
            bbox, conf, class_id = detections[det_idx]
            self.create_track(bbox, conf, class_id, "")
        
        self.cleanup()
        return self.confirmed_tracks
    
    def predict(self) -> List[Track]:
        """Basit velocity tabanlı tahmin"""
        for track in self._tracks.values():
            if track.velocity:
                x1, y1, x2, y2 = track.bbox
                vx, vy = track.velocity
                track.bbox = (
                    int(x1 + vx),
                    int(y1 + vy),
                    int(x2 + vx),
                    int(y2 + vy)
                )
        return self.active_tracks
    
    def _match_detections(
        self,
        detections: list
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """IOU tabanlı eşleştirme"""
        if not self._tracks or not detections:
            return [], list(range(len(self._tracks))), list(range(len(detections)))
        
        tracks = list(self._tracks.values())
        
        # IOU matrix
        iou_matrix = np.zeros((len(tracks), len(detections)))
        for t, track in enumerate(tracks):
            for d, (det_bbox, _, _) in enumerate(detections):
                iou_matrix[t, d] = self._calculate_iou(track.bbox, det_bbox)
        
        # Greedy matching
        matches = []
        matched_tracks = set()
        matched_dets = set()
        
        while True:
            # En yüksek IOU'yu bul
            max_iou = 0
            best_match = None
            
            for t in range(len(tracks)):
                if t in matched_tracks:
                    continue
                for d in range(len(detections)):
                    if d in matched_dets:
                        continue
                    if iou_matrix[t, d] > max_iou:
                        max_iou = iou_matrix[t, d]
                        best_match = (t, d)
            
            if best_match is None or max_iou < self.config.iou_threshold:
                break
            
            matches.append(best_match)
            matched_tracks.add(best_match[0])
            matched_dets.add(best_match[1])
        
        unmatched_tracks = [i for i in range(len(tracks)) if i not in matched_tracks]
        unmatched_dets = [i for i in range(len(detections)) if i not in matched_dets]
        
        return matches, unmatched_tracks, unmatched_dets


class TrackManager:
    """
    Track yönetim sınıfı
    Farklı tracker'ları ve Re-ID'yi koordine eder
    """
    
    def __init__(self, config: TrackManagerConfig):
        """
        Args:
            config: Track manager konfigürasyonu
        """
        self.config = config
        
        # Tracker oluştur
        self._tracker = self._create_tracker()
        
        # Re-ID bileşenleri
        self._reid_enabled = config.enable_reid
        self._feature_extractor: Optional[FeatureExtractor] = None
        self._reid_matcher: Optional[ReIDMatcher] = None
        
        if self._reid_enabled:
            self._init_reid()
        
        # Trajectory geçmişi
        self._trajectories: Dict[int, List[Tuple[int, int]]] = {}
        
        # Zone tracking
        self._zones = config.zones if config.enable_zone_tracking else []
        self._zone_events: List[Dict] = []
        
        # İstatistikler
        self._stats = {
            "total_frames": 0,
            "total_tracks": 0,
            "active_tracks": 0,
            "reid_matches": 0,
            "new_identities": 0
        }
        
        # Callbacks
        self._on_new_track: Optional[Callable[[Track], None]] = None
        self._on_track_lost: Optional[Callable[[Track], None]] = None
        self._on_zone_enter: Optional[Callable[[int, str], None]] = None
        self._on_zone_exit: Optional[Callable[[int, str], None]] = None
    
    def _create_tracker(self) -> TrackerBase:
        """Tracker türüne göre oluştur"""
        if self.config.tracker_type == TrackerType.DEEPSORT:
            config = DeepSORTConfig()
            return DeepSORTTracker(config)
        
        elif self.config.tracker_type == TrackerType.BYTETRACK:
            config = ByteTrackConfig()
            return ByteTracker(config)
        
        else:  # SIMPLE_IOU
            config = TrackerConfig()
            return SimpleIOUTracker(config)
    
    def _init_reid(self) -> None:
        """Re-ID bileşenlerini başlat"""
        reid_config = ReIDConfig()
        self._feature_extractor = FeatureExtractor(reid_config)
        self._reid_matcher = ReIDMatcher(reid_config)
        
        # Feature extractor'ı yükle (opsiyonel)
        try:
            self._feature_extractor.load_model()
        except Exception as e:
            logger.warning(f"Feature extractor yüklenemedi, HOG kullanılacak: {e}")
    
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int, str]],
        frame: Optional[np.ndarray] = None
    ) -> List[Track]:
        """
        Track'leri güncelle
        
        Args:
            detections: (bbox, confidence, class_id, class_name) listesi
            frame: Orijinal frame
            
        Returns:
            Aktif track listesi
        """
        self._stats["total_frames"] += 1
        
        # Tracker formatına çevir
        tracker_dets = [(d[0], d[1], d[2]) for d in detections]
        
        # Feature extraction (Re-ID için)
        features = None
        if self._reid_enabled and frame is not None and self._feature_extractor:
            features = self._extract_features(frame, tracker_dets)
        
        # Tracker güncelle
        if isinstance(self._tracker, DeepSORTTracker):
            tracks = self._tracker.update(tracker_dets, frame, features)
        else:
            tracks = self._tracker.update(tracker_dets, frame)
        
        # Re-ID eşleştirme
        if self._reid_enabled and self._reid_matcher and features:
            self._apply_reid(tracks, features, frame)
        
        # Trajectory güncelle
        if self.config.save_trajectories:
            self._update_trajectories(tracks)
        
        # Zone tracking
        if self._zones:
            self._check_zones(tracks)
        
        # İstatistik güncelle
        self._stats["active_tracks"] = len(tracks)
        
        return tracks
    
    def _extract_features(
        self,
        frame: np.ndarray,
        detections: list
    ) -> List[np.ndarray]:
        """Detection'lar için feature çıkar"""
        features = []
        
        for bbox, _, _ in detections:
            x1, y1, x2, y2 = bbox
            
            # ROI çıkar
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            
            if x2 <= x1 or y2 <= y1:
                features.append(np.zeros(512))
                continue
            
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                features.append(np.zeros(512))
                continue
            
            feature = self._feature_extractor.extract(roi)
            features.append(feature)
        
        return features
    
    def _apply_reid(
        self,
        tracks: List[Track],
        features: List[np.ndarray],
        frame: np.ndarray
    ) -> None:
        """Re-ID uygula"""
        frame_id = self._stats["total_frames"]
        
        # Her Re-ID aralığında kontrol et
        if frame_id % self.config.reid_interval != 0:
            return
        
        for i, track in enumerate(tracks):
            if i >= len(features):
                continue
            
            feature = features[i]
            
            # ROI görüntüsünü al
            x1, y1, x2, y2 = track.bbox
            roi = frame[max(0,y1):min(frame.shape[0],y2), max(0,x1):min(frame.shape[1],x2)]
            
            # Eşleştir veya kaydet
            identity_id, is_new = self._reid_matcher.match_or_register(
                feature, roi, frame_id, {"track_id": track.track_id}
            )
            
            # Track metadata güncelle
            track.metadata["reid_id"] = identity_id
            
            if is_new:
                self._stats["new_identities"] += 1
            else:
                self._stats["reid_matches"] += 1
    
    def _update_trajectories(self, tracks: List[Track]) -> None:
        """Track trajectory'lerini güncelle"""
        for track in tracks:
            if track.track_id not in self._trajectories:
                self._trajectories[track.track_id] = []
            
            trajectory = self._trajectories[track.track_id]
            trajectory.append(track.center)
            
            # Buffer sınırı
            if len(trajectory) > self.config.trajectory_buffer:
                trajectory.pop(0)
    
    def _check_zones(self, tracks: List[Track]) -> None:
        """Zone geçişlerini kontrol et"""
        for track in tracks:
            center = track.center
            
            for zone in self._zones:
                zone_id = zone.get("id", "unknown")
                polygon = zone.get("polygon", [])
                
                if not polygon:
                    continue
                
                is_inside = self._point_in_polygon(center, polygon)
                was_inside = track.metadata.get(f"in_zone_{zone_id}", False)
                
                if is_inside and not was_inside:
                    # Zone'a giriş
                    track.metadata[f"in_zone_{zone_id}"] = True
                    self._zone_events.append({
                        "type": "enter",
                        "track_id": track.track_id,
                        "zone_id": zone_id,
                        "frame": self._stats["total_frames"]
                    })
                    
                    if self._on_zone_enter:
                        self._on_zone_enter(track.track_id, zone_id)
                
                elif not is_inside and was_inside:
                    # Zone'dan çıkış
                    track.metadata[f"in_zone_{zone_id}"] = False
                    self._zone_events.append({
                        "type": "exit",
                        "track_id": track.track_id,
                        "zone_id": zone_id,
                        "frame": self._stats["total_frames"]
                    })
                    
                    if self._on_zone_exit:
                        self._on_zone_exit(track.track_id, zone_id)
    
    def _point_in_polygon(
        self,
        point: Tuple[int, int],
        polygon: List[Tuple[int, int]]
    ) -> bool:
        """Noktanın polygon içinde olup olmadığını kontrol et"""
        x, y = point
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def get_trajectory(self, track_id: int) -> List[Tuple[int, int]]:
        """Track trajectory'sini al"""
        return self._trajectories.get(track_id, [])
    
    def get_all_trajectories(self) -> Dict[int, List[Tuple[int, int]]]:
        """Tüm trajectory'leri al"""
        return self._trajectories.copy()
    
    def add_zone(
        self,
        zone_id: str,
        polygon: List[Tuple[int, int]],
        name: str = "",
        metadata: dict = None
    ) -> None:
        """Yeni zone ekle"""
        self._zones.append({
            "id": zone_id,
            "polygon": polygon,
            "name": name,
            "metadata": metadata or {}
        })
    
    def remove_zone(self, zone_id: str) -> bool:
        """Zone'u kaldır"""
        for i, zone in enumerate(self._zones):
            if zone.get("id") == zone_id:
                self._zones.pop(i)
                return True
        return False
    
    def get_zone_events(
        self,
        zone_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """Zone event'lerini al"""
        events = self._zone_events
        
        if zone_id:
            events = [e for e in events if e.get("zone_id") == zone_id]
        
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        
        return events
    
    def draw_tracks(
        self,
        frame: np.ndarray,
        tracks: List[Track],
        draw_trajectory: bool = True,
        draw_bbox: bool = True,
        draw_id: bool = True
    ) -> np.ndarray:
        """
        Track'leri frame üzerine çiz
        
        Args:
            frame: Giriş frame'i
            tracks: Track listesi
            draw_trajectory: Trajectory çiz
            draw_bbox: Bounding box çiz
            draw_id: Track ID göster
            
        Returns:
            Çizilmiş frame
        """
        frame = frame.copy()
        
        # Renk paleti
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (128, 0, 0), (0, 128, 0), (0, 0, 128)
        ]
        
        for track in tracks:
            color = colors[track.track_id % len(colors)]
            
            if draw_bbox:
                x1, y1, x2, y2 = track.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            if draw_id:
                x1, y1, _, _ = track.bbox
                label = f"ID:{track.track_id}"
                
                if "reid_id" in track.metadata:
                    label += f" R:{track.metadata['reid_id']}"
                
                cv2.putText(
                    frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                )
            
            if draw_trajectory:
                trajectory = self.get_trajectory(track.track_id)
                if len(trajectory) > 1:
                    pts = np.array(trajectory, dtype=np.int32)
                    cv2.polylines(frame, [pts], False, color, 2)
        
        # Zone'ları çiz
        for zone in self._zones:
            polygon = zone.get("polygon", [])
            if polygon:
                pts = np.array(polygon, dtype=np.int32)
                cv2.polylines(frame, [pts], True, (255, 255, 0), 2)
                
                # Zone adını yaz
                if zone.get("name"):
                    cv2.putText(
                        frame, zone["name"], polygon[0],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2
                    )
        
        return frame
    
    def set_callbacks(
        self,
        on_new_track: Callable[[Track], None] = None,
        on_track_lost: Callable[[Track], None] = None,
        on_zone_enter: Callable[[int, str], None] = None,
        on_zone_exit: Callable[[int, str], None] = None
    ) -> None:
        """Event callback'lerini ayarla"""
        self._on_new_track = on_new_track
        self._on_track_lost = on_track_lost
        self._on_zone_enter = on_zone_enter
        self._on_zone_exit = on_zone_exit
    
    def get_statistics(self) -> dict:
        """İstatistikleri al"""
        stats = self._stats.copy()
        stats["tracker_stats"] = self._tracker.stats
        
        if self._reid_matcher:
            stats["reid_stats"] = self._reid_matcher.get_statistics()
        
        return stats
    
    def reset(self) -> None:
        """Manager'ı sıfırla"""
        self._tracker.reset()
        self._trajectories.clear()
        self._zone_events.clear()
        
        if self._reid_matcher:
            self._reid_matcher.clear()
        
        self._stats = {
            "total_frames": 0,
            "total_tracks": 0,
            "active_tracks": 0,
            "reid_matches": 0,
            "new_identities": 0
        }
        
        logger.info("TrackManager sıfırlandı")
    
    def save_state(self, path: str) -> bool:
        """Durumu kaydet"""
        try:
            import pickle
            
            state = {
                "stats": self._stats,
                "trajectories": self._trajectories,
                "zone_events": self._zone_events
            }
            
            with open(path, 'wb') as f:
                pickle.dump(state, f)
            
            # Re-ID gallery'yi ayrı kaydet
            if self._reid_matcher:
                self._reid_matcher.save_gallery(path + ".reid")
            
            logger.info(f"Durum kaydedildi: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Durum kaydetme hatası: {e}")
            return False
    
    def load_state(self, path: str) -> bool:
        """Durumu yükle"""
        try:
            import pickle
            
            with open(path, 'rb') as f:
                state = pickle.load(f)
            
            self._stats = state.get("stats", self._stats)
            self._trajectories = state.get("trajectories", {})
            self._zone_events = state.get("zone_events", [])
            
            # Re-ID gallery'yi yükle
            if self._reid_matcher:
                self._reid_matcher.load_gallery(path + ".reid")
            
            logger.info(f"Durum yüklendi: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Durum yükleme hatası: {e}")
            return False
