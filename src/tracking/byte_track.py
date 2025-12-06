"""
ByteTrack Tracker
ByteTrack: Multi-Object Tracking by Associating Every Detection Box
"""

import numpy as np
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment

from .tracker_base import TrackerBase, TrackerConfig, Track, TrackState

logger = logging.getLogger(__name__)


@dataclass
class ByteTrackConfig(TrackerConfig):
    """ByteTrack konfigürasyonu"""
    track_thresh: float = 0.5       # Yüksek confidence eşiği
    track_buffer: int = 30          # Track buffer boyutu
    match_thresh: float = 0.8       # IOU eşleştirme eşiği
    low_thresh: float = 0.1         # Düşük confidence eşiği
    new_track_thresh: float = 0.6   # Yeni track oluşturma eşiği


class STrack:
    """ByteTrack için Single Track sınıfı"""
    
    _count = 0
    
    def __init__(
        self,
        bbox: Tuple[int, int, int, int],
        score: float,
        class_id: int
    ):
        """
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            score: Detection score
            class_id: Sınıf ID'si
        """
        self.track_id = 0  # Henüz atanmadı
        self._bbox = bbox
        self.score = score
        self.class_id = class_id
        
        self.is_activated = False
        self.state = TrackState.TENTATIVE
        
        self.frame_id = 0
        self.start_frame = 0
        self.tracklet_len = 0
        
        # Kalman filter state
        self.mean = None
        self.covariance = None
        
        self._init_kalman()
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return self._bbox
    
    @bbox.setter
    def bbox(self, value: Tuple[int, int, int, int]):
        self._bbox = value
    
    @property
    def tlwh(self) -> np.ndarray:
        """Top-left width height formatı"""
        x1, y1, x2, y2 = self._bbox
        return np.array([x1, y1, x2 - x1, y2 - y1])
    
    @property
    def tlbr(self) -> np.ndarray:
        """Top-left bottom-right formatı"""
        return np.array(self._bbox)
    
    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self._bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def _init_kalman(self):
        """Basit Kalman state initialization"""
        x1, y1, x2, y2 = self._bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        
        # State: [cx, cy, w, h, vx, vy, vw, vh]
        self.mean = np.array([cx, cy, w, h, 0, 0, 0, 0], dtype=np.float32)
        self.covariance = np.eye(8, dtype=np.float32)
    
    def predict(self):
        """Kalman prediction"""
        if self.mean is None:
            return
        
        # Basit prediction: state + velocity
        self.mean[:4] += self.mean[4:8]
        
        # Update bbox
        cx, cy, w, h = self.mean[:4]
        self._bbox = (
            int(cx - w / 2),
            int(cy - h / 2),
            int(cx + w / 2),
            int(cy + h / 2)
        )
    
    def update(self, new_bbox: Tuple[int, int, int, int], score: float):
        """Kalman update"""
        old_center = self.center
        self._bbox = new_bbox
        new_center = self.center
        
        # Velocity güncelle
        self.mean[4] = new_center[0] - old_center[0]
        self.mean[5] = new_center[1] - old_center[1]
        
        # State güncelle
        x1, y1, x2, y2 = new_bbox
        self.mean[0] = (x1 + x2) / 2
        self.mean[1] = (y1 + y2) / 2
        self.mean[2] = x2 - x1
        self.mean[3] = y2 - y1
        
        self.score = score
        self.tracklet_len += 1
    
    def activate(self, frame_id: int):
        """Track'i aktive et"""
        STrack._count += 1
        self.track_id = STrack._count
        
        self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id
        self.state = TrackState.CONFIRMED
    
    def re_activate(self, new_bbox: Tuple[int, int, int, int], score: float, frame_id: int):
        """Kayıp track'i yeniden aktive et"""
        self.update(new_bbox, score)
        self.is_activated = True
        self.frame_id = frame_id
        self.state = TrackState.CONFIRMED
    
    def mark_lost(self):
        """Track'i kayıp olarak işaretle"""
        self.state = TrackState.TENTATIVE
    
    def mark_removed(self):
        """Track'i silinmiş olarak işaretle"""
        self.state = TrackState.DELETED
    
    @staticmethod
    def reset_id():
        """ID sayacını sıfırla"""
        STrack._count = 0


