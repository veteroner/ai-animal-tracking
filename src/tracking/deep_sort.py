"""
DeepSORT Tracker
Deep Simple Online and Realtime Tracking implementasyonu
"""

import numpy as np
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter

from .tracker_base import TrackerBase, TrackerConfig, Track, TrackState

logger = logging.getLogger(__name__)


@dataclass
class DeepSORTConfig(TrackerConfig):
    """DeepSORT konfigürasyonu"""
    nn_budget: int = 100          # Feature gallery boyutu
    max_cosine_distance: float = 0.3  # Maksimum cosine mesafesi
    n_init: int = 3               # Onay için hit sayısı
    max_iou_distance: float = 0.7  # Maksimum IOU mesafesi
    lambda_: float = 0.0          # Appearance vs motion balance


class KalmanBoxTracker:
    """
    Kalman Filter ile bounding box takibi
    State: [x, y, a, h, vx, vy, va, vh]
    - x, y: merkez koordinatları
    - a: aspect ratio (width/height)
    - h: height
    - vx, vy, va, vh: velocity bileşenleri
    """
    
    count = 0
    
    def __init__(self, bbox: Tuple[int, int, int, int]):
        """
        Args:
            bbox: İlk bounding box (x1, y1, x2, y2)
        """
        # Kalman filter tanımla
        self.kf = KalmanFilter(dim_x=8, dim_z=4)
        
        # State transition matrix
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement matrix
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0]
        ])
        
        # Measurement noise
        self.kf.R[2:, 2:] *= 10.0
        
        # Covariance matrix
        self.kf.P[4:, 4:] *= 1000.0  # Velocity belirsizliği
        self.kf.P *= 10.0
        
        # Process noise
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        # İlk state
        self.kf.x[:4] = self._bbox_to_z(bbox)
        
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
    
    def _bbox_to_z(self, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Bbox'ı measurement'a çevir [x, y, a, h]"""
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        x = x1 + w / 2
        y = y1 + h / 2
        a = w / float(h) if h > 0 else 1.0
        return np.array([[x], [y], [a], [h]])
    
    def _z_to_bbox(self, z: np.ndarray) -> Tuple[int, int, int, int]:
        """Measurement'ı bbox'a çevir"""
        x, y, a, h = z.flatten()[:4]
        w = a * h
        return (
            int(x - w / 2),
            int(y - h / 2),
            int(x + w / 2),
            int(y + h / 2)
        )
    
    def update(self, bbox: Tuple[int, int, int, int]) -> None:
        """Kalman filter'ı yeni ölçümle güncelle"""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._bbox_to_z(bbox))
    
    def predict(self) -> Tuple[int, int, int, int]:
        """Bir sonraki state'i tahmin et"""
        # Negatif alan önleme
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        
        self.kf.predict()
        self.age += 1
        
        if self.time_since_update > 0:
            self.hit_streak = 0
        
        self.time_since_update += 1
        self.history.append(self._z_to_bbox(self.kf.x))
        
        return self.history[-1]
    
    def get_state(self) -> Tuple[int, int, int, int]:
        """Mevcut state'i bbox olarak al"""
        return self._z_to_bbox(self.kf.x)


class DeepSORTTracker(TrackerBase):
    """
    DeepSORT Tracker implementasyonu
    
    Özellikler:
    - Kalman filter ile motion prediction
    - Appearance feature matching
    - Hungarian algoritması ile eşleştirme
    """
    
    def __init__(self, config: DeepSORTConfig):
        """
        Args:
            config: DeepSORT konfigürasyonu
        """
        super().__init__(config)
        self.config: DeepSORTConfig = config
        
        self._kalman_trackers: Dict[int, KalmanBoxTracker] = {}
        self._feature_gallery: Dict[int, List[np.ndarray]] = {}
    
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        frame: Optional[np.ndarray] = None,
        features: Optional[List[np.ndarray]] = None
    ) -> List[Track]:
        """
        Tracker'ı yeni tespitlerle güncelle
        
        Args:
            detections: (bbox, confidence, class_id) tuple listesi
            frame: Orijinal frame (kullanılmıyor, feature extractor dışarıda)
            features: Detection'lar için önceden çıkarılmış özellikler
            
        Returns:
            Güncellenmiş track listesi
        """
        self.increment_frame()
        
        # 1. Mevcut track'leri predict et
        self.predict()
        
        # 2. Detection'larla eşleştir
        matches, unmatched_tracks, unmatched_detections = self._match(
            detections, features
        )
        
        # 3. Eşleşmeleri güncelle
        for track_idx, det_idx in matches:
            track_id = list(self._tracks.keys())[track_idx]
            bbox, conf, class_id = detections[det_idx]
            
            self.update_track(track_id, bbox, conf)
            self._kalman_trackers[track_id].update(bbox)
            
            # Feature güncelle
            if features is not None and det_idx < len(features):
                self._update_feature_gallery(track_id, features[det_idx])
        
        # 4. Eşleşmeyenleri işaretle
        for track_idx in unmatched_tracks:
            track_id = list(self._tracks.keys())[track_idx]
            self.mark_missed(track_id)
        
        # 5. Yeni track'ler oluştur
        for det_idx in unmatched_detections:
            bbox, conf, class_id = detections[det_idx]
            track = self.create_track(bbox, conf, class_id, "")
            
            # Kalman tracker oluştur
            self._kalman_trackers[track.track_id] = KalmanBoxTracker(bbox)
            
            # Feature ekle
            if features is not None and det_idx < len(features):
                self._feature_gallery[track.track_id] = [features[det_idx]]
        
        # 6. Temizlik
        self.cleanup()
        
        return self.confirmed_tracks
    
    def predict(self) -> List[Track]:
        """Kalman filter ile track pozisyonlarını tahmin et"""
        for track_id, track in self._tracks.items():
            if track_id in self._kalman_trackers:
                predicted_bbox = self._kalman_trackers[track_id].predict()
                track.bbox = predicted_bbox
        
        return self.active_tracks
    
    def _match(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], float, int]],
        features: Optional[List[np.ndarray]] = None
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Detection'ları track'lerle eşleştir
        
        İki aşamalı eşleştirme:
        1. Confirmed track'ler için appearance + motion
        2. Kalan track'ler için sadece IOU
        """
        if not self._tracks or not detections:
            return [], list(range(len(self._tracks))), list(range(len(detections)))
        
        tracks = list(self._tracks.values())
        
        # Confirmed ve unconfirmed track'leri ayır
        confirmed_indices = [i for i, t in enumerate(tracks) if t.is_confirmed]
        unconfirmed_indices = [i for i, t in enumerate(tracks) if not t.is_confirmed]
        
        # 1. Cascade matching (confirmed tracks)
        matches_a, unmatched_tracks_a, unmatched_detections = self._cascade_matching(
            tracks, confirmed_indices, detections, features
        )
        
        # 2. IOU matching (unconfirmed tracks + unmatched)
        iou_track_candidates = unconfirmed_indices + [
            i for i in unmatched_tracks_a if tracks[i].time_since_update == 1
        ]
        
        matches_b, unmatched_tracks_b, unmatched_detections = self._iou_matching(
            tracks, iou_track_candidates, detections, unmatched_detections
        )
        
        matches = matches_a + matches_b
        unmatched_tracks = list(set(unmatched_tracks_a) - set([m[0] for m in matches_b])) + unmatched_tracks_b
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _cascade_matching(
        self,
        tracks: List[Track],
        track_indices: List[int],
        detections: list,
        features: Optional[List[np.ndarray]]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Cascade matching - appearance ve motion birleştirerek"""
        if not track_indices:
            return [], [], list(range(len(detections)))
        
        unmatched_detections = list(range(len(detections)))
        matches = []
        
        # Age'e göre matching (en güncel track'ler önce)
        for age in range(self.config.max_age):
            if not unmatched_detections:
                break
            
            age_tracks = [i for i in track_indices if tracks[i].time_since_update == age + 1]
            if not age_tracks:
                continue
            
            # Cost matrix hesapla
            cost_matrix = self._combined_cost_matrix(
                tracks, age_tracks, detections, unmatched_detections, features
            )
            
            # Hungarian matching
            if cost_matrix.size > 0:
                row_indices, col_indices = linear_sum_assignment(cost_matrix)
                
                for row, col in zip(row_indices, col_indices):
                    track_idx = age_tracks[row]
                    det_idx = unmatched_detections[col]
                    
                    if cost_matrix[row, col] <= self.config.max_cosine_distance:
                        matches.append((track_idx, det_idx))
                
                # Eşleşen detection'ları kaldır
                matched_dets = [m[1] for m in matches if m[1] in unmatched_detections]
                unmatched_detections = [d for d in unmatched_detections if d not in matched_dets]
        
        unmatched_tracks = [i for i in track_indices if i not in [m[0] for m in matches]]
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _iou_matching(
        self,
        tracks: List[Track],
        track_indices: List[int],
        detections: list,
        detection_indices: List[int]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """IOU tabanlı matching"""
        if not track_indices or not detection_indices:
            return [], track_indices, detection_indices
        
        # IOU cost matrix
        cost_matrix = np.zeros((len(track_indices), len(detection_indices)))
        
        for i, track_idx in enumerate(track_indices):
            for j, det_idx in enumerate(detection_indices):
                track = tracks[track_idx]
                det_bbox = detections[det_idx][0]
                iou = self._calculate_iou(track.bbox, det_bbox)
                cost_matrix[i, j] = 1 - iou  # IOU'yu cost'a çevir
        
        # Hungarian matching
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        matches = []
        unmatched_tracks = list(range(len(track_indices)))
        unmatched_detections = list(range(len(detection_indices)))
        
        for row, col in zip(row_indices, col_indices):
            if cost_matrix[row, col] <= self.config.max_iou_distance:
                matches.append((track_indices[row], detection_indices[col]))
                unmatched_tracks.remove(row)
                unmatched_detections.remove(col)
        
        unmatched_tracks = [track_indices[i] for i in unmatched_tracks]
        unmatched_detections = [detection_indices[i] for i in unmatched_detections]
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _combined_cost_matrix(
        self,
        tracks: List[Track],
        track_indices: List[int],
        detections: list,
        detection_indices: List[int],
        features: Optional[List[np.ndarray]]
    ) -> np.ndarray:
        """Appearance ve motion birleştiren cost matrix"""
        cost_matrix = np.zeros((len(track_indices), len(detection_indices)))
        
        for i, track_idx in enumerate(track_indices):
            track = tracks[track_idx]
            track_id = track.track_id
            
            for j, det_idx in enumerate(detection_indices):
                det_bbox = detections[det_idx][0]
                
                # Motion cost (Mahalanobis distance - basitleştirilmiş)
                motion_cost = 1 - self._calculate_iou(track.bbox, det_bbox)
                
                # Appearance cost
                appearance_cost = 1.0
                if features is not None and track_id in self._feature_gallery:
                    if det_idx < len(features):
                        det_feature = features[det_idx]
                        gallery = self._feature_gallery[track_id]
                        
                        # En yakın feature ile mesafe
                        min_dist = min(
                            self._cosine_distance(det_feature, gf) for gf in gallery
                        )
                        appearance_cost = min_dist
                
                # Birleşik cost
                cost = self.config.lambda_ * motion_cost + (1 - self.config.lambda_) * appearance_cost
                cost_matrix[i, j] = cost
        
        return cost_matrix
    
    def _cosine_distance(self, f1: np.ndarray, f2: np.ndarray) -> float:
        """Cosine mesafesi hesapla"""
        f1 = f1.flatten()
        f2 = f2.flatten()
        
        dot = np.dot(f1, f2)
        norm1 = np.linalg.norm(f1)
        norm2 = np.linalg.norm(f2)
        
        if norm1 == 0 or norm2 == 0:
            return 1.0
        
        similarity = dot / (norm1 * norm2)
        return 1 - similarity
    
    def _update_feature_gallery(self, track_id: int, feature: np.ndarray) -> None:
        """Track'in feature gallery'sini güncelle"""
        if track_id not in self._feature_gallery:
            self._feature_gallery[track_id] = []
        
        gallery = self._feature_gallery[track_id]
        gallery.append(feature)
        
        # Budget aşıldıysa en eskisini kaldır
        if len(gallery) > self.config.nn_budget:
            gallery.pop(0)
    
    def cleanup(self) -> None:
        """Eski track'leri ve ilişkili verileri temizle"""
        to_delete = []
        
        for track_id, track in self._tracks.items():
            if track.state == TrackState.DELETED:
                to_delete.append(track_id)
            elif track.time_since_update > self.config.max_age:
                to_delete.append(track_id)
        
        for track_id in to_delete:
            self.delete_track(track_id)
            
            # Kalman tracker'ı sil
            if track_id in self._kalman_trackers:
                del self._kalman_trackers[track_id]
            
            # Feature gallery'yi sil
            if track_id in self._feature_gallery:
                del self._feature_gallery[track_id]
    
    def reset(self) -> None:
        """Tracker'ı sıfırla"""
        super().reset()
        self._kalman_trackers.clear()
        self._feature_gallery.clear()
        KalmanBoxTracker.count = 0
