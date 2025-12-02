"""
AI Animal Tracking System - Behavior Analyzer
==============================================

Hayvan davranış analizi modülü.
Hareket paternlerinden davranış tespiti.
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import numpy as np

from src.tracking.object_tracker import Track, TrackingResult


logger = logging.getLogger("animal_tracking.behavior")


# ===========================================
# Behavior Types
# ===========================================

class BehaviorType(Enum):
    """Hayvan davranış tipleri"""
    UNKNOWN = "unknown"
    
    # Hareket davranışları
    STATIONARY = "stationary"     # Durağan
    WALKING = "walking"           # Yürüme
    RUNNING = "running"           # Koşma
    
    # Beslenme davranışları
    EATING = "eating"             # Yeme
    DRINKING = "drinking"         # İçme
    GRAZING = "grazing"           # Otlama
    
    # Dinlenme davranışları
    RESTING = "resting"           # Dinlenme
    LYING = "lying"               # Yatma
    SLEEPING = "sleeping"         # Uyuma
    
    # Sosyal davranışlar
    FOLLOWING = "following"       # Takip etme
    GROUPING = "grouping"         # Grup oluşturma
    FIGHTING = "fighting"         # Kavga
    PLAYING = "playing"           # Oynama
    
    # Anormal davranışlar
    PACING = "pacing"             # Stresli gezinme
    CIRCLING = "circling"         # Dönme
    ISOLATION = "isolation"       # Sürüden ayrılma


# Davranış renkleri (görselleştirme için)
BEHAVIOR_COLORS = {
    BehaviorType.UNKNOWN: (128, 128, 128),      # Gri
    BehaviorType.STATIONARY: (0, 255, 255),     # Sarı
    BehaviorType.WALKING: (0, 255, 0),          # Yeşil
    BehaviorType.RUNNING: (0, 165, 255),        # Turuncu
    BehaviorType.EATING: (255, 0, 255),         # Magenta
    BehaviorType.DRINKING: (255, 255, 0),       # Cyan
    BehaviorType.GRAZING: (0, 200, 0),          # Koyu yeşil
    BehaviorType.RESTING: (255, 200, 100),      # Açık mavi
    BehaviorType.LYING: (200, 150, 100),        # Açık kahve
    BehaviorType.SLEEPING: (150, 100, 50),      # Kahve
    BehaviorType.FOLLOWING: (100, 100, 255),    # Kırmızımsı
    BehaviorType.GROUPING: (255, 100, 100),     # Mavimsi
    BehaviorType.FIGHTING: (0, 0, 255),         # Kırmızı
    BehaviorType.PLAYING: (255, 150, 200),      # Pembe
    BehaviorType.PACING: (50, 50, 200),         # Koyu kırmızı
    BehaviorType.CIRCLING: (100, 50, 150),      # Mor
    BehaviorType.ISOLATION: (50, 50, 50),       # Koyu gri
}

# Türkçe isimler
BEHAVIOR_NAMES_TR = {
    BehaviorType.UNKNOWN: "Bilinmiyor",
    BehaviorType.STATIONARY: "Durağan",
    BehaviorType.WALKING: "Yürüyor",
    BehaviorType.RUNNING: "Koşuyor",
    BehaviorType.EATING: "Yiyor",
    BehaviorType.DRINKING: "İçiyor",
    BehaviorType.GRAZING: "Otluyor",
    BehaviorType.RESTING: "Dinleniyor",
    BehaviorType.LYING: "Yatıyor",
    BehaviorType.SLEEPING: "Uyuyor",
    BehaviorType.FOLLOWING: "Takip Ediyor",
    BehaviorType.GROUPING: "Gruplaşıyor",
    BehaviorType.FIGHTING: "Kavga Ediyor",
    BehaviorType.PLAYING: "Oynuyor",
    BehaviorType.PACING: "Stresli",
    BehaviorType.CIRCLING: "Dönüyor",
    BehaviorType.ISOLATION: "İzole",
}


# ===========================================
# Data Classes
# ===========================================

@dataclass
class BehaviorConfig:
    """Davranış analizi konfigürasyonu"""
    # Hareket eşikleri (piksel/frame)
    stationary_threshold: float = 2.0      # Durağan kabul edilme
    walking_threshold: float = 15.0        # Yürüme maksimum hız
    running_threshold: float = 30.0        # Koşma minimum hız
    
    # Zaman eşikleri (frame sayısı)
    min_behavior_frames: int = 15          # Minimum davranış süresi
    behavior_window: int = 30              # Analiz penceresi
    
    # Bölge tespiti
    eating_zones: List[Tuple[int, int, int, int]] = field(default_factory=list)
    drinking_zones: List[Tuple[int, int, int, int]] = field(default_factory=list)
    
    # FPS (hız hesabı için)
    fps: float = 30.0


@dataclass
class BehaviorEvent:
    """Tek bir davranış olayı"""
    behavior: BehaviorType
    confidence: float
    start_frame: int
    end_frame: Optional[int] = None
    
    # İlişkili hayvan
    animal_id: Optional[str] = None
    track_id: Optional[int] = None
    
    # Konum
    location: Optional[Tuple[int, int]] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    @property
    def duration_frames(self) -> int:
        if self.end_frame is None:
            return 0
        return self.end_frame - self.start_frame
    
    @property
    def is_active(self) -> bool:
        return self.end_frame is None
    
    @property
    def behavior_name_tr(self) -> str:
        return BEHAVIOR_NAMES_TR.get(self.behavior, self.behavior.value)
    
    def to_dict(self) -> dict:
        return {
            "behavior": self.behavior.value,
            "behavior_tr": self.behavior_name_tr,
            "confidence": round(self.confidence, 4),
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "duration_frames": self.duration_frames,
            "animal_id": self.animal_id,
            "track_id": self.track_id,
            "location": self.location,
            "is_active": self.is_active,
        }


@dataclass 
class BehaviorState:
    """Track için davranış durumu"""
    track_id: int
    current_behavior: BehaviorType = BehaviorType.UNKNOWN
    confidence: float = 0.0
    
    # Geçmiş
    behavior_history: deque = field(default_factory=lambda: deque(maxlen=100))
    speed_history: deque = field(default_factory=lambda: deque(maxlen=30))
    
    # Aktif olay
    active_event: Optional[BehaviorEvent] = None
    
    # İstatistikler
    behavior_counts: Dict[BehaviorType, int] = field(default_factory=lambda: defaultdict(int))


@dataclass
class BehaviorAnalysisResult:
    """Davranış analizi sonucu"""
    track_id: int
    behavior: BehaviorType
    confidence: float
    speed: float  # pixel/frame
    
    # Önceki davranış
    previous_behavior: Optional[BehaviorType] = None
    behavior_changed: bool = False
    
    # Ek bilgiler
    in_eating_zone: bool = False
    in_drinking_zone: bool = False
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "behavior": self.behavior.value,
            "behavior_tr": BEHAVIOR_NAMES_TR.get(self.behavior, self.behavior.value),
            "confidence": round(self.confidence, 4),
            "speed": round(self.speed, 2),
            "behavior_changed": self.behavior_changed,
            "in_eating_zone": self.in_eating_zone,
            "in_drinking_zone": self.in_drinking_zone,
        }


# ===========================================
# Behavior Analyzer
# ===========================================

class BehaviorAnalyzer:
    """
    Hayvan davranış analiz sınıfı.
    
    Track trajectory ve hız bilgilerinden davranış tespit eder.
    
    Kullanım:
        analyzer = BehaviorAnalyzer()
        
        for track in tracking_result.tracks:
            result = analyzer.analyze(track)
            print(f"Track {track.track_id}: {result.behavior.value}")
    """
    
    def __init__(self, config: Optional[BehaviorConfig] = None):
        self.config = config or BehaviorConfig()
        
        # Track state'leri
        self._states: Dict[int, BehaviorState] = {}
        
        # Frame sayacı
        self._frame_id: int = 0
        
        # Event log
        self._events: List[BehaviorEvent] = []
        
        # İstatistikler
        self._total_analyses: int = 0
        self._behavior_distribution: Dict[BehaviorType, int] = defaultdict(int)
    
    @property
    def statistics(self) -> dict:
        return {
            "total_analyses": self._total_analyses,
            "active_tracks": len(self._states),
            "total_events": len(self._events),
            "behavior_distribution": {
                k.value: v for k, v in self._behavior_distribution.items()
            },
        }
    
    def analyze(self, track: Track, frame_id: Optional[int] = None) -> BehaviorAnalysisResult:
        """
        Track'in davranışını analiz et.
        
        Args:
            track: Track nesnesi
            frame_id: Frame numarası (opsiyonel)
            
        Returns:
            BehaviorAnalysisResult
        """
        if frame_id is not None:
            self._frame_id = frame_id
        else:
            self._frame_id += 1
        
        self._total_analyses += 1
        
        # State al veya oluştur
        if track.track_id not in self._states:
            self._states[track.track_id] = BehaviorState(track_id=track.track_id)
        
        state = self._states[track.track_id]
        
        # Hız hesapla
        speed = self._calculate_speed(track)
        state.speed_history.append(speed)
        
        # Ortalama hız
        avg_speed = np.mean(list(state.speed_history)) if state.speed_history else 0
        
        # Bölge kontrolü
        in_eating = self._check_zone(track.center, self.config.eating_zones)
        in_drinking = self._check_zone(track.center, self.config.drinking_zones)
        
        # Davranış tespit et
        behavior, confidence = self._detect_behavior(
            track, state, avg_speed, in_eating, in_drinking
        )
        
        # Davranış değişimi kontrolü
        previous = state.current_behavior
        changed = previous != behavior
        
        # State güncelle
        state.current_behavior = behavior
        state.confidence = confidence
        state.behavior_history.append(behavior)
        state.behavior_counts[behavior] += 1
        
        # Event yönetimi
        self._handle_behavior_event(state, behavior, confidence, track)
        
        # İstatistik güncelle
        self._behavior_distribution[behavior] += 1
        
        return BehaviorAnalysisResult(
            track_id=track.track_id,
            behavior=behavior,
            confidence=confidence,
            speed=avg_speed,
            previous_behavior=previous if changed else None,
            behavior_changed=changed,
            in_eating_zone=in_eating,
            in_drinking_zone=in_drinking,
        )
    
    def _calculate_speed(self, track: Track) -> float:
        """Track hızını hesapla (pixel/frame)"""
        if track.velocity is None:
            return 0.0
        
        vx, vy = track.velocity
        return np.sqrt(vx**2 + vy**2)
    
    def _check_zone(
        self,
        point: Tuple[int, int],
        zones: List[Tuple[int, int, int, int]]
    ) -> bool:
        """Noktanın herhangi bir bölgede olup olmadığını kontrol et"""
        px, py = point
        for x1, y1, x2, y2 in zones:
            if x1 <= px <= x2 and y1 <= py <= y2:
                return True
        return False
    
    def _detect_behavior(
        self,
        track: Track,
        state: BehaviorState,
        speed: float,
        in_eating: bool,
        in_drinking: bool,
    ) -> Tuple[BehaviorType, float]:
        """
        Davranış tespit et.
        
        Basit kural tabanlı sistem.
        Daha gelişmiş versiyonda ML modeli kullanılabilir.
        """
        confidence = 0.8
        
        # Bölge tabanlı davranışlar (öncelikli)
        if in_eating and speed < self.config.stationary_threshold:
            return BehaviorType.EATING, 0.9
        
        if in_drinking and speed < self.config.stationary_threshold:
            return BehaviorType.DRINKING, 0.9
        
        # Hız tabanlı davranışlar
        if speed < self.config.stationary_threshold:
            # Durağan - uzun süre durağansa dinleniyor/yatıyor olabilir
            stationary_count = sum(
                1 for b in list(state.behavior_history)[-self.config.min_behavior_frames:]
                if b in [BehaviorType.STATIONARY, BehaviorType.RESTING, BehaviorType.LYING]
            )
            
            if stationary_count >= self.config.min_behavior_frames:
                return BehaviorType.RESTING, 0.85
            
            return BehaviorType.STATIONARY, confidence
        
        elif speed < self.config.walking_threshold:
            return BehaviorType.WALKING, confidence
        
        elif speed >= self.config.running_threshold:
            return BehaviorType.RUNNING, confidence
        
        else:
            # Orta hız - yürüme
            return BehaviorType.WALKING, confidence * 0.9
    
    def _handle_behavior_event(
        self,
        state: BehaviorState,
        behavior: BehaviorType,
        confidence: float,
        track: Track,
    ):
        """Davranış event yönetimi"""
        # Aktif event var mı?
        if state.active_event is not None:
            if state.active_event.behavior == behavior:
                # Aynı davranış devam ediyor
                return
            else:
                # Davranış değişti, event kapat
                state.active_event.end_frame = self._frame_id
                self._events.append(state.active_event)
                state.active_event = None
        
        # Yeni event başlat
        if behavior != BehaviorType.UNKNOWN:
            state.active_event = BehaviorEvent(
                behavior=behavior,
                confidence=confidence,
                start_frame=self._frame_id,
                track_id=track.track_id,
                location=track.center,
            )
    
    def analyze_batch(self, tracking_result: TrackingResult) -> List[BehaviorAnalysisResult]:
        """
        Tüm track'leri analiz et.
        
        Args:
            tracking_result: TrackingResult nesnesi
            
        Returns:
            BehaviorAnalysisResult listesi
        """
        results = []
        for track in tracking_result.tracks:
            result = self.analyze(track, frame_id=tracking_result.frame_id)
            results.append(result)
        return results
    
    def get_events(
        self,
        track_id: Optional[int] = None,
        behavior: Optional[BehaviorType] = None,
        active_only: bool = False,
    ) -> List[BehaviorEvent]:
        """
        Event'leri filtrele ve al.
        
        Args:
            track_id: Track ID filtresi
            behavior: Davranış tipi filtresi
            active_only: Sadece aktif eventler
            
        Returns:
            BehaviorEvent listesi
        """
        events = self._events.copy()
        
        # Aktif eventleri ekle
        for state in self._states.values():
            if state.active_event is not None:
                events.append(state.active_event)
        
        # Filtrele
        if track_id is not None:
            events = [e for e in events if e.track_id == track_id]
        
        if behavior is not None:
            events = [e for e in events if e.behavior == behavior]
        
        if active_only:
            events = [e for e in events if e.is_active]
        
        return events
    
    def get_track_state(self, track_id: int) -> Optional[BehaviorState]:
        """Track state al"""
        return self._states.get(track_id)
    
    def add_eating_zone(self, zone: Tuple[int, int, int, int]):
        """Yeme bölgesi ekle"""
        self.config.eating_zones.append(zone)
        logger.info(f"Added eating zone: {zone}")
    
    def add_drinking_zone(self, zone: Tuple[int, int, int, int]):
        """İçme bölgesi ekle"""
        self.config.drinking_zones.append(zone)
        logger.info(f"Added drinking zone: {zone}")
    
    def reset(self):
        """Analyzer'ı sıfırla"""
        self._states.clear()
        self._events.clear()
        self._frame_id = 0
        self._total_analyses = 0
        self._behavior_distribution.clear()
        logger.info("Behavior analyzer reset")


