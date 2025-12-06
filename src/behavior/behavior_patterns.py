"""
Behavior Patterns
Davranış kalıpları tanımlama ve analiz
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class BehaviorCategory(str, Enum):
    """Davranış kategorileri"""
    FEEDING = "feeding"             # Beslenme
    RESTING = "resting"             # Dinlenme
    LOCOMOTION = "locomotion"       # Hareket
    SOCIAL = "social"               # Sosyal
    GROOMING = "grooming"           # Temizlik
    REPRODUCTIVE = "reproductive"   # Üreme
    ABNORMAL = "abnormal"           # Anormal
    UNKNOWN = "unknown"             # Bilinmeyen


class BehaviorIntensity(str, Enum):
    """Davranış yoğunluğu"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BehaviorPattern:
    """Davranış kalıbı tanımı"""
    id: str
    name: str
    category: BehaviorCategory
    description: str
    
    # Tanımlama kriterleri
    min_duration: float = 1.0           # Minimum süre (saniye)
    max_duration: float = float('inf')  # Maksimum süre
    required_poses: List[str] = field(default_factory=list)
    required_motions: List[str] = field(default_factory=list)
    
    # Koşullar
    time_of_day: Optional[Tuple[int, int]] = None  # Saat aralığı (başlangıç, bitiş)
    location_zones: List[str] = field(default_factory=list)
    
    # Önem
    priority: int = 0
    is_alert_worthy: bool = False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "required_poses": self.required_poses,
            "required_motions": self.required_motions,
            "priority": self.priority,
            "is_alert_worthy": self.is_alert_worthy
        }


@dataclass
class BehaviorEvent:
    """Tespit edilen davranış olayı"""
    id: str
    pattern: BehaviorPattern
    animal_id: str
    
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    
    confidence: float = 0.0
    intensity: BehaviorIntensity = BehaviorIntensity.MEDIUM
    
    location: Optional[Tuple[float, float]] = None
    zone: Optional[str] = None
    
    # Ek veriler
    poses: List[str] = field(default_factory=list)
    motions: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None
    
    def complete(self) -> None:
        if self.end_time is None:
            self.end_time = datetime.now()
            self.duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class AnimalState:
    """Hayvan durumu"""
    animal_id: str
    timestamp: datetime
    
    # Konum ve hareket
    position: Tuple[float, float] = (0.0, 0.0)
    velocity: Tuple[float, float] = (0.0, 0.0)
    speed: float = 0.0
    
    # Poz
    pose: str = "unknown"
    pose_confidence: float = 0.0
    
    # Mevcut davranış
    current_behavior: Optional[str] = None
    behavior_duration: float = 0.0
    
    # Aktivite seviyesi (0-1)
    activity_level: float = 0.5


