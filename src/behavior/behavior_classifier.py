"""
Davranış Sınıflandırma Modülü
Hayvan davranışlarını otomatik olarak sınıflandırır
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class BehaviorType(Enum):
    """Davranış tipleri"""
    EATING = "eating"
    DRINKING = "drinking"
    WALKING = "walking"
    RUNNING = "running"
    STANDING = "standing"
    LYING = "lying"
    RESTING = "resting"
    RUMINATING = "ruminating"
    GRAZING = "grazing"
    GROOMING = "grooming"
    SOCIAL = "social"
    UNKNOWN = "unknown"


@dataclass
class BehaviorPrediction:
    """Davranış tahmini sonucu"""
    behavior: BehaviorType
    confidence: float
    start_time: float
    duration: Optional[float] = None
    location: Optional[Tuple[int, int]] = None
    metadata: Optional[Dict] = None


class BehaviorClassifier:
    """
    Hayvan davranışlarını sınıflandıran ana sınıf
    
    Özellikler:
    - Çoklu davranış tespiti
    - Temporal smoothing
    - Güvenilirlik skoru
    - Davranış geçiş analizi
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        temporal_window: int = 30,  # frames
        smoothing_factor: float = 0.3
    ):
        self.confidence_threshold = confidence_threshold
        self.temporal_window = temporal_window
        self.smoothing_factor = smoothing_factor
        
        # Davranış geçmişi
        self.behavior_history: Dict[str, List[BehaviorPrediction]] = {}
        
        # Davranış kuralları
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Davranış tanıma kurallarını başlat"""
        # Yeme davranışı kuralları
        self.eating_rules = {
            'near_feeder': True,
            'head_down': True,
            'low_movement': True,
            'min_duration': 5.0  # saniye
        }
        
        # İçme davranışı kuralları
        self.drinking_rules = {
            'near_water': True,
            'head_down': True,
            'very_low_movement': True,
            'min_duration': 2.0
        }
        
        # Yürüme kuralları
        self.walking_rules = {
            'velocity_range': (0.3, 2.0),  # m/s
            'consistent_direction': True
        }
        
        # Dinlenme kuralları
        self.resting_rules = {
            'lying_position': True,
            'min_duration': 60.0,
            'very_low_movement': True
        }
    
    def classify(
        self,
        animal_id: str,
        position: Tuple[int, int],
        velocity: float,
        zones: Dict[str, any],
        pose_keypoints: Optional[np.ndarray] = None,
        timestamp: float = 0.0
    ) -> BehaviorPrediction:
        """
        Anlık davranış sınıflandırması
        
        Args:
            animal_id: Hayvan kimliği
            position: (x, y) pozisyon
            velocity: Hareket hızı
            zones: Tanımlı bölgeler (feeder, water, rest)
            pose_keypoints: Poz tahmin noktaları (opsiyonel)
            timestamp: Zaman damgası
        
        Returns:
            BehaviorPrediction: Tahmin edilen davranış
        """
        behaviors_scores = {}
        
        # Yeme davranışı kontrolü
        if self._is_near_zone(position, zones.get('feeder')):
            if velocity < 0.2:  # Düşük hareket
                behaviors_scores[BehaviorType.EATING] = 0.85
        
        # İçme davranışı
        if self._is_near_zone(position, zones.get('water')):
            if velocity < 0.1:
                behaviors_scores[BehaviorType.DRINKING] = 0.80
        
        # Hareket davranışları
        if 0.3 <= velocity <= 2.0:
            behaviors_scores[BehaviorType.WALKING] = 0.75
        elif velocity > 2.0:
            behaviors_scores[BehaviorType.RUNNING] = 0.70
        elif velocity < 0.1:
            # Durağan - pozisyon analizi gerekli
            if pose_keypoints is not None:
                if self._is_lying(pose_keypoints):
                    behaviors_scores[BehaviorType.LYING] = 0.80
                else:
                    behaviors_scores[BehaviorType.STANDING] = 0.75
            else:
                behaviors_scores[BehaviorType.STANDING] = 0.60
        
        # En yüksek skorlu davranışı seç
        if behaviors_scores:
            best_behavior = max(behaviors_scores.items(), key=lambda x: x[1])
            behavior, confidence = best_behavior
            
            # Temporal smoothing uygula
            smoothed_behavior, smoothed_confidence = self._apply_temporal_smoothing(
                animal_id, behavior, confidence, timestamp
            )
            
            prediction = BehaviorPrediction(
                behavior=smoothed_behavior,
                confidence=smoothed_confidence,
                start_time=timestamp,
                location=position
            )
        else:
            prediction = BehaviorPrediction(
                behavior=BehaviorType.UNKNOWN,
                confidence=0.0,
                start_time=timestamp,
                location=position
            )
        
        # Geçmişe kaydet
        if animal_id not in self.behavior_history:
            self.behavior_history[animal_id] = []
        self.behavior_history[animal_id].append(prediction)
        
        # Geçmiş temizleme (son N frame)
        if len(self.behavior_history[animal_id]) > self.temporal_window:
            self.behavior_history[animal_id].pop(0)
        
        return prediction
    
    def _is_near_zone(
        self,
        position: Tuple[int, int],
        zone: Optional[Dict]
    ) -> bool:
        """Hayvanın belirli bir bölgede olup olmadığını kontrol eder"""
        if zone is None:
            return False
        
        x, y = position
        x1, y1, x2, y2 = zone['bbox']
        
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _is_lying(self, pose_keypoints: np.ndarray) -> bool:
        """Poz noktalarından yatma pozisyonunu tespit eder"""
        # Basit yöntem: ortalama y koordinatı düşükse yatıyor olabilir
        # Gerçek implementasyon için keypoint analizi gerekli
        if len(pose_keypoints) == 0:
            return False
        
        avg_y = np.mean(pose_keypoints[:, 1])
        # Eğer ortalama y yüksekse (koordinat sistemi ters) yatıyor
        return avg_y > 300  # Threshold, kamera açısına göre ayarlanmalı
    
    def _apply_temporal_smoothing(
        self,
        animal_id: str,
        behavior: BehaviorType,
        confidence: float,
        timestamp: float
    ) -> Tuple[BehaviorType, float]:
        """
        Temporal smoothing uygula - kısa süreli davranış değişimlerini filtrele
        """
        if animal_id not in self.behavior_history:
            return behavior, confidence
        
        history = self.behavior_history[animal_id]
        if len(history) < 3:
            return behavior, confidence
        
        # Son N frame'deki davranışları kontrol et
        recent_behaviors = [h.behavior for h in history[-5:]]
        behavior_counts = {}
        
        for b in recent_behaviors:
            behavior_counts[b] = behavior_counts.get(b, 0) + 1
        
        # En sık görülen davranışı bul
        most_common = max(behavior_counts.items(), key=lambda x: x[1])
        
        if most_common[1] >= 3:  # En az 3 kez görülmüşse
            # Smoothing uygula
            smoothed_behavior = most_common[0]
            # Güvenilirliği artır
            smoothed_confidence = min(confidence * 1.1, 1.0)
            return smoothed_behavior, smoothed_confidence
        
        return behavior, confidence
    
    def get_behavior_duration(
        self,
        animal_id: str,
        behavior: BehaviorType,
        time_window: float = 60.0
    ) -> float:
        """
        Belirli bir davranışın süresini hesapla
        
        Args:
            animal_id: Hayvan kimliği
            behavior: Davranış tipi
            time_window: Zaman penceresi (saniye)
        
        Returns:
            float: Toplam süre (saniye)
        """
        if animal_id not in self.behavior_history:
            return 0.0
        
        history = self.behavior_history[animal_id]
        total_duration = 0.0
        
        for pred in history:
            if pred.behavior == behavior:
                if pred.duration:
                    total_duration += pred.duration
        
        return total_duration
    
    def get_behavior_summary(
        self,
        animal_id: str,
        time_window: float = 3600.0
    ) -> Dict[BehaviorType, Dict]:
        """
        Davranış özeti
        
        Returns:
            Dict: {
                BehaviorType.EATING: {
                    'count': 10,
                    'total_duration': 300.0,
                    'avg_confidence': 0.85
                },
                ...
            }
        """
        if animal_id not in self.behavior_history:
            return {}
        
        summary = {}
        history = self.behavior_history[animal_id]
        
        for behavior_type in BehaviorType:
            matching = [h for h in history if h.behavior == behavior_type]
            
            if matching:
                summary[behavior_type] = {
                    'count': len(matching),
                    'total_duration': sum(h.duration or 0 for h in matching),
                    'avg_confidence': np.mean([h.confidence for h in matching])
                }
        
        return summary
    
    def detect_abnormal_behavior(
        self,
        animal_id: str,
        baseline: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Anormal davranış tespiti
        
        Args:
            animal_id: Hayvan kimliği
            baseline: Baseline davranış profili
        
        Returns:
            List[Dict]: Tespit edilen anormallikler
        """
        anomalies = []
        summary = self.get_behavior_summary(animal_id)
        
        # Yeme davranışı eksikliği
        if BehaviorType.EATING in summary:
            eating_duration = summary[BehaviorType.EATING]['total_duration']
            if eating_duration < 60.0:  # Son 1 saatte 1 dk'dan az
                anomalies.append({
                    'type': 'low_eating',
                    'severity': 'medium',
                    'message': f'Düşük yeme aktivitesi: {eating_duration:.1f}s'
                })
        
        # Aşırı hareketsizlik
        if BehaviorType.STANDING in summary or BehaviorType.LYING in summary:
            static_duration = (
                summary.get(BehaviorType.STANDING, {}).get('total_duration', 0) +
                summary.get(BehaviorType.LYING, {}).get('total_duration', 0)
            )
            
            if static_duration > 2400:  # 40 dk'dan fazla hareketsiz
                anomalies.append({
                    'type': 'excessive_inactivity',
                    'severity': 'low',
                    'message': f'Uzun süreli hareketsizlik: {static_duration/60:.1f} dk'
                })
        
        return anomalies
