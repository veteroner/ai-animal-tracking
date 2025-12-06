"""
Tracker Base
Temel tracker sınıfı - tüm tracker implementasyonları için abstract base class
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class TrackState(Enum):
    """Track durumu"""
    TENTATIVE = "tentative"     # Yeni, henüz onaylanmamış
    CONFIRMED = "confirmed"      # Onaylanmış aktif track
    DELETED = "deleted"          # Silinmiş/kayıp track


@dataclass
class Track:
    """Tek bir nesnenin track bilgisi"""
    track_id: int
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str
    state: TrackState = TrackState.TENTATIVE
    age: int = 0                     # Track yaşı (frame sayısı)
    hits: int = 0                    # Başarılı eşleşme sayısı
    time_since_update: int = 0       # Son güncellemeden beri geçen frame
    features: Optional[np.ndarray] = None
    velocity: Optional[Tuple[float, float]] = None
    history: List[Tuple[int, int, int, int]] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Track merkezi"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def is_confirmed(self) -> bool:
        return self.state == TrackState.CONFIRMED
    
    def to_dict(self) -> dict:
        """Dictionary'e çevir"""
        return {
            "track_id": self.track_id,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "state": self.state.value,
            "age": self.age,
            "hits": self.hits,
            "time_since_update": self.time_since_update,
            "center": self.center,
            "velocity": self.velocity,
            "metadata": self.metadata
        }


@dataclass
class TrackerConfig:
    """Tracker konfigürasyonu"""
    max_age: int = 30               # Track kaybolmadan önce max frame sayısı
    min_hits: int = 3               # Onay için minimum eşleşme sayısı
    iou_threshold: float = 0.3      # IOU eşik değeri
    max_tracks: int = 100           # Maksimum aktif track sayısı
    track_buffer: int = 30          # Track geçmiş buffer boyutu
    use_appearance: bool = False    # Görünüm özelliklerini kullan
    appearance_threshold: float = 0.7


class TrackerBase(ABC):
    """
    Temel Tracker sınıfı
    Tüm tracker implementasyonları bu sınıftan türetilir
    """
    
    def __init__(self, config: TrackerConfig):
        """
        Args:
            config: Tracker konfigürasyonu
        """
        self.config = config
        self._tracks: Dict[int, Track] = {}
        self._next_id = 1
        self._frame_count = 0
        
        # İstatistikler
        self._stats = {
            "total_tracks_created": 0,
            "active_tracks": 0,
            "confirmed_tracks": 0,
            "avg_track_length": 0.0,
            "total_frames": 0
        }
    
    @property
    def tracks(self) -> Dict[int, Track]:
        """Aktif track'ler"""
        return self._tracks
    
    @property
    def active_tracks(self) -> List[Track]:
        """Aktif track listesi"""
        return list(self._tracks.values())
    
    @property
    def confirmed_tracks(self) -> List[Track]:
        """Onaylanmış track listesi"""
        return [t for t in self._tracks.values() if t.is_confirmed]
    
    @property
    def stats(self) -> dict:
        """İstatistikler"""
        self._stats["active_tracks"] = len(self._tracks)
        self._stats["confirmed_tracks"] = len(self.confirmed_tracks)
        return self._stats.copy()
    
    @abstractmethod
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        frame: Optional[np.ndarray] = None
    ) -> List[Track]:
        """
        Tracker'ı yeni tespitlerle güncelle
        
        Args:
            detections: (bbox, confidence, class_id) tuple listesi
            frame: Görünüm özellikleri için orijinal frame
            
        Returns:
            Güncellenmiş track listesi
        """
        pass
    
    @abstractmethod
    def predict(self) -> List[Track]:
        """
        Track pozisyonlarını tahmin et (Kalman filter vb.)
        
        Returns:
            Tahmin edilmiş track listesi
        """
        pass
    
    def create_track(
        self,
        bbox: Tuple[int, int, int, int],
        confidence: float,
        class_id: int,
        class_name: str = "",
        features: Optional[np.ndarray] = None
    ) -> Track:
        """
        Yeni track oluştur
        
        Args:
            bbox: Bounding box
            confidence: Tespit confidence'ı
            class_id: Sınıf ID'si
            class_name: Sınıf adı
            features: Görünüm özellikleri
            
        Returns:
            Yeni Track objesi
        """
        track = Track(
            track_id=self._next_id,
            bbox=bbox,
            confidence=confidence,
            class_id=class_id,
            class_name=class_name,
            features=features,
            state=TrackState.TENTATIVE,
            age=1,
            hits=1
        )
        
        self._tracks[self._next_id] = track
        self._next_id += 1
        self._stats["total_tracks_created"] += 1
        
        logger.debug(f"Yeni track oluşturuldu: {track.track_id}")
        return track
    
    def delete_track(self, track_id: int) -> None:
        """Track'i sil"""
        if track_id in self._tracks:
            del self._tracks[track_id]
            logger.debug(f"Track silindi: {track_id}")
    
    def update_track(
        self,
        track_id: int,
        bbox: Tuple[int, int, int, int],
        confidence: float,
        features: Optional[np.ndarray] = None
    ) -> Optional[Track]:
        """
        Mevcut track'i güncelle
        
        Args:
            track_id: Track ID'si
            bbox: Yeni bounding box
            confidence: Yeni confidence
            features: Yeni özellikler
            
        Returns:
            Güncellenmiş Track veya None
        """
        track = self._tracks.get(track_id)
        if not track:
            return None
        
        # Velocity hesapla
        old_center = track.center
        track.bbox = bbox
        new_center = track.center
        
        track.velocity = (
            new_center[0] - old_center[0],
            new_center[1] - old_center[1]
        )
        
        track.confidence = confidence
        track.hits += 1
        track.time_since_update = 0
        track.age += 1
        
        # Geçmişe ekle
        if len(track.history) >= self.config.track_buffer:
            track.history.pop(0)
        track.history.append(bbox)
        
        # Özellik güncelle
        if features is not None:
            track.features = features
        
        # Durumu kontrol et
        if track.hits >= self.config.min_hits:
            track.state = TrackState.CONFIRMED
        
        return track
    
    def mark_missed(self, track_id: int) -> None:
        """Track'i kaçırılmış olarak işaretle"""
        track = self._tracks.get(track_id)
        if track:
            track.time_since_update += 1
            track.age += 1
            
            if track.time_since_update > self.config.max_age:
                track.state = TrackState.DELETED
                self.delete_track(track_id)
    
    def cleanup(self) -> None:
        """Eski track'leri temizle"""
        to_delete = []
        
        for track_id, track in self._tracks.items():
            if track.state == TrackState.DELETED:
                to_delete.append(track_id)
            elif track.time_since_update > self.config.max_age:
                to_delete.append(track_id)
        
        for track_id in to_delete:
            self.delete_track(track_id)
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """Track'i ID ile al"""
        return self._tracks.get(track_id)
    
    def get_track_by_bbox(
        self,
        bbox: Tuple[int, int, int, int],
        iou_threshold: float = 0.5
    ) -> Optional[Track]:
        """
        Bounding box ile eşleşen track'i bul
        
        Args:
            bbox: Aranacak bbox
            iou_threshold: Minimum IOU
            
        Returns:
            Eşleşen Track veya None
        """
        best_track = None
        best_iou = 0.0
        
        for track in self._tracks.values():
            iou = self._calculate_iou(bbox, track.bbox)
            if iou > best_iou and iou >= iou_threshold:
                best_iou = iou
                best_track = track
        
        return best_track
    
    def _calculate_iou(
        self,
        box1: Tuple[int, int, int, int],
        box2: Tuple[int, int, int, int]
    ) -> float:
        """İki bbox arasındaki IOU'yu hesapla"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def reset(self) -> None:
        """Tracker'ı sıfırla"""
        self._tracks.clear()
        self._next_id = 1
        self._frame_count = 0
        logger.info("Tracker sıfırlandı")
    
    def increment_frame(self) -> None:
        """Frame sayacını artır"""
        self._frame_count += 1
        self._stats["total_frames"] = self._frame_count