# Önceden tanımlı davranış kalıpları
PREDEFINED_PATTERNS = {
    # Beslenme davranışları
    "grazing": BehaviorPattern(
        id="grazing",
        name="Otlama",
        category=BehaviorCategory.FEEDING,
        description="Hayvan ot yiyor",
        min_duration=30.0,
        required_poses=["standing", "eating"],
        required_motions=["slow_walk", "stationary"]
    ),
    "drinking": BehaviorPattern(
        id="drinking",
        name="Su İçme",
        category=BehaviorCategory.FEEDING,
        description="Hayvan su içiyor",
        min_duration=5.0,
        required_poses=["standing", "drinking"],
        location_zones=["water_trough"]
    ),
    "feeding_trough": BehaviorPattern(
        id="feeding_trough",
        name="Yemlikten Yeme",
        category=BehaviorCategory.FEEDING,
        description="Hayvan yemlikten yiyor",
        min_duration=60.0,
        location_zones=["feeder"]
    ),
    
    # Dinlenme davranışları
    "lying_rest": BehaviorPattern(
        id="lying_rest",
        name="Yatarak Dinlenme",
        category=BehaviorCategory.RESTING,
        description="Hayvan yatarak dinleniyor",
        min_duration=300.0,
        required_poses=["lying"]
    ),
    "standing_rest": BehaviorPattern(
        id="standing_rest",
        name="Ayakta Dinlenme",
        category=BehaviorCategory.RESTING,
        description="Hayvan ayakta dinleniyor",
        min_duration=60.0,
        required_poses=["standing"],
        required_motions=["stationary"]
    ),
    "rumination": BehaviorPattern(
        id="rumination",
        name="Geviş Getirme",
        category=BehaviorCategory.RESTING,
        description="Hayvan geviş getiriyor",
        min_duration=600.0,
        required_poses=["lying", "standing"]
    ),
    
    # Hareket davranışları
    "walking": BehaviorPattern(
        id="walking",
        name="Yürüme",
        category=BehaviorCategory.LOCOMOTION,
        description="Hayvan yürüyor",
        min_duration=5.0,
        required_poses=["standing", "walking"],
        required_motions=["slow_walk", "normal_walk"]
    ),
    "running": BehaviorPattern(
        id="running",
        name="Koşma",
        category=BehaviorCategory.LOCOMOTION,
        description="Hayvan koşuyor",
        min_duration=2.0,
        required_poses=["running"],
        required_motions=["fast_run"]
    ),
    
    # Sosyal davranışlar
    "social_grooming": BehaviorPattern(
        id="social_grooming",
        name="Sosyal Temizlik",
        category=BehaviorCategory.SOCIAL,
        description="Hayvanlar birbirini temizliyor",
        min_duration=30.0
    ),
    "playing": BehaviorPattern(
        id="playing",
        name="Oynama",
        category=BehaviorCategory.SOCIAL,
        description="Hayvanlar oynuyor",
        min_duration=10.0,
        required_motions=["fast_run", "sudden_turn"]
    ),
    
    # Anormal davranışlar
    "isolation": BehaviorPattern(
        id="isolation",
        name="İzolasyon",
        category=BehaviorCategory.ABNORMAL,
        description="Hayvan gruptan ayrı duruyor",
        min_duration=1800.0,
        is_alert_worthy=True,
        priority=8
    ),
    "excessive_lying": BehaviorPattern(
        id="excessive_lying",
        name="Aşırı Yatma",
        category=BehaviorCategory.ABNORMAL,
        description="Hayvan normalden fazla yatıyor",
        min_duration=7200.0,
        required_poses=["lying"],
        is_alert_worthy=True,
        priority=7
    ),
    "lameness": BehaviorPattern(
        id="lameness",
        name="Topallık",
        category=BehaviorCategory.ABNORMAL,
        description="Hayvan topallıyor",
        min_duration=5.0,
        required_motions=["uneven_gait"],
        is_alert_worthy=True,
        priority=9
    ),
    "aggression": BehaviorPattern(
        id="aggression",
        name="Saldırganlık",
        category=BehaviorCategory.ABNORMAL,
        description="Hayvan saldırgan davranış gösteriyor",
        min_duration=2.0,
        is_alert_worthy=True,
        priority=10
    )
}


