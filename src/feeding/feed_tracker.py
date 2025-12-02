# src/feeding/feed_tracker.py
"""
Feed Tracker - Beslenme Davranışı İzleme
========================================

Hayvanların yemlik ziyaretlerini ve yeme sürelerini takip eder.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FeedingZone:
    """Yemlik bölgesi tanımı."""
    zone_id: str
    name: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    zone_type: str = "feeder"  # feeder, water, hay
    capacity: Optional[float] = None  # kg
    
    def contains(self, point: Tuple[int, int]) -> bool:
        """Nokta bu bölgede mi kontrol et."""
        x, y = point
        x1, y1, x2, y2 = self.bbox
        return x1 <= x <= x2 and y1 <= y <= y2
    
    @property
    def center(self) -> Tuple[int, int]:
        """Bölge merkezi."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def area(self) -> int:
        """Bölge alanı (piksel)."""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)


@dataclass
class FeedingSession:
    """Tek bir beslenme seansı."""
    session_id: str
    animal_id: str
    zone_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Detaylar
    head_positions: List[Tuple[int, int]] = field(default_factory=list)
    frame_count: int = 0
    confidence_sum: float = 0.0
    
    @property
    def duration(self) -> float:
        """Seans süresi (saniye)."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Seans hala aktif mi."""
        return self.end_time is None
    
    @property
    def avg_confidence(self) -> float:
        """Ortalama güven skoru."""
        if self.frame_count == 0:
            return 0.0
        return self.confidence_sum / self.frame_count
    
    def add_observation(self, position: Tuple[int, int], confidence: float = 1.0):
        """Gözlem ekle."""
        self.head_positions.append(position)
        self.frame_count += 1
        self.confidence_sum += confidence
    
    def close(self):
        """Seansı kapat."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> dict:
        """Sözlüğe dönüştür."""
        return {
            "session_id": self.session_id,
            "animal_id": self.animal_id,
            "zone_id": self.zone_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "frame_count": self.frame_count,
            "avg_confidence": self.avg_confidence
        }


@dataclass
class FeedingStats:
    """Hayvan beslenme istatistikleri."""
    animal_id: str
    total_sessions: int = 0
    total_duration: float = 0.0  # saniye
    avg_session_duration: float = 0.0
    sessions_per_day: float = 0.0
    favorite_zone: Optional[str] = None
    zone_visits: Dict[str, int] = field(default_factory=dict)
    daily_pattern: Dict[int, float] = field(default_factory=dict)  # saat -> toplam süre
    
    def to_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "total_sessions": self.total_sessions,
            "total_duration_minutes": self.total_duration / 60,
            "avg_session_duration_seconds": self.avg_session_duration,
            "sessions_per_day": self.sessions_per_day,
            "favorite_zone": self.favorite_zone,
            "zone_visits": self.zone_visits,
            "daily_pattern": self.daily_pattern
        }


class FeedTracker:
    """
    Beslenme davranışı takip sistemi.
    
    Kullanım:
        tracker = FeedTracker()
        tracker.add_zone("feeder1", "Ana Yemlik", (100, 100, 300, 200))
        tracker.update(animal_id="cow_001", position=(150, 150))
        stats = tracker.get_animal_stats("cow_001")
    """
    
    def __init__(
        self,
        session_timeout: float = 30.0,  # Yemlikten ayrılma süresi (saniye)
        min_session_duration: float = 5.0,  # Minimum seans süresi
        zone_enter_frames: int = 3  # Bölgeye giriş için gereken frame
    ):
        """
        Args:
            session_timeout: Yemlikten ayrılma kabul süresi
            min_session_duration: Geçerli seans minimum süresi
            zone_enter_frames: Bölgeye giriş teyidi için frame sayısı
        """
        self.session_timeout = session_timeout
        self.min_session_duration = min_session_duration
        self.zone_enter_frames = zone_enter_frames
        
        # Bölgeler
        self._zones: Dict[str, FeedingZone] = {}
        
        # Aktif seanslar: animal_id -> FeedingSession
        self._active_sessions: Dict[str, FeedingSession] = {}
        
        # Tamamlanan seanslar
        self._completed_sessions: List[FeedingSession] = []
        
        # Hayvan bölge sayaçları (giriş teyidi için)
        self._zone_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Son görülme zamanları
        self._last_seen: Dict[str, datetime] = {}
        
        # Session ID sayacı
        self._session_counter = 0
        
        logger.info("FeedTracker initialized")
    
    def add_zone(
        self,
        zone_id: str,
        name: str,
        bbox: Tuple[int, int, int, int],
        zone_type: str = "feeder",
        capacity: Optional[float] = None
    ) -> FeedingZone:
        """Yemlik bölgesi ekle."""
        zone = FeedingZone(
            zone_id=zone_id,
            name=name,
            bbox=bbox,
            zone_type=zone_type,
            capacity=capacity
        )
        self._zones[zone_id] = zone
        logger.info(f"Added feeding zone: {name} ({zone_id})")
        return zone
    
    def remove_zone(self, zone_id: str) -> bool:
        """Bölge kaldır."""
        if zone_id in self._zones:
            del self._zones[zone_id]
            return True
        return False
    
    def get_zones(self) -> List[FeedingZone]:
        """Tüm bölgeleri al."""
        return list(self._zones.values())
    
    def _generate_session_id(self) -> str:
        """Benzersiz seans ID oluştur."""
        self._session_counter += 1
        return f"session_{self._session_counter:06d}"
    
    def _find_zone(self, position: Tuple[int, int]) -> Optional[str]:
        """Konum hangi bölgede kontrol et."""
        for zone_id, zone in self._zones.items():
            if zone.contains(position):
                return zone_id
        return None
    
    def update(
        self,
        animal_id: str,
        position: Tuple[int, int],
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None
    ) -> Optional[FeedingSession]:
        """
        Hayvan konumunu güncelle.
        
        Args:
            animal_id: Hayvan ID
            position: (x, y) konum
            confidence: Tespit güveni
            timestamp: Zaman damgası
            
        Returns:
            Aktif seans varsa döndür
        """
        timestamp = timestamp or datetime.now()
        self._last_seen[animal_id] = timestamp
        
        # Hangi bölgede?
        current_zone = self._find_zone(position)
        
        # Aktif seans var mı?
        active_session = self._active_sessions.get(animal_id)
        
        if active_session:
            # Aynı bölgedeyse devam et
            if current_zone == active_session.zone_id:
                active_session.add_observation(position, confidence)
                self._zone_counters[animal_id][current_zone] = 0  # Reset counter
                return active_session
            
            # Farklı bölgedeyse veya bölge dışındaysa
            else:
                # Timeout kontrolü
                if (timestamp - active_session.start_time).total_seconds() > self.session_timeout:
                    # Seansı kapat
                    self._close_session(animal_id)
                    
                    # Yeni bölgedeyse yeni seans başlat
                    if current_zone:
                        return self._start_session(animal_id, current_zone, position, confidence, timestamp)
                else:
                    # Henüz timeout olmadı, gözlem ekle
                    active_session.add_observation(position, confidence)
                    return active_session
        
        else:
            # Aktif seans yok
            if current_zone:
                # Bölgeye giriş sayacı
                self._zone_counters[animal_id][current_zone] += 1
                
                # Yeterli frame ile bölgeye giriş teyit edildi mi?
                if self._zone_counters[animal_id][current_zone] >= self.zone_enter_frames:
                    return self._start_session(animal_id, current_zone, position, confidence, timestamp)
            else:
                # Bölge dışında, sayaçları sıfırla
                self._zone_counters[animal_id] = defaultdict(int)
        
        return None
    
    def _start_session(
        self,
        animal_id: str,
        zone_id: str,
        position: Tuple[int, int],
        confidence: float,
        timestamp: datetime
    ) -> FeedingSession:
        """Yeni seans başlat."""
        session = FeedingSession(
            session_id=self._generate_session_id(),
            animal_id=animal_id,
            zone_id=zone_id,
            start_time=timestamp
        )
        session.add_observation(position, confidence)
        
        self._active_sessions[animal_id] = session
        self._zone_counters[animal_id] = defaultdict(int)
        
        logger.debug(f"Started feeding session: {session.session_id} for {animal_id}")
        return session
    
    def _close_session(self, animal_id: str) -> Optional[FeedingSession]:
        """Seansı kapat."""
        session = self._active_sessions.pop(animal_id, None)
        
        if session:
            session.close()
            
            # Minimum süre kontrolü
            if session.duration >= self.min_session_duration:
                self._completed_sessions.append(session)
                logger.debug(
                    f"Closed feeding session: {session.session_id} "
                    f"duration={session.duration:.1f}s"
                )
            else:
                logger.debug(
                    f"Discarded short session: {session.session_id} "
                    f"duration={session.duration:.1f}s"
                )
        
        return session
    
    def check_timeouts(self):
        """Timeout olan seansları kapat."""
        now = datetime.now()
        to_close = []
        
        for animal_id, session in self._active_sessions.items():
            last_seen = self._last_seen.get(animal_id)
            if last_seen and (now - last_seen).total_seconds() > self.session_timeout:
                to_close.append(animal_id)
        
        for animal_id in to_close:
            self._close_session(animal_id)
    
    def get_active_sessions(self) -> List[FeedingSession]:
        """Aktif seansları al."""
        return list(self._active_sessions.values())
    
    def get_completed_sessions(
        self,
        animal_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[FeedingSession]:
        """Tamamlanan seansları al."""
        sessions = self._completed_sessions
        
        if animal_id:
            sessions = [s for s in sessions if s.animal_id == animal_id]
        if zone_id:
            sessions = [s for s in sessions if s.zone_id == zone_id]
        if since:
            sessions = [s for s in sessions if s.start_time >= since]
        
        return sessions[-limit:]
    
    def get_animal_stats(
        self,
        animal_id: str,
        period_days: int = 7
    ) -> FeedingStats:
        """Hayvan beslenme istatistiklerini hesapla."""
        since = datetime.now() - timedelta(days=period_days)
        sessions = self.get_completed_sessions(animal_id=animal_id, since=since)
        
        stats = FeedingStats(animal_id=animal_id)
        
        if not sessions:
            return stats
        
        # Temel istatistikler
        stats.total_sessions = len(sessions)
        stats.total_duration = sum(s.duration for s in sessions)
        stats.avg_session_duration = stats.total_duration / stats.total_sessions
        stats.sessions_per_day = stats.total_sessions / period_days
        
        # Bölge ziyaretleri
        for session in sessions:
            stats.zone_visits[session.zone_id] = stats.zone_visits.get(session.zone_id, 0) + 1
        
        # En çok ziyaret edilen bölge
        if stats.zone_visits:
            stats.favorite_zone = max(stats.zone_visits.keys(), key=lambda z: stats.zone_visits[z])
        
        # Günlük pattern (saat bazında)
        for session in sessions:
            hour = session.start_time.hour
            stats.daily_pattern[hour] = stats.daily_pattern.get(hour, 0) + session.duration
        
        return stats
    
    def get_zone_stats(self, zone_id: str, period_days: int = 7) -> dict:
        """Bölge istatistiklerini hesapla."""
        since = datetime.now() - timedelta(days=period_days)
        sessions = self.get_completed_sessions(zone_id=zone_id, since=since)
        
        if not sessions:
            return {
                "zone_id": zone_id,
                "total_sessions": 0,
                "total_duration": 0,
                "unique_animals": 0,
                "avg_session_duration": 0
            }
        
        unique_animals = set(s.animal_id for s in sessions)
        total_duration = sum(s.duration for s in sessions)
        
        return {
            "zone_id": zone_id,
            "zone_name": self._zones[zone_id].name if zone_id in self._zones else zone_id,
            "total_sessions": len(sessions),
            "total_duration_minutes": total_duration / 60,
            "unique_animals": len(unique_animals),
            "avg_session_duration_seconds": total_duration / len(sessions),
            "sessions_per_day": len(sessions) / period_days
        }
    
    def reset(self):
        """Tracker'ı sıfırla."""
        self._active_sessions.clear()
        self._completed_sessions.clear()
        self._zone_counters.clear()
        self._last_seen.clear()
        self._session_counter = 0
        logger.info("FeedTracker reset")