# ===========================================
# Behavior Statistics
# ===========================================

class BehaviorStatistics:
    """
    Davranış istatistikleri toplayıcı.
    
    Uzun vadeli davranış paternlerini analiz eder.
    """
    
    def __init__(self):
        # Hayvan bazlı istatistikler
        self._animal_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_frames": 0,
            "behavior_frames": defaultdict(int),
            "behavior_durations": defaultdict(list),
        })
    
    def update(self, animal_id: str, behavior: BehaviorType):
        """İstatistik güncelle"""
        stats = self._animal_stats[animal_id]
        stats["total_frames"] += 1
        stats["behavior_frames"][behavior] += 1
    
    def get_behavior_percentages(self, animal_id: str) -> Dict[str, float]:
        """Davranış yüzdelerini al"""
        stats = self._animal_stats.get(animal_id)
        if not stats or stats["total_frames"] == 0:
            return {}
        
        total = stats["total_frames"]
        return {
            b.value: (count / total * 100)
            for b, count in stats["behavior_frames"].items()
        }
    
    def get_summary(self, animal_id: str) -> dict:
        """Hayvan davranış özeti"""
        stats = self._animal_stats.get(animal_id)
        if not stats:
            return {}
        
        percentages = self.get_behavior_percentages(animal_id)
        dominant = max(percentages, key=percentages.get) if percentages else None
        
        return {
            "animal_id": animal_id,
            "total_frames": stats["total_frames"],
            "behavior_percentages": {k: round(v, 2) for k, v in percentages.items()},
            "dominant_behavior": dominant,
        }


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    analyzer = BehaviorAnalyzer()
    
    # Fake track oluştur
    class FakeTrack:
        def __init__(self, track_id, center, velocity):
            self.track_id = track_id
            self.center = center
            self.velocity = velocity
            self.history = [center]
    
    # Test senaryoları
    scenarios = [
        ("Durağan", FakeTrack(1, (100, 100), (0.5, 0.3))),
        ("Yürüyen", FakeTrack(2, (200, 200), (8.0, 5.0))),
        ("Koşan", FakeTrack(3, (300, 300), (25.0, 20.0))),
    ]
    
    print("=== Behavior Analysis Test ===\n")
    
    for name, track in scenarios:
        result = analyzer.analyze(track)
        print(f"{name}:")
        print(f"  Behavior: {result.behavior.value}")
        print(f"  Türkçe: {BEHAVIOR_NAMES_TR[result.behavior]}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Speed: {result.speed:.2f} px/frame")
        print()
    
    # İstatistikler
    print("=== Statistics ===")
    for k, v in analyzer.statistics.items():
        print(f"{k}: {v}")