class BehaviorPatternMatcher:
    """Davranış kalıbı eşleştirici"""
    
    def __init__(self):
        self._patterns: Dict[str, BehaviorPattern] = PREDEFINED_PATTERNS.copy()
        self._custom_matchers: Dict[str, Callable] = {}
        
        # Aktif olaylar (animal_id -> event)
        self._active_events: Dict[str, BehaviorEvent] = {}
        
        # Geçmiş olaylar
        self._event_history: Dict[str, deque] = {}
        self._max_history = 100
    
    def add_pattern(self, pattern: BehaviorPattern) -> None:
        """Yeni davranış kalıbı ekle"""
        self._patterns[pattern.id] = pattern
    
    def add_custom_matcher(
        self,
        pattern_id: str,
        matcher: Callable[[AnimalState, List[AnimalState]], Tuple[bool, float]]
    ) -> None:
        """Özel eşleştirici fonksiyon ekle"""
        self._custom_matchers[pattern_id] = matcher
    
    def match(
        self,
        state: AnimalState,
        history: List[AnimalState] = None
    ) -> List[Tuple[BehaviorPattern, float]]:
        """
        Durum için eşleşen davranış kalıplarını bul
        
        Returns:
            List of (pattern, confidence) tuples
        """
        matches = []
        history = history or []
        
        for pattern_id, pattern in self._patterns.items():
            # Özel matcher varsa kullan
            if pattern_id in self._custom_matchers:
                is_match, confidence = self._custom_matchers[pattern_id](state, history)
            else:
                is_match, confidence = self._default_match(pattern, state, history)
            
            if is_match and confidence > 0.0:
                matches.append((pattern, confidence))
        
        # Önceliğe göre sırala
        matches.sort(key=lambda x: (x[0].priority, x[1]), reverse=True)
        
        return matches
    
    def _default_match(
        self,
        pattern: BehaviorPattern,
        state: AnimalState,
        history: List[AnimalState]
    ) -> Tuple[bool, float]:
        """Varsayılan eşleştirme mantığı"""
        confidence = 1.0
        
        # Poz kontrolü
        if pattern.required_poses:
            if state.pose not in pattern.required_poses:
                return False, 0.0
            confidence *= state.pose_confidence
        
        # Hareket kontrolü
        if pattern.required_motions:
            motion = self._classify_motion(state.speed)
            if motion not in pattern.required_motions:
                return False, 0.0
        
        # Konum/bölge kontrolü
        if pattern.location_zones:
            if state.current_behavior != pattern.id:  # Basit kontrol
                pass  # Zone kontrolü gerekli
        
        # Zaman kontrolü
        if pattern.time_of_day:
            hour = state.timestamp.hour
            start_hour, end_hour = pattern.time_of_day
            if not (start_hour <= hour < end_hour):
                return False, 0.0
        
        # Süre kontrolü (geçmişten)
        if history:
            behavior_duration = self._calculate_behavior_duration(
                pattern.id, state, history
            )
            
            if behavior_duration < pattern.min_duration:
                confidence *= behavior_duration / pattern.min_duration
        
        return True, confidence
    
    def _classify_motion(self, speed: float) -> str:
        """Hız değerinden hareket sınıfı"""
        if speed < 0.1:
            return "stationary"
        elif speed < 0.5:
            return "slow_walk"
        elif speed < 2.0:
            return "normal_walk"
        elif speed < 5.0:
            return "fast_walk"
        else:
            return "fast_run"
    
    def _calculate_behavior_duration(
        self,
        behavior_id: str,
        state: AnimalState,
        history: List[AnimalState]
    ) -> float:
        """Davranış süresini hesapla"""
        if not history:
            return 0.0
        
        duration = 0.0
        for past_state in reversed(history):
            if past_state.current_behavior == behavior_id:
                duration = (state.timestamp - past_state.timestamp).total_seconds()
            else:
                break
        
        return duration
    
    def update_events(
        self,
        animal_id: str,
        state: AnimalState,
        history: List[AnimalState] = None
    ) -> List[BehaviorEvent]:
        """
        Hayvan durumunu güncelle ve olayları yönet
        
        Returns:
            Yeni veya değişen olaylar
        """
        matches = self.match(state, history)
        events = []
        
        if not matches:
            # Aktif olayı sonlandır
            if animal_id in self._active_events:
                event = self._active_events.pop(animal_id)
                event.complete()
                self._add_to_history(animal_id, event)
                events.append(event)
            return events
        
        # En iyi eşleşme
        best_pattern, best_conf = matches[0]
        
        # Mevcut aktif olay kontrolü
        if animal_id in self._active_events:
            active_event = self._active_events[animal_id]
            
            if active_event.pattern.id == best_pattern.id:
                # Aynı davranış devam ediyor
                active_event.confidence = best_conf
                active_event.poses.append(state.pose)
                return []
            else:
                # Farklı davranış - eskiyi sonlandır
                active_event.complete()
                self._add_to_history(animal_id, active_event)
                events.append(active_event)
        
        # Yeni olay oluştur
        import uuid
        new_event = BehaviorEvent(
            id=str(uuid.uuid4())[:8],
            pattern=best_pattern,
            animal_id=animal_id,
            start_time=state.timestamp,
            confidence=best_conf,
            intensity=self._determine_intensity(state),
            location=state.position,
            poses=[state.pose]
        )
        
        self._active_events[animal_id] = new_event
        events.append(new_event)
        
        return events
    
    def _determine_intensity(self, state: AnimalState) -> BehaviorIntensity:
        """Davranış yoğunluğunu belirle"""
        if state.activity_level < 0.3:
            return BehaviorIntensity.LOW
        elif state.activity_level < 0.7:
            return BehaviorIntensity.MEDIUM
        else:
            return BehaviorIntensity.HIGH
    
    def _add_to_history(self, animal_id: str, event: BehaviorEvent) -> None:
        """Geçmişe olay ekle"""
        if animal_id not in self._event_history:
            self._event_history[animal_id] = deque(maxlen=self._max_history)
        self._event_history[animal_id].append(event)
    
    def get_active_events(self) -> Dict[str, BehaviorEvent]:
        """Aktif olayları al"""
        return self._active_events.copy()
    
    def get_history(
        self,
        animal_id: str,
        limit: int = 50
    ) -> List[BehaviorEvent]:
        """Geçmiş olayları al"""
        if animal_id not in self._event_history:
            return []
        return list(self._event_history[animal_id])[-limit:]
    
    def get_patterns_by_category(
        self,
        category: BehaviorCategory
    ) -> List[BehaviorPattern]:
        """Kategoriye göre kalıpları al"""
        return [p for p in self._patterns.values() if p.category == category]
    
    def get_alert_patterns(self) -> List[BehaviorPattern]:
        """Uyarı gerektiren kalıpları al"""
        return [p for p in self._patterns.values() if p.is_alert_worthy]