class ByteTracker(TrackerBase):
    """
    ByteTrack implementasyonu
    
    Özellikler:
    - Yüksek ve düşük confidence detection'ları ayrı işler
    - İki aşamalı association
    - Kayıp track'leri düşük confidence ile kurtarır
    """
    
    def __init__(self, config: ByteTrackConfig):
        """
        Args:
            config: ByteTrack konfigürasyonu
        """
        super().__init__(config)
        self.config: ByteTrackConfig = config
        
        # Track havuzları
        self._tracked_stracks: List[STrack] = []  # Aktif track'ler
        self._lost_stracks: List[STrack] = []     # Kayıp track'ler
        self._removed_stracks: List[STrack] = []  # Silinen track'ler
    
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        frame: Optional[np.ndarray] = None
    ) -> List[Track]:
        """
        ByteTrack güncelleme
        
        Args:
            detections: (bbox, score, class_id) listesi
            frame: Orijinal frame (kullanılmıyor)
            
        Returns:
            Aktif track listesi
        """
        self.increment_frame()
        
        # Detection'ları score'a göre ayır
        high_dets = []  # Yüksek confidence
        low_dets = []   # Düşük confidence
        
        for det in detections:
            bbox, score, class_id = det
            if score >= self.config.track_thresh:
                high_dets.append(det)
            elif score >= self.config.low_thresh:
                low_dets.append(det)
        
        # Aktif track'leri predict et
        for strack in self._tracked_stracks:
            strack.predict()
        
        for strack in self._lost_stracks:
            strack.predict()
        
        # ========== İlk Association: Yüksek confidence ==========
        # Tracked + Lost stracks vs High detections
        strack_pool = self._tracked_stracks + self._lost_stracks
        
        # IOU matching
        matches, u_tracks, u_dets_high = self._linear_assignment(
            strack_pool, high_dets, self.config.match_thresh
        )
        
        # Eşleşmeleri güncelle
        for itrack, idet in matches:
            track = strack_pool[itrack]
            bbox, score, _ = high_dets[idet]
            
            if track.state == TrackState.CONFIRMED:
                track.update(bbox, score)
                track.frame_id = self._frame_count
            else:
                track.re_activate(bbox, score, self._frame_count)
        
        # ========== İkinci Association: Düşük confidence ==========
        # Kalan tracked stracks vs Low detections
        r_tracked_stracks = [strack_pool[i] for i in u_tracks if strack_pool[i].state == TrackState.CONFIRMED]
        
        matches, u_tracks_remain, u_dets_low = self._linear_assignment(
            r_tracked_stracks, low_dets, 0.5
        )
        
        for itrack, idet in matches:
            track = r_tracked_stracks[itrack]
            bbox, score, _ = low_dets[idet]
            track.update(bbox, score)
            track.frame_id = self._frame_count
        
        # Eşleşmeyen track'leri kayıp olarak işaretle
        for itrack in u_tracks_remain:
            track = r_tracked_stracks[itrack]
            if track.frame_id != self._frame_count:
                track.mark_lost()
                self._lost_stracks.append(track)
        
        # ========== Yeni Track'ler Oluştur ==========
        for idet in u_dets_high:
            bbox, score, class_id = high_dets[idet]
            if score >= self.config.new_track_thresh:
                new_track = STrack(bbox, score, class_id)
                new_track.activate(self._frame_count)
                self._tracked_stracks.append(new_track)
        
        # ========== Track Havuzlarını Güncelle ==========
        # Tracked: Aktif olanlar
        self._tracked_stracks = [t for t in self._tracked_stracks if t.state == TrackState.CONFIRMED]
        
        # Lost: Kayıp olanları kontrol et
        self._lost_stracks = [
            t for t in self._lost_stracks 
            if t.state != TrackState.DELETED and 
            self._frame_count - t.frame_id <= self.config.track_buffer
        ]
        
        # Çok eski kayıpları sil
        for track in self._lost_stracks:
            if self._frame_count - track.frame_id > self.config.track_buffer:
                track.mark_removed()
                self._removed_stracks.append(track)
        
        self._lost_stracks = [t for t in self._lost_stracks if t.state != TrackState.DELETED]
        
        # Ana _tracks dict'i güncelle
        self._tracks.clear()
        for strack in self._tracked_stracks:
            track = Track(
                track_id=strack.track_id,
                bbox=strack.bbox,
                confidence=strack.score,
                class_id=strack.class_id,
                class_name="",
                state=strack.state,
                age=strack.tracklet_len
            )
            self._tracks[strack.track_id] = track
        
        return self.confirmed_tracks
    
    def predict(self) -> List[Track]:
        """Track'leri tahmin et"""
        for strack in self._tracked_stracks + self._lost_stracks:
            strack.predict()
        return self.active_tracks
    
    def _linear_assignment(
        self,
        tracks: List[STrack],
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        thresh: float
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        IOU tabanlı linear assignment
        
        Returns:
            matches, unmatched_tracks, unmatched_detections
        """
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))
        
        # IOU matrix hesapla
        iou_matrix = np.zeros((len(tracks), len(detections)))
        
        for t, track in enumerate(tracks):
            for d, det in enumerate(detections):
                iou_matrix[t, d] = self._iou(track.bbox, det[0])
        
        # Cost matrix (1 - IOU)
        cost_matrix = 1 - iou_matrix
        
        # Hungarian assignment
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        matches = []
        unmatched_tracks = list(range(len(tracks)))
        unmatched_detections = list(range(len(detections)))
        
        for row, col in zip(row_indices, col_indices):
            if iou_matrix[row, col] >= thresh:
                matches.append((row, col))
                if row in unmatched_tracks:
                    unmatched_tracks.remove(row)
                if col in unmatched_detections:
                    unmatched_detections.remove(col)
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _iou(
        self,
        box1: Tuple[int, int, int, int],
        box2: Tuple[int, int, int, int]
    ) -> float:
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
    
    def reset(self) -> None:
        """Tracker'ı sıfırla"""
        super().reset()
        self._tracked_stracks.clear()
        self._lost_stracks.clear()
        self._removed_stracks.clear()
        STrack.reset_id()
    
    def get_lost_tracks(self) -> List[STrack]:
        """Kayıp track'leri al"""
        return self._lost_stracks.copy()
    
    def get_all_stracks(self) -> Dict[str, List[STrack]]:
        """Tüm strack'leri kategorilere göre al"""
        return {
            "tracked": self._tracked_stracks,
            "lost": self._lost_stracks,
            "removed": self._removed_stracks
        }
