"""
Topallama Tespiti Modülü

Yürüyüş analizi ile topallama tespiti ve şiddet değerlendirmesi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, deque


class LamenessScore(Enum):
    """Topallama skoru (1-5 ölçeği)"""
    NORMAL = 1          # Normal yürüyüş
    MILD = 2            # Hafif topallama
    MODERATE = 3        # Orta derece
    SEVERE = 4          # Şiddetli
    NON_AMBULATORY = 5  # Yürüyemez


class AffectedLimb(Enum):
    """Etkilenen uzuv"""
    FRONT_LEFT = "front_left"
    FRONT_RIGHT = "front_right"
    REAR_LEFT = "rear_left"
    REAR_RIGHT = "rear_right"
    MULTIPLE = "multiple"
    UNKNOWN = "unknown"


class GaitPattern(Enum):
    """Yürüyüş paterni"""
    NORMAL = "normal"
    HEAD_BOB = "head_bob"
    HIP_DROP = "hip_drop"
    SHORT_STRIDE = "short_stride"
    ARCHED_BACK = "arched_back"
    RELUCTANT = "reluctant"


@dataclass
class GaitMetrics:
    """Yürüyüş metrikleri"""
    stride_length: float = 0.0
    stride_symmetry: float = 1.0
    speed: float = 0.0
    head_movement: float = 0.0
    hip_movement: float = 0.0
    back_arch: float = 0.0
    stance_duration: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "stride_length": round(self.stride_length, 4),
            "stride_symmetry": round(self.stride_symmetry, 4),
            "speed": round(self.speed, 4),
            "head_movement": round(self.head_movement, 4),
            "hip_movement": round(self.hip_movement, 4),
            "back_arch": round(self.back_arch, 4),
            "stance_duration": round(self.stance_duration, 4)
        }


@dataclass
class LamenessAssessment:
    """Topallama değerlendirmesi"""
    assessment_id: str
    animal_id: str
    timestamp: datetime
    score: LamenessScore
    affected_limb: AffectedLimb
    confidence: float
    gait_pattern: GaitPattern
    metrics: GaitMetrics
    video_segment_id: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def is_lame(self) -> bool:
        return self.score.value >= 2
    
    @property
    def needs_treatment(self) -> bool:
        return self.score.value >= 3
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "animal_id": self.animal_id,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score.value,
            "score_label": self.score.name.lower(),
            "affected_limb": self.affected_limb.value,
            "confidence": round(self.confidence, 3),
            "gait_pattern": self.gait_pattern.value,
            "is_lame": self.is_lame,
            "needs_treatment": self.needs_treatment,
            "metrics": self.metrics.to_dict()
        }


@dataclass
class MovementFrame:
    """Hareket çerçevesi"""
    frame_id: int
    timestamp: float
    bbox: Tuple[float, float, float, float]
    centroid: Tuple[float, float]
    keypoints: Optional[Dict[str, Tuple[float, float]]] = None


@dataclass
class LamenessHistory:
    """Topallama geçmişi"""
    animal_id: str
    assessments: List[LamenessAssessment] = field(default_factory=list)
    
    @property
    def current_score(self) -> Optional[LamenessScore]:
        if self.assessments:
            return self.assessments[-1].score
        return None
    
    @property
    def trend(self) -> str:
        if len(self.assessments) < 2:
            return "stable"
        recent = self.assessments[-5:]
        scores = [a.score.value for a in recent]
        if scores[-1] > scores[0] + 0.5:
            return "worsening"
        elif scores[-1] < scores[0] - 0.5:
            return "improving"
        return "stable"


class LamenessDetector:
    """Topallama tespit edici"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.histories: Dict[str, LamenessHistory] = {}
        self.movement_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=150))
        
        self.min_frames = self.config.get("min_frames", 30)
        self.symmetry_threshold = self.config.get("symmetry_threshold", 0.85)
        self.head_bob_threshold = self.config.get("head_bob_threshold", 0.15)
        self.speed_threshold = self.config.get("speed_threshold", 0.3)
        
        self._assessment_counter = 0
    
    def _generate_assessment_id(self) -> str:
        self._assessment_counter += 1
        return f"LAM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._assessment_counter}"
    
    def _get_or_create_history(self, animal_id: str) -> LamenessHistory:
        if animal_id not in self.histories:
            self.histories[animal_id] = LamenessHistory(animal_id=animal_id)
        return self.histories[animal_id]
    
    def add_detection(self, animal_id: str, frame_id: int,
                     bbox: Tuple[float, float, float, float],
                     timestamp: float,
                     keypoints: Optional[Dict] = None):
        """Tespit ekle"""
        x, y, w, h = bbox
        centroid = (x + w/2, y + h/2)
        
        frame = MovementFrame(
            frame_id=frame_id,
            timestamp=timestamp,
            bbox=bbox,
            centroid=centroid,
            keypoints=keypoints
        )
        self.movement_buffers[animal_id].append(frame)
    
    def analyze_gait(self, animal_id: str) -> Optional[GaitMetrics]:
        """Yürüyüş analizi yap"""
        buffer = self.movement_buffers.get(animal_id)
        if not buffer or len(buffer) < self.min_frames:
            return None
        
        frames = list(buffer)
        positions = np.array([f.centroid for f in frames])
        
        # Hız hesaplama
        velocities = np.diff(positions, axis=0)
        speeds = np.linalg.norm(velocities, axis=1)
        avg_speed = np.mean(speeds) if len(speeds) > 0 else 0
        
        # Adım uzunluğu
        if len(positions) > 10:
            total_distance = np.sum(speeds)
            stride_length = total_distance / (len(frames) / 25)
        else:
            stride_length = 0
        
        # Hareket analizi
        y_positions = positions[:, 1]
        x_positions = positions[:, 0]
        
        # Baş hareketi
        if len(y_positions) > 5:
            y_detrended = y_positions - np.convolve(y_positions, np.ones(5)/5, mode='same')
            head_movement = np.std(y_detrended)
        else:
            head_movement = 0
        
        # Adım simetrisi
        stride_symmetry = self._calculate_stride_symmetry(positions)
        
        # Kalça hareketi
        hip_movement = np.std(x_positions) if len(x_positions) > 5 else 0
        
        return GaitMetrics(
            stride_length=stride_length,
            stride_symmetry=stride_symmetry,
            speed=avg_speed,
            head_movement=head_movement,
            hip_movement=hip_movement
        )
    
    def _calculate_stride_symmetry(self, positions: np.ndarray) -> float:
        """Adım simetrisini hesapla"""
        if len(positions) < 20:
            return 1.0
        
        direction = positions[-1] - positions[0]
        direction = direction / (np.linalg.norm(direction) + 1e-6)
        projected = np.dot(positions - positions[0], direction)
        
        if len(projected) < 3:
            return 1.0
        
        stride_lengths = []
        for i in range(1, len(projected) - 1):
            if projected[i] > projected[i-1] and projected[i] >= projected[i+1]:
                if stride_lengths:
                    stride_lengths.append(projected[i] - stride_lengths[-1])
                else:
                    stride_lengths.append(projected[i])
        
        if len(stride_lengths) < 2:
            return 1.0
        
        symmetry_scores = []
        for i in range(0, len(stride_lengths) - 1, 2):
            if i + 1 < len(stride_lengths):
                ratio = min(stride_lengths[i], stride_lengths[i+1]) / \
                       (max(stride_lengths[i], stride_lengths[i+1]) + 1e-6)
                symmetry_scores.append(ratio)
        
        return np.mean(symmetry_scores) if symmetry_scores else 1.0
    
    def assess_lameness(self, animal_id: str,
                       video_segment_id: Optional[str] = None) -> Optional[LamenessAssessment]:
        """Topallama değerlendirmesi yap"""
        metrics = self.analyze_gait(animal_id)
        if metrics is None:
            return None
        
        score_value = self._calculate_lameness_score(metrics)
        score = self._value_to_score(score_value)
        affected_limb = self._determine_affected_limb(metrics)
        gait_pattern = self._determine_gait_pattern(metrics)
        confidence = self._calculate_confidence(metrics, animal_id)
        
        assessment = LamenessAssessment(
            assessment_id=self._generate_assessment_id(),
            animal_id=animal_id,
            timestamp=datetime.now(),
            score=score,
            affected_limb=affected_limb,
            confidence=confidence,
            gait_pattern=gait_pattern,
            metrics=metrics,
            video_segment_id=video_segment_id
        )
        
        history = self._get_or_create_history(animal_id)
        history.assessments.append(assessment)
        self.movement_buffers[animal_id].clear()
        
        return assessment
    
    def _calculate_lameness_score(self, metrics: GaitMetrics) -> float:
        """Topallama skor değerini hesapla"""
        normalized = {
            "stride_symmetry": 1 - metrics.stride_symmetry,
            "head_movement": min(1, metrics.head_movement / 0.2),
            "hip_movement": min(1, metrics.hip_movement / 0.15),
            "speed": 1 - min(1, metrics.speed / self.speed_threshold) if metrics.speed < self.speed_threshold else 0,
            "stride_length": 1 - min(1, metrics.stride_length / 0.5) if metrics.stride_length < 0.5 else 0
        }
        
        weights = {"stride_symmetry": 0.3, "head_movement": 0.25, "hip_movement": 0.2, "speed": 0.15, "stride_length": 0.1}
        return sum(normalized[k] * weights[k] for k in weights.keys())
    
    def _value_to_score(self, value: float) -> LamenessScore:
        if value < 0.15:
            return LamenessScore.NORMAL
        elif value < 0.35:
            return LamenessScore.MILD
        elif value < 0.55:
            return LamenessScore.MODERATE
        elif value < 0.75:
            return LamenessScore.SEVERE
        else:
            return LamenessScore.NON_AMBULATORY
    
    def _determine_affected_limb(self, metrics: GaitMetrics) -> AffectedLimb:
        if metrics.head_movement > self.head_bob_threshold:
            return AffectedLimb.FRONT_LEFT
        if metrics.hip_movement > 0.1:
            return AffectedLimb.REAR_RIGHT
        if metrics.stride_symmetry < 0.6:
            return AffectedLimb.MULTIPLE
        return AffectedLimb.UNKNOWN
    
    def _determine_gait_pattern(self, metrics: GaitMetrics) -> GaitPattern:
        if metrics.head_movement > self.head_bob_threshold:
            return GaitPattern.HEAD_BOB
        if metrics.hip_movement > 0.1:
            return GaitPattern.HIP_DROP
        if metrics.stride_length < 0.4:
            return GaitPattern.SHORT_STRIDE
        if metrics.speed < self.speed_threshold * 0.5:
            return GaitPattern.RELUCTANT
        return GaitPattern.NORMAL
    
    def _calculate_confidence(self, metrics: GaitMetrics, animal_id: str) -> float:
        buffer = self.movement_buffers.get(animal_id)
        frame_confidence = min(1.0, len(buffer) / 100) if buffer else 0.5
        return (frame_confidence + 0.8) / 2
    
    def get_lame_animals(self, min_score: int = 2) -> List[Dict]:
        """Topallayan hayvanları listele"""
        lame = []
        for animal_id, history in self.histories.items():
            if not history.assessments:
                continue
            current = history.assessments[-1]
            if current.score.value >= min_score:
                lame.append({
                    "animal_id": animal_id,
                    "score": current.score.value,
                    "score_label": current.score.name,
                    "affected_limb": current.affected_limb.value,
                    "trend": history.trend
                })
        return sorted(lame, key=lambda x: x["score"], reverse=True)
    
    def get_recommendations(self, animal_id: str) -> List[str]:
        """Topallama için öneriler"""
        history = self.histories.get(animal_id)
        if not history or not history.assessments:
            return ["Yürüyüş analizi yapılmalı"]
        
        assessment = history.assessments[-1]
        recommendations = []
        
        if assessment.score == LamenessScore.NORMAL:
            return ["Normal yürüyüş - takip edilmeli"]
        elif assessment.score == LamenessScore.MILD:
            recommendations.extend(["2-3 gün içinde yeniden değerlendir", "Tırnak kontrolü yap"])
        elif assessment.score == LamenessScore.MODERATE:
            recommendations.extend(["Veteriner muayenesi gerekli", "Tırnak bakımı yapılmalı", "Ağrı kesici düşünülebilir"])
        elif assessment.score == LamenessScore.SEVERE:
            recommendations.extend(["ACİL: Veteriner muayenesi", "İzole edilmeli", "Ağrı yönetimi başlanmalı"])
        elif assessment.score == LamenessScore.NON_AMBULATORY:
            recommendations.extend(["ACİL VETERİNER ÇAĞIR", "Hayvan hareket ettirilmemeli", "Yatak sağlanmalı"])
        
        return recommendations