class BehaviorStatistics:
    """Davranış istatistikleri"""
    
    def __init__(self):
        self._daily_stats: Dict[str, Dict[str, float]] = {}
    
    def calculate_time_budget(
        self,
        events: List[BehaviorEvent],
        period_hours: float = 24.0
    ) -> Dict[str, float]:
        """
        Zaman bütçesi hesapla
        
        Returns:
            Davranış kategorisi -> saat cinsinden süre
        """
        time_budget = {}
        
        for event in events:
            if event.duration > 0:
                category = event.pattern.category.value
                if category not in time_budget:
                    time_budget[category] = 0.0
                time_budget[category] += event.duration / 3600.0
        
        return time_budget
    
    def calculate_behavior_frequency(
        self,
        events: List[BehaviorEvent]
    ) -> Dict[str, int]:
        """Davranış frekansı hesapla"""
        frequency = {}
        
        for event in events:
            behavior_id = event.pattern.id
            if behavior_id not in frequency:
                frequency[behavior_id] = 0
            frequency[behavior_id] += 1
        
        return frequency
    
    def detect_abnormal_patterns(
        self,
        events: List[BehaviorEvent],
        baseline: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """Anormal kalıpları tespit et"""
        anomalies = []
        
        # Davranış süreleri
        time_budget = self.calculate_time_budget(events)
        
        if baseline:
            for behavior, duration in time_budget.items():
                if behavior in baseline:
                    expected = baseline[behavior]
                    deviation = abs(duration - expected) / expected if expected > 0 else 0
                    
                    if deviation > 0.5:  # %50'den fazla sapma
                        anomalies.append({
                            "type": "duration_anomaly",
                            "behavior": behavior,
                            "expected": expected,
                            "actual": duration,
                            "deviation": deviation
                        })
        
        # Anormal davranış olayları
        for event in events:
            if event.pattern.category == BehaviorCategory.ABNORMAL:
                anomalies.append({
                    "type": "abnormal_behavior",
                    "behavior": event.pattern.id,
                    "animal_id": event.animal_id,
                    "duration": event.duration,
                    "timestamp": event.start_time.isoformat()
                })
        
        return anomalies
