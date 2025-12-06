"""
Feeding Behavior
Beslenme davranışı analizi
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class FeedingActivity(str, Enum):
    """Beslenme aktivite tipleri"""
    GRAZING = "grazing"             # Otlama
    TROUGH_FEEDING = "trough"       # Yemlik
    DRINKING = "drinking"           # Su içme
    RUMINATING = "ruminating"       # Geviş getirme
    NOT_FEEDING = "not_feeding"     # Beslenmiyyor


@dataclass
class FeedingEvent:
    """Beslenme olayı"""
    id: str
    animal_id: str
    activity: FeedingActivity
    
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0  # Saniye
    
    location: Optional[Tuple[float, float]] = None
    zone: Optional[str] = None  # "feeder_1", "water_trough", etc.
    
    # Ölçümler
    estimated_intake: float = 0.0  # kg veya litre
    bites_count: int = 0
    
    confidence: float = 0.0
    
    def complete(self) -> None:
        if self.end_time is None:
            self.end_time = datetime.now()
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None


@dataclass
class DailyFeedingStats:
    """Günlük beslenme istatistikleri"""
    date: datetime
    animal_id: str
    
    # Süre (dakika)
    grazing_minutes: float = 0.0
    trough_minutes: float = 0.0
    drinking_minutes: float = 0.0
    ruminating_minutes: float = 0.0
    
    # Sayılar
    feeding_sessions: int = 0
    drinking_sessions: int = 0
    
    # Tahmini alım
    estimated_food_intake: float = 0.0  # kg
    estimated_water_intake: float = 0.0  # litre
    
    def total_feeding_time(self) -> float:
        """Toplam beslenme süresi (dakika)"""
        return self.grazing_minutes + self.trough_minutes
    
    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "animal_id": self.animal_id,
            "grazing_minutes": self.grazing_minutes,
            "trough_minutes": self.trough_minutes,
            "drinking_minutes": self.drinking_minutes,
            "ruminating_minutes": self.ruminating_minutes,
            "feeding_sessions": self.feeding_sessions,
            "drinking_sessions": self.drinking_sessions,
            "estimated_food_intake": self.estimated_food_intake,
            "estimated_water_intake": self.estimated_water_intake
        }


@dataclass
class FeedingZone:
    """Beslenme bölgesi tanımı"""
    id: str
    name: str
    zone_type: str  # "feeder", "water", "pasture"
    
    # Bölge sınırları (polygon noktaları)
    boundaries: List[Tuple[float, float]] = field(default_factory=list)
    
    # Kapasite
    capacity: int = 1  # Aynı anda kaç hayvan kullanabilir
    current_occupancy: int = 0
    
    # İstatistikler
    total_visits: int = 0
    total_usage_time: float = 0.0


class FeedingBehaviorAnalyzer:
    """Beslenme davranışı analizci"""
    
    def __init__(
        self,
        grazing_threshold: float = 0.6,
        drinking_min_duration: float = 3.0
    ):
        self.grazing_threshold = grazing_threshold
        self.drinking_min_duration = drinking_min_duration
        
        # Beslenme bölgeleri
        self._zones: Dict[str, FeedingZone] = {}
        
        # Aktif olaylar (animal_id -> event)
        self._active_events: Dict[str, FeedingEvent] = {}
        
        # Olay geçmişi (animal_id -> deque)
        self._event_history: Dict[str, deque] = {}
        self._max_history = 500
        
        # Günlük istatistikler (animal_id -> stats)
        self._daily_stats: Dict[str, DailyFeedingStats] = {}
        
        # Tahmin parametreleri
        self._intake_rates = {
            FeedingActivity.GRAZING: 0.5,      # kg/dakika (kuru madde)
            FeedingActivity.TROUGH_FEEDING: 0.3,
            FeedingActivity.DRINKING: 0.5       # litre/dakika
        }
    
    def add_zone(self, zone: FeedingZone) -> None:
        """Beslenme bölgesi ekle"""
        self._zones[zone.id] = zone
    
    def analyze_frame(
        self,
        animal_id: str,
        pose: str,
        position: Tuple[float, float],
        head_position: Optional[Tuple[float, float]] = None,
        timestamp: datetime = None
    ) -> Optional[FeedingEvent]:
        """
        Frame analizi - beslenme aktivitesi tespit
        
        Args:
            animal_id: Hayvan ID'si
            pose: Mevcut poz
            position: Hayvan pozisyonu
            head_position: Baş pozisyonu (opsiyonel)
            timestamp: Zaman damgası
            
        Returns:
            Tespit edilen veya güncellenen beslenme olayı
        """
        timestamp = timestamp or datetime.now()
        
        # Aktivite tespiti
        activity = self._detect_activity(pose, position, head_position)
        current_zone = self._get_zone_at_position(position)
        
        # Aktif olay kontrolü
        if animal_id in self._active_events:
            event = self._active_events[animal_id]
            
            if activity == event.activity:
                # Aynı aktivite devam ediyor
                return event
            else:
                # Aktivite değişti - olayı sonlandır
                self._complete_event(animal_id)
        
        # Beslenme aktivitesi yoksa çık
        if activity == FeedingActivity.NOT_FEEDING:
            return None
        
        # Yeni olay oluştur
        import uuid
        event = FeedingEvent(
            id=str(uuid.uuid4())[:8],
            animal_id=animal_id,
            activity=activity,
            start_time=timestamp,
            location=position,
            zone=current_zone.id if current_zone else None,
            confidence=0.8
        )
        
        self._active_events[animal_id] = event
        
        # Bölge doluluk güncelle
        if current_zone:
            current_zone.current_occupancy += 1
            current_zone.total_visits += 1
        
        return event
    
    def _detect_activity(
        self,
        pose: str,
        position: Tuple[float, float],
        head_position: Optional[Tuple[float, float]]
    ) -> FeedingActivity:
        """Aktivite tespiti"""
        # Bölge kontrolü
        zone = self._get_zone_at_position(position)
        
        if zone:
            if zone.zone_type == "water":
                return FeedingActivity.DRINKING
            elif zone.zone_type == "feeder":
                return FeedingActivity.TROUGH_FEEDING
            elif zone.zone_type == "pasture":
                return FeedingActivity.GRAZING
        
        # Poz tabanlı tespit
        if pose == "eating":
            return FeedingActivity.GRAZING
        elif pose == "drinking":
            return FeedingActivity.DRINKING
        elif pose == "lying" or pose == "ruminating":
            return FeedingActivity.RUMINATING
        
        # Baş pozisyonu analizi
        if head_position and position:
            head_x, head_y = head_position
            body_x, body_y = position
            
            # Baş aşağıda ise beslenme olabilir
            if head_y > body_y + 20:  # Baş vücuttan aşağıda
                return FeedingActivity.GRAZING
        
        return FeedingActivity.NOT_FEEDING
    
    def _get_zone_at_position(
        self,
        position: Tuple[float, float]
    ) -> Optional[FeedingZone]:
        """Pozisyondaki bölgeyi bul"""
        for zone in self._zones.values():
            if self._point_in_polygon(position, zone.boundaries):
                return zone
        return None
    
    def _point_in_polygon(
        self,
        point: Tuple[float, float],
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """Nokta polygon içinde mi?"""
        if not polygon or len(polygon) < 3:
            return False
        
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
    
    def _complete_event(self, animal_id: str) -> Optional[FeedingEvent]:
        """Aktif olayı tamamla"""
        if animal_id not in self._active_events:
            return None
        
        event = self._active_events.pop(animal_id)
        event.complete()
        
        # Tahmini alım hesapla
        event.estimated_intake = self._estimate_intake(event)
        
        # Geçmişe ekle
        if animal_id not in self._event_history:
            self._event_history[animal_id] = deque(maxlen=self._max_history)
        self._event_history[animal_id].append(event)
        
        # Günlük istatistikleri güncelle
        self._update_daily_stats(event)
        
        # Bölge doluluk güncelle
        if event.zone and event.zone in self._zones:
            zone = self._zones[event.zone]
            zone.current_occupancy = max(0, zone.current_occupancy - 1)
            zone.total_usage_time += event.duration
        
        return event
    
    def _estimate_intake(self, event: FeedingEvent) -> float:
        """Besin/su alımı tahmini"""
        if event.activity in self._intake_rates:
            rate = self._intake_rates[event.activity]
            return rate * (event.duration / 60.0)  # dakikaya çevir
        return 0.0
    
    def _update_daily_stats(self, event: FeedingEvent) -> None:
        """Günlük istatistikleri güncelle"""
        date_key = event.start_time.strftime("%Y-%m-%d")
        stats_key = f"{event.animal_id}_{date_key}"
        
        if stats_key not in self._daily_stats:
            self._daily_stats[stats_key] = DailyFeedingStats(
                date=event.start_time.replace(hour=0, minute=0, second=0),
                animal_id=event.animal_id
            )
        
        stats = self._daily_stats[stats_key]
        duration_minutes = event.duration / 60.0
        
        if event.activity == FeedingActivity.GRAZING:
            stats.grazing_minutes += duration_minutes
            stats.feeding_sessions += 1
            stats.estimated_food_intake += event.estimated_intake
            
        elif event.activity == FeedingActivity.TROUGH_FEEDING:
            stats.trough_minutes += duration_minutes
            stats.feeding_sessions += 1
            stats.estimated_food_intake += event.estimated_intake
            
        elif event.activity == FeedingActivity.DRINKING:
            stats.drinking_minutes += duration_minutes
            stats.drinking_sessions += 1
            stats.estimated_water_intake += event.estimated_intake
            
        elif event.activity == FeedingActivity.RUMINATING:
            stats.ruminating_minutes += duration_minutes
    
    def get_active_events(self) -> Dict[str, FeedingEvent]:
        """Aktif beslenme olayları"""
        return self._active_events.copy()
    
    def get_history(
        self,
        animal_id: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[FeedingEvent]:
        """Beslenme geçmişi"""
        if animal_id not in self._event_history:
            return []
        
        events = list(self._event_history[animal_id])
        
        if start_time:
            events = [e for e in events if e.start_time >= start_time]
        if end_time:
            events = [e for e in events if e.start_time <= end_time]
        
        return events
    
    def get_daily_stats(
        self,
        animal_id: str,
        date: datetime = None
    ) -> Optional[DailyFeedingStats]:
        """Günlük istatistikler"""
        date = date or datetime.now()
        date_key = date.strftime("%Y-%m-%d")
        stats_key = f"{animal_id}_{date_key}"
        return self._daily_stats.get(stats_key)
    
    def get_feeding_summary(
        self,
        animal_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Beslenme özeti"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_grazing = 0.0
        total_drinking = 0.0
        total_ruminating = 0.0
        total_food = 0.0
        total_water = 0.0
        session_count = 0
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            stats = self.get_daily_stats(animal_id, date)
            
            if stats:
                total_grazing += stats.grazing_minutes
                total_drinking += stats.drinking_minutes
                total_ruminating += stats.ruminating_minutes
                total_food += stats.estimated_food_intake
                total_water += stats.estimated_water_intake
                session_count += stats.feeding_sessions
        
        return {
            "animal_id": animal_id,
            "period_days": days,
            "avg_daily_grazing_hours": (total_grazing / 60) / days,
            "avg_daily_drinking_minutes": total_drinking / days,
            "avg_daily_ruminating_hours": (total_ruminating / 60) / days,
            "avg_daily_food_intake_kg": total_food / days,
            "avg_daily_water_intake_l": total_water / days,
            "total_feeding_sessions": session_count
        }
    
    def detect_feeding_anomalies(
        self,
        animal_id: str,
        threshold_deviation: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Beslenme anomalileri tespit"""
        anomalies = []
        
        # Son 7 günlük ortalamayı hesapla
        summary = self.get_feeding_summary(animal_id, days=7)
        today_stats = self.get_daily_stats(animal_id)
        
        if not today_stats:
            return anomalies
        
        # Otlama süresi kontrolü
        avg_grazing = summary["avg_daily_grazing_hours"] * 60
        if avg_grazing > 0:
            deviation = abs(today_stats.grazing_minutes - avg_grazing) / avg_grazing
            if deviation > threshold_deviation:
                anomalies.append({
                    "type": "grazing_anomaly",
                    "expected_minutes": avg_grazing,
                    "actual_minutes": today_stats.grazing_minutes,
                    "deviation": deviation,
                    "severity": "high" if deviation > 0.5 else "medium"
                })
        
        # Su içme kontrolü
        avg_drinking = summary["avg_daily_drinking_minutes"]
        if avg_drinking > 0:
            deviation = abs(today_stats.drinking_minutes - avg_drinking) / avg_drinking
            if deviation > threshold_deviation:
                anomalies.append({
                    "type": "drinking_anomaly",
                    "expected_minutes": avg_drinking,
                    "actual_minutes": today_stats.drinking_minutes,
                    "deviation": deviation,
                    "severity": "high" if deviation > 0.5 else "medium"
                })
        
        return anomalies
    
    def get_zone_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Bölge istatistikleri"""
        stats = {}
        
        for zone_id, zone in self._zones.items():
            stats[zone_id] = {
                "name": zone.name,
                "type": zone.zone_type,
                "total_visits": zone.total_visits,
                "total_usage_hours": zone.total_usage_time / 3600,
                "current_occupancy": zone.current_occupancy,
                "capacity": zone.capacity,
                "utilization": zone.current_occupancy / zone.capacity if zone.capacity > 0 else 0
            }
        
        return stats