class HungarianMatcher:
    """Hungarian algoritması ile track-detection eşleştirme"""
    
    @staticmethod
    def match(
        tracks: List[Track],
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        iou_threshold: float = 0.3
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Track'leri detection'larla eşleştir
        
        Args:
            tracks: Mevcut track listesi
            detections: Yeni detection'lar
            iou_threshold: Minimum IOU eşik değeri
            
        Returns:
            (matches, unmatched_tracks, unmatched_detections)
            - matches: [(track_idx, detection_idx), ...]
            - unmatched_tracks: Eşleşmeyen track indeksleri
            - unmatched_detections: Eşleşmeyen detection indeksleri
        """
        if not tracks or not detections:
            return [], list(range(len(tracks))), list(range(len(detections)))
        
        # IOU matrisini hesapla
        iou_matrix = np.zeros((len(tracks), len(detections)))
        
        for t_idx, track in enumerate(tracks):
            for d_idx, (det_bbox, _, _) in enumerate(detections):
                iou_matrix[t_idx, d_idx] = HungarianMatcher._calculate_iou(
                    track.bbox, det_bbox
                )
        
        # Hungarian algoritması
        try:
            from scipy.optimize import linear_sum_assignment
            
            # Maliyet matrisi (1 - IOU)
            cost_matrix = 1 - iou_matrix
            row_indices, col_indices = linear_sum_assignment(cost_matrix)
            
            matches = []
            unmatched_tracks = list(range(len(tracks)))
            unmatched_detections = list(range(len(detections)))
            
            for row, col in zip(row_indices, col_indices):
                if iou_matrix[row, col] >= iou_threshold:
                    matches.append((row, col))
                    unmatched_tracks.remove(row)
                    unmatched_detections.remove(col)
            
            return matches, unmatched_tracks, unmatched_detections
            
        except ImportError:
            # Scipy yoksa basit greedy matching
            return HungarianMatcher._greedy_match(
                tracks, detections, iou_matrix, iou_threshold
            )
    
    @staticmethod
    def _greedy_match(
        tracks: List[Track],
        detections: list,
        iou_matrix: np.ndarray,
        iou_threshold: float
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Basit greedy eşleştirme"""
        matches = []
        matched_tracks = set()
        matched_detections = set()
        
        # IOU'ya göre sırala
        indices = np.dstack(np.unravel_index(
            np.argsort(iou_matrix.ravel())[::-1],
            iou_matrix.shape
        ))[0]
        
        for t_idx, d_idx in indices:
            if t_idx in matched_tracks or d_idx in matched_detections:
                continue
            
            if iou_matrix[t_idx, d_idx] >= iou_threshold:
                matches.append((t_idx, d_idx))
                matched_tracks.add(t_idx)
                matched_detections.add(d_idx)
        
        unmatched_tracks = [i for i in range(len(tracks)) if i not in matched_tracks]
        unmatched_detections = [i for i in range(len(detections)) if i not in matched_detections]
        
        return matches, unmatched_tracks, unmatched_detections
    
    @staticmethod
    def _calculate_iou(box1: tuple, box2: tuple) -> float:
        """IOU hesapla"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        
        return inter / union if union > 0 else 0.0
