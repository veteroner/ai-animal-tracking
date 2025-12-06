"""
Estrus (Kızgınlık) Tespit Modülü
===============================
Sığır ve koyunlarda kızgınlık davranışlarını tespit eder.

Tespit Edilen Davranışlar:
- Atlama davranışı (mounting)
- Atlanmaya izin verme (standing heat)
- Huzursuzluk/gezinme
- Kuyruk kaldırma/sallama
- Sosyal etkileşim artışı
- Aktivite seviyesi değişimi
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class EstrusStatus(Enum):
    """Kızgınlık durumu"""
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    BRED = "bred"
    MISSED = "missed"
    FALSE_POSITIVE = "false_positive"


class AnimalType(Enum):
    """Hayvan türü"""
    CATTLE = "cattle"  # Sığır
    SHEEP = "sheep"    # Koyun
    GOAT = "goat"      # Keçi


@dataclass
class EstrusDetection:
    """Kızgınlık tespiti veri yapısı"""
    id: str
    animal_id: str
    detection_time: datetime
    behaviors: Dict[str, float]
    confidence: float
    optimal_breeding_start: datetime
    optimal_breeding_end: datetime
    status: EstrusStatus = EstrusStatus.DETECTED
    notified: bool = False
    notes: str = ""


@dataclass
class BehaviorMetrics:
    """Davranış metrikleri"""
    mounting_count: int = 0           # Atlama sayısı
    standing_heat_duration: float = 0  # Atlanmaya izin verme süresi (dakika)
    activity_level: float = 0         # Aktivite seviyesi (0-1)
    restlessness_score: float = 0     # Huzursuzluk skoru (0-1)
    tail_raising_count: int = 0       # Kuyruk kaldırma sayısı
    social_interactions: int = 0       # Sosyal etkileşim sayısı
    vocalization_count: int = 0        # Ses çıkarma sayısı (opsiyonel)


class EstrusDetector:
    """
    Kızgınlık Tespit Sınıfı
    
    Görüntü analizi ile hayvanların kızgınlık davranışlarını tespit eder.
    """
    
    # Kızgınlık süresi (saat)
    ESTRUS_DURATION = {
        AnimalType.CATTLE: 18,  # İneklerde ortalama 18 saat
        AnimalType.SHEEP: 36,   # Koyunlarda ortalama 36 saat
        AnimalType.GOAT: 36     # Keçilerde ortalama 36 saat
    }
    
    # Optimal tohumlama zamanı (kızgınlık başlangıcından sonra, saat)
    OPTIMAL_BREEDING_TIME = {
        AnimalType.CATTLE: (12, 18),  # 12-18 saat arası
        AnimalType.SHEEP: (12, 24),   # 12-24 saat arası
        AnimalType.GOAT: (12, 24)     # 12-24 saat arası
    }
    
    # Davranış ağırlıkları (confidence hesabı için)
    BEHAVIOR_WEIGHTS = {
        'mounting': 0.30,           # Atlama - en güçlü gösterge
        'standing_heat': 0.35,      # Atlanmaya izin verme - altın standart
        'activity_increase': 0.10,  # Aktivite artışı
        'restlessness': 0.10,       # Huzursuzluk
        'tail_raising': 0.08,       # Kuyruk kaldırma
        'social_interaction': 0.07  # Sosyal etkileşim
    }
    
    def __init__(self, animal_type: AnimalType = AnimalType.CATTLE):
        self.animal_type = animal_type
        self.detections: Dict[str, EstrusDetection] = {}
        self.behavior_history: Dict[str, List[BehaviorMetrics]] = {}
        self.baseline_activity: Dict[str, float] = {}
        
    def analyze_frame(
        self, 
        animal_id: str, 
        frame: np.ndarray,
        detections: List[Dict],
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        Tek bir frame'i analiz eder ve kızgınlık davranışlarını tespit eder.
        
        Args:
            animal_id: Hayvan kimliği
            frame: Video frame'i
            detections: YOLO tespit sonuçları
            timestamp: Frame zamanı
            
        Returns:
            Tespit edilen davranışlar veya None
        """
        behaviors = self._detect_behaviors(animal_id, frame, detections)
        
        if behaviors:
            # Davranış geçmişine ekle
            if animal_id not in self.behavior_history:
                self.behavior_history[animal_id] = []
            self.behavior_history[animal_id].append(behaviors)
            
            # Son 2 saatteki davranışları değerlendir
            return self._evaluate_estrus(animal_id, timestamp)
        
        return None
    
    def _detect_behaviors(
        self, 
        animal_id: str, 
        frame: np.ndarray,
        detections: List[Dict]
    ) -> Optional[BehaviorMetrics]:
        """
        Frame'den davranış metriklerini çıkarır.
        
        Gerçek implementasyonda:
        - Pose estimation ile pozisyon analizi
        - Hareket vektörleri ile aktivite hesabı
        - Proximity detection ile sosyal etkileşim
        """
        metrics = BehaviorMetrics()
        
        # Hayvanı bul
        target_animal = None
        other_animals = []
        
        for det in detections:
            if det.get('id') == animal_id:
                target_animal = det
            else:
                other_animals.append(det)
        
        if not target_animal:
            return None
        
        # Atlama tespiti (mounting detection)
        metrics.mounting_count = self._detect_mounting(target_animal, other_animals)
        
        # Standing heat tespiti
        metrics.standing_heat_duration = self._detect_standing_heat(target_animal, other_animals)
        
        # Aktivite seviyesi
        metrics.activity_level = self._calculate_activity(animal_id, target_animal)
        
        # Huzursuzluk skoru
        metrics.restlessness_score = self._calculate_restlessness(animal_id, target_animal)
        
        # Kuyruk hareketi
        metrics.tail_raising_count = self._detect_tail_raising(target_animal)
        
        # Sosyal etkileşim
        metrics.social_interactions = self._count_social_interactions(target_animal, other_animals)
        
        return metrics
    
    def _detect_mounting(self, target: Dict, others: List[Dict]) -> int:
        """
        Atlama davranışı tespiti.
        
        İki hayvanın dikey pozisyon farkı ve yakınlığına bakılır.
        """
        mounting_count = 0
        target_bbox = target.get('bbox', [0, 0, 0, 0])
        target_center_y = (target_bbox[1] + target_bbox[3]) / 2
        
        for other in others:
            other_bbox = other.get('bbox', [0, 0, 0, 0])
            other_center_y = (other_bbox[1] + other_bbox[3]) / 2
            
            # Horizontal overlap kontrolü
            x_overlap = self._calculate_overlap(
                target_bbox[0], target_bbox[2],
                other_bbox[0], other_bbox[2]
            )
            
            # Dikey pozisyon farkı (üstte olan atlıyor)
            if x_overlap > 0.3 and other_center_y < target_center_y - 50:
                mounting_count += 1
                
        return mounting_count
    
    def _detect_standing_heat(self, target: Dict, others: List[Dict]) -> float:
        """
        Standing heat tespiti - Atlanmaya izin verme.
        
        Hayvanın atlama sırasında sabit durma süresi.
        """
        # Simülasyon için rastgele değer
        # Gerçek implementasyonda temporal analiz gerekir
        return np.random.uniform(0, 5) if others else 0
    
    def _calculate_activity(self, animal_id: str, target: Dict) -> float:
        """
        Aktivite seviyesi hesaplama.
        
        Baseline'a göre hareket artışı.
        """
        current_speed = target.get('speed', 0)
        baseline = self.baseline_activity.get(animal_id, 0.5)
        
        if baseline > 0:
            activity_ratio = current_speed / baseline
            return min(activity_ratio, 2.0) / 2.0  # 0-1 arası normalize
        
        return 0.5
    
    def _calculate_restlessness(self, animal_id: str, target: Dict) -> float:
        """
        Huzursuzluk skoru hesaplama.
        
        Sık pozisyon değişikliği, yatıp kalkma.
        """
        # Pozisyon değişikliği sayısı
        position_changes = target.get('position_changes', 0)
        
        # 0-1 arası normalize (10+ değişiklik = maksimum huzursuzluk)
        return min(position_changes / 10.0, 1.0)
    
    def _detect_tail_raising(self, target: Dict) -> int:
        """
        Kuyruk kaldırma tespiti.
        
        Pose estimation ile kuyruk açısı analizi.
        """
        # Pose keypoints varsa analiz et
        keypoints = target.get('keypoints', {})
        tail_angle = keypoints.get('tail_angle', 0)
        
        # 45 derecenin üstü = kuyruk kaldırma
        if tail_angle > 45:
            return 1
        return 0
    
    def _count_social_interactions(self, target: Dict, others: List[Dict]) -> int:
        """
        Sosyal etkileşim sayısı.
        
        Yakın mesafedeki hayvan sayısı.
        """
        interactions = 0
        target_center = self._get_center(target.get('bbox', [0, 0, 0, 0]))
        
        for other in others:
            other_center = self._get_center(other.get('bbox', [0, 0, 0, 0]))
            distance = np.sqrt(
                (target_center[0] - other_center[0])**2 + 
                (target_center[1] - other_center[1])**2
            )
            
            # 100 pixel içinde = etkileşim
            if distance < 100:
                interactions += 1
                
        return interactions
    
    def _evaluate_estrus(self, animal_id: str, timestamp: datetime) -> Optional[Dict]:
        """
        Son davranışları değerlendirerek kızgınlık durumunu belirler.
        """
        history = self.behavior_history.get(animal_id, [])
        
        if len(history) < 5:  # En az 5 frame gerekli
            return None
        
        # Son 30 dakikalık veriyi al
        recent = history[-30:]  # ~30 dakika (1 frame/dakika varsayımı)
        
        # Davranış skorlarını hesapla
        behavior_scores = {
            'mounting': sum(m.mounting_count for m in recent) > 0,
            'standing_heat': sum(m.standing_heat_duration for m in recent) > 2,
            'activity_increase': np.mean([m.activity_level for m in recent]) > 0.7,
            'restlessness': np.mean([m.restlessness_score for m in recent]) > 0.5,
            'tail_raising': sum(m.tail_raising_count for m in recent) > 3,
            'social_interaction': sum(m.social_interactions for m in recent) > 5
        }
        
        # Confidence hesapla
        confidence = sum(
            self.BEHAVIOR_WEIGHTS[behavior] 
            for behavior, detected in behavior_scores.items() 
            if detected
        )
        
        # Kızgınlık eşiği: %50
        if confidence >= 0.5:
            detection = self._create_detection(
                animal_id, timestamp, behavior_scores, confidence
            )
            self.detections[detection.id] = detection
            
            return {
                'detection_id': detection.id,
                'animal_id': animal_id,
                'confidence': confidence,
                'behaviors': behavior_scores,
                'optimal_breeding_start': detection.optimal_breeding_start.isoformat(),
                'optimal_breeding_end': detection.optimal_breeding_end.isoformat(),
                'status': detection.status.value
            }
        
        return None
    
    def _create_detection(
        self, 
        animal_id: str, 
        timestamp: datetime,
        behaviors: Dict[str, bool],
        confidence: float
    ) -> EstrusDetection:
        """Yeni kızgınlık tespiti oluşturur."""
        
        # Optimal tohumlama zamanını hesapla
        breeding_start, breeding_end = self.OPTIMAL_BREEDING_TIME[self.animal_type]
        
        return EstrusDetection(
            id=f"estrus-{animal_id}-{uuid.uuid4().hex[:8]}",
            animal_id=animal_id,
            detection_time=timestamp,
            behaviors={k: 1.0 if v else 0.0 for k, v in behaviors.items()},
            confidence=confidence,
            optimal_breeding_start=timestamp + timedelta(hours=breeding_start),
            optimal_breeding_end=timestamp + timedelta(hours=breeding_end),
            status=EstrusStatus.DETECTED
        )
    
    def confirm_estrus(self, detection_id: str) -> bool:
        """Kızgınlık tespitini manuel olarak onaylar."""
        if detection_id in self.detections:
            self.detections[detection_id].status = EstrusStatus.CONFIRMED
            return True
        return False
    
    def mark_as_bred(self, detection_id: str) -> bool:
        """Tohumlama yapıldı olarak işaretler."""
        if detection_id in self.detections:
            self.detections[detection_id].status = EstrusStatus.BRED
            return True
        return False
    
    def get_active_estrus(self) -> List[EstrusDetection]:
        """Aktif kızgınlık tespitlerini döndürür."""
        now = datetime.now()
        duration = timedelta(hours=self.ESTRUS_DURATION[self.animal_type])
        
        return [
            d for d in self.detections.values()
            if d.status in [EstrusStatus.DETECTED, EstrusStatus.CONFIRMED]
            and now - d.detection_time < duration
        ]
    
    def get_breeding_ready(self) -> List[EstrusDetection]:
        """Tohumlamaya hazır hayvanları döndürür."""
        now = datetime.now()
        
        return [
            d for d in self.detections.values()
            if d.status in [EstrusStatus.DETECTED, EstrusStatus.CONFIRMED]
            and d.optimal_breeding_start <= now <= d.optimal_breeding_end
        ]
    
    def update_baseline(self, animal_id: str, activity_level: float):
        """Hayvanın baseline aktivite seviyesini günceller."""
        if animal_id not in self.baseline_activity:
            self.baseline_activity[animal_id] = activity_level
        else:
            # Exponential moving average
            alpha = 0.1
            self.baseline_activity[animal_id] = (
                alpha * activity_level + 
                (1 - alpha) * self.baseline_activity[animal_id]
            )
    
    @staticmethod
    def _calculate_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
        """İki aralığın örtüşme oranını hesaplar."""
        overlap = max(0, min(a_max, b_max) - max(a_min, b_min))
        total = max(a_max, b_max) - min(a_min, b_min)
        return overlap / total if total > 0 else 0
    
    @staticmethod
    def _get_center(bbox: List[float]) -> Tuple[float, float]:
        """Bounding box merkezini hesaplar."""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


# Test için örnek kullanım
if __name__ == "__main__":
    detector = EstrusDetector(AnimalType.CATTLE)
    
    # Simüle edilmiş tespit
    test_detections = [
        {'id': 'inek-001', 'bbox': [100, 100, 200, 200], 'speed': 0.8},
        {'id': 'inek-002', 'bbox': [150, 50, 250, 150], 'speed': 0.3},
    ]
    
    # Frame analizi
    result = detector.analyze_frame(
        animal_id='inek-001',
        frame=np.zeros((480, 640, 3), dtype=np.uint8),
        detections=test_detections,
        timestamp=datetime.now()
    )
    
    if result:
        print(f"Kızgınlık tespit edildi: {result}")
    else:
        print("Kızgınlık tespit edilmedi (yeterli veri yok)")
