"""
Pose Estimator
Hayvan poz tahmini modülü
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class PoseType(str, Enum):
    """Poz tipleri"""
    STANDING = "standing"           # Ayakta
    LYING = "lying"                 # Yatıyor
    SITTING = "sitting"             # Oturuyor
    WALKING = "walking"             # Yürüyor
    RUNNING = "running"             # Koşuyor
    EATING = "eating"               # Yemek yiyor
    DRINKING = "drinking"           # Su içiyor
    GROOMING = "grooming"           # Temizleniyor
    UNKNOWN = "unknown"             # Bilinmeyen


@dataclass
class Keypoint:
    """Vücut anahtar noktası"""
    name: str
    x: float
    y: float
    confidence: float
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def is_valid(self, threshold: float = 0.5) -> bool:
        return self.confidence >= threshold


@dataclass
class PoseEstimate:
    """Poz tahmini sonucu"""
    pose_type: PoseType
    confidence: float
    keypoints: Dict[str, Keypoint]
    bounding_box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    orientation: float = 0.0  # Derece cinsinden yön
    
    def get_keypoint(self, name: str) -> Optional[Keypoint]:
        return self.keypoints.get(name)
    
    def get_valid_keypoints(self, threshold: float = 0.5) -> Dict[str, Keypoint]:
        return {k: v for k, v in self.keypoints.items() if v.is_valid(threshold)}


# Hayvan keypoint isimleri
ANIMAL_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "neck", "spine_start", "spine_mid", "spine_end", "tail_base",
    "left_front_shoulder", "left_front_elbow", "left_front_paw",
    "right_front_shoulder", "right_front_elbow", "right_front_paw",
    "left_back_hip", "left_back_knee", "left_back_paw",
    "right_back_hip", "right_back_knee", "right_back_paw"
]


class PoseEstimatorConfig:
    """Poz tahmin yapılandırması"""
    def __init__(
        self,
        model_path: Optional[str] = None,
        input_size: Tuple[int, int] = (256, 256),
        confidence_threshold: float = 0.5,
        device: str = "cpu"
    ):
        self.model_path = model_path
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.device = device


class AnimalPoseEstimator:
    """Hayvan poz tahminci"""
    
    def __init__(self, config: PoseEstimatorConfig = None):
        self.config = config or PoseEstimatorConfig()
        self._model = None
        self._initialized = False
        
        # Poz sınıflandırma kuralları
        self._pose_rules = self._create_pose_rules()
    
    def initialize(self) -> bool:
        """Modeli yükle ve başlat"""
        try:
            if self.config.model_path and Path(self.config.model_path).exists():
                # Gerçek model yükleme
                # self._model = load_pose_model(self.config.model_path)
                pass
            
            # Kural tabanlı sistem kullan (model yoksa)
            self._initialized = True
            logger.info("Poz tahminci başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Poz tahminci başlatma hatası: {e}")
            return False
    
    def estimate(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int] = None
    ) -> Optional[PoseEstimate]:
        """
        Tek bir hayvan için poz tahmini
        
        Args:
            image: Görüntü (BGR)
            bbox: Hayvan bounding box'ı (x1, y1, x2, y2)
            
        Returns:
            Poz tahmini
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # Bounding box varsa crop
            if bbox:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                crop = image[y1:y2, x1:x2].copy()
            else:
                crop = image
                x1, y1 = 0, 0
                x2, y2 = image.shape[1], image.shape[0]
            
            # Keypoint tahmini
            keypoints = self._estimate_keypoints(crop, (x1, y1))
            
            # Poz sınıflandırma
            pose_type, pose_conf = self._classify_pose(keypoints, crop)
            
            # Yön hesaplama
            orientation = self._calculate_orientation(keypoints)
            
            return PoseEstimate(
                pose_type=pose_type,
                confidence=pose_conf,
                keypoints=keypoints,
                bounding_box=(x1, y1, x2, y2),
                orientation=orientation
            )
            
        except Exception as e:
            logger.error(f"Poz tahmini hatası: {e}")
            return None
    
    def estimate_batch(
        self,
        image: np.ndarray,
        bboxes: List[Tuple[int, int, int, int]]
    ) -> List[PoseEstimate]:
        """Birden fazla hayvan için poz tahmini"""
        results = []
        for bbox in bboxes:
            pose = self.estimate(image, bbox)
            if pose:
                results.append(pose)
        return results
    
    def _estimate_keypoints(
        self,
        crop: np.ndarray,
        offset: Tuple[int, int]
    ) -> Dict[str, Keypoint]:
        """Keypoint tahmini yap"""
        h, w = crop.shape[:2]
        ox, oy = offset
        
        keypoints = {}
        
        if self._model is not None:
            # Model tabanlı tahmin
            # keypoints = self._model.predict(crop)
            pass
        else:
            # Heuristik tabanlı tahmin
            # Basit yerleştirme (gerçek uygulamada model kullanılır)
            
            # Baş bölgesi (üst %30)
            keypoints["nose"] = Keypoint("nose", ox + w * 0.5, oy + h * 0.1, 0.7)
            keypoints["left_eye"] = Keypoint("left_eye", ox + w * 0.4, oy + h * 0.08, 0.6)
            keypoints["right_eye"] = Keypoint("right_eye", ox + w * 0.6, oy + h * 0.08, 0.6)
            keypoints["left_ear"] = Keypoint("left_ear", ox + w * 0.35, oy + h * 0.05, 0.5)
            keypoints["right_ear"] = Keypoint("right_ear", ox + w * 0.65, oy + h * 0.05, 0.5)
            
            # Gövde
            keypoints["neck"] = Keypoint("neck", ox + w * 0.5, oy + h * 0.25, 0.6)
            keypoints["spine_start"] = Keypoint("spine_start", ox + w * 0.5, oy + h * 0.35, 0.5)
            keypoints["spine_mid"] = Keypoint("spine_mid", ox + w * 0.5, oy + h * 0.5, 0.5)
            keypoints["spine_end"] = Keypoint("spine_end", ox + w * 0.5, oy + h * 0.65, 0.5)
            keypoints["tail_base"] = Keypoint("tail_base", ox + w * 0.5, oy + h * 0.75, 0.4)
            
            # Ön bacaklar
            keypoints["left_front_shoulder"] = Keypoint("left_front_shoulder", ox + w * 0.35, oy + h * 0.3, 0.5)
            keypoints["left_front_elbow"] = Keypoint("left_front_elbow", ox + w * 0.3, oy + h * 0.5, 0.4)
            keypoints["left_front_paw"] = Keypoint("left_front_paw", ox + w * 0.25, oy + h * 0.85, 0.5)
            
            keypoints["right_front_shoulder"] = Keypoint("right_front_shoulder", ox + w * 0.65, oy + h * 0.3, 0.5)
            keypoints["right_front_elbow"] = Keypoint("right_front_elbow", ox + w * 0.7, oy + h * 0.5, 0.4)
            keypoints["right_front_paw"] = Keypoint("right_front_paw", ox + w * 0.75, oy + h * 0.85, 0.5)
            
            # Arka bacaklar
            keypoints["left_back_hip"] = Keypoint("left_back_hip", ox + w * 0.35, oy + h * 0.6, 0.5)
            keypoints["left_back_knee"] = Keypoint("left_back_knee", ox + w * 0.3, oy + h * 0.75, 0.4)
            keypoints["left_back_paw"] = Keypoint("left_back_paw", ox + w * 0.25, oy + h * 0.95, 0.5)
            
            keypoints["right_back_hip"] = Keypoint("right_back_hip", ox + w * 0.65, oy + h * 0.6, 0.5)
            keypoints["right_back_knee"] = Keypoint("right_back_knee", ox + w * 0.7, oy + h * 0.75, 0.4)
            keypoints["right_back_paw"] = Keypoint("right_back_paw", ox + w * 0.75, oy + h * 0.95, 0.5)
        
        return keypoints
    
    def _classify_pose(
        self,
        keypoints: Dict[str, Keypoint],
        crop: np.ndarray
    ) -> Tuple[PoseType, float]:
        """Keypoint'lerden poz sınıflandır"""
        valid_kps = {k: v for k, v in keypoints.items() if v.is_valid(0.3)}
        
        if not valid_kps:
            return PoseType.UNKNOWN, 0.0
        
        # Aspect ratio hesapla
        h, w = crop.shape[:2]
        aspect_ratio = w / h if h > 0 else 1.0
        
        # Keypoint pozisyon analizi
        spine_kps = ["spine_start", "spine_mid", "spine_end"]
        spine_y = [keypoints[k].y for k in spine_kps if k in keypoints]
        
        paw_kps = ["left_front_paw", "right_front_paw", "left_back_paw", "right_back_paw"]
        paw_y = [keypoints[k].y for k in paw_kps if k in keypoints]
        
        # Yatma tahmini
        if aspect_ratio > 1.5 and len(spine_y) >= 2:
            spine_variance = np.var(spine_y) if spine_y else 0
            if spine_variance < 100:  # Yatay omurga
                return PoseType.LYING, 0.7
        
        # Ayakta durma tahmini
        if 0.7 < aspect_ratio < 1.3:
            return PoseType.STANDING, 0.6
        
        # Oturma
        if aspect_ratio < 0.8:
            if paw_y:
                front_paws = [keypoints.get("left_front_paw"), keypoints.get("right_front_paw")]
                back_paws = [keypoints.get("left_back_paw"), keypoints.get("right_back_paw")]
                
                front_y = np.mean([p.y for p in front_paws if p])
                back_y = np.mean([p.y for p in back_paws if p])
                
                if abs(front_y - back_y) < h * 0.2:
                    return PoseType.SITTING, 0.6
        
        return PoseType.STANDING, 0.5
    
    def _calculate_orientation(self, keypoints: Dict[str, Keypoint]) -> float:
        """Hayvanın yönünü hesapla (derece)"""
        nose = keypoints.get("nose")
        tail = keypoints.get("tail_base")
        
        if nose and tail and nose.is_valid() and tail.is_valid():
            dx = nose.x - tail.x
            dy = nose.y - tail.y
            angle = np.arctan2(dy, dx) * 180 / np.pi
            return float(angle)
        
        return 0.0
    
    def _create_pose_rules(self) -> Dict[PoseType, dict]:
        """Poz sınıflandırma kuralları"""
        return {
            PoseType.STANDING: {
                "aspect_ratio": (0.7, 1.3),
                "spine_angle": (-30, 30)
            },
            PoseType.LYING: {
                "aspect_ratio": (1.5, 3.0),
                "spine_angle": (-15, 15)
            },
            PoseType.SITTING: {
                "aspect_ratio": (0.5, 0.9),
                "spine_angle": (-45, 45)
            }
        }
    
    def draw_pose(
        self,
        image: np.ndarray,
        pose: PoseEstimate,
        draw_keypoints: bool = True,
        draw_skeleton: bool = True,
        draw_bbox: bool = True
    ) -> np.ndarray:
        """Pozu görüntü üzerine çiz"""
        output = image.copy()
        
        # Bounding box
        if draw_bbox:
            x1, y1, x2, y2 = pose.bounding_box
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            label = f"{pose.pose_type.value}: {pose.confidence:.2f}"
            cv2.putText(output, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Keypoint'ler
        if draw_keypoints:
            for name, kp in pose.keypoints.items():
                if kp.is_valid(0.3):
                    color = (0, 0, 255) if "paw" in name else (255, 0, 0)
                    cv2.circle(output, (int(kp.x), int(kp.y)), 4, color, -1)
        
        # Skeleton
        if draw_skeleton:
            skeleton_pairs = [
                ("nose", "neck"),
                ("neck", "spine_start"),
                ("spine_start", "spine_mid"),
                ("spine_mid", "spine_end"),
                ("spine_end", "tail_base"),
                ("neck", "left_front_shoulder"),
                ("neck", "right_front_shoulder"),
                ("left_front_shoulder", "left_front_elbow"),
                ("left_front_elbow", "left_front_paw"),
                ("right_front_shoulder", "right_front_elbow"),
                ("right_front_elbow", "right_front_paw"),
                ("spine_end", "left_back_hip"),
                ("spine_end", "right_back_hip"),
                ("left_back_hip", "left_back_knee"),
                ("left_back_knee", "left_back_paw"),
                ("right_back_hip", "right_back_knee"),
                ("right_back_knee", "right_back_paw")
            ]
            
            for start, end in skeleton_pairs:
                kp1 = pose.keypoints.get(start)
                kp2 = pose.keypoints.get(end)
                
                if kp1 and kp2 and kp1.is_valid(0.3) and kp2.is_valid(0.3):
                    pt1 = (int(kp1.x), int(kp1.y))
                    pt2 = (int(kp2.x), int(kp2.y))
                    cv2.line(output, pt1, pt2, (0, 255, 255), 2)
        
        return output
