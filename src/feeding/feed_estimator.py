# src/feeding/feed_estimator.py
"""
Feed Estimator - Yem Tüketim Tahmini
====================================

Beslenme seanslarından yem tüketimini tahmin eder.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from .feed_tracker import FeedingSession, FeedTracker

logger = logging.getLogger(__name__)


@dataclass
class FeedConsumptionEstimate:
    """Yem tüketim tahmini."""
    animal_id: str
    period_start: datetime
    period_end: datetime
    
    # Tahminler
    estimated_kg: float = 0.0
    confidence: float = 0.0
    
    # Detaylar
    total_feeding_time_minutes: float = 0.0
    session_count: int = 0
    feed_type: str = "general"
    
    def to_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "estimated_kg": round(self.estimated_kg, 2),
            "confidence": round(self.confidence, 2),
            "total_feeding_time_minutes": round(self.total_feeding_time_minutes, 1),
            "session_count": self.session_count,
            "feed_type": self.feed_type
        }


@dataclass
class CalibrationData:
    """Kalibrasyon verisi."""
    animal_id: str
    feed_type: str
    feeding_duration_seconds: float
    actual_consumption_kg: float
    timestamp: datetime = field(default_factory=datetime.now)


class FeedEstimator:
    """
    Yem tüketim tahmin sistemi.
    
    Süre bazlı ve kalibrasyon bazlı tahmin yapar.
    
    Kullanım:
        estimator = FeedEstimator()
        estimator.set_consumption_rate("cow", 0.5)  # kg/dakika
        estimate = estimator.estimate_consumption("cow_001", sessions)
    """
    
    # Varsayılan tüketim hızları (kg/dakika)
    DEFAULT_RATES = {
        "cow": 0.5,       # İnek: ~30 kg/gün, 60 dk yeme
        "sheep": 0.1,     # Koyun: ~2 kg/gün, 20 dk yeme
        "goat": 0.08,     # Keçi: ~1.5 kg/gün
        "horse": 0.3,     # At: ~10 kg/gün
        "pig": 0.15,      # Domuz: ~3 kg/gün
        "chicken": 0.005, # Tavuk: ~100g/gün
        "dog": 0.02,      # Köpek
        "cat": 0.005,     # Kedi
        "default": 0.1
    }
    
    def __init__(self):
        """Estimator'ı başlat."""
        # Tüketim hızları (özelleştirilebilir)
        self._consumption_rates: Dict[str, float] = dict(self.DEFAULT_RATES)
        
        # Hayvan bazında özel hızlar
        self._animal_rates: Dict[str, float] = {}
        
        # Kalibrasyon verileri
        self._calibration_data: List[CalibrationData] = []
        
        # Günlük tahminler cache
        self._daily_estimates: Dict[str, Dict[str, FeedConsumptionEstimate]] = {}
        
        logger.info("FeedEstimator initialized")
    
    def set_consumption_rate(
        self,
        species_or_animal: str,
        rate_kg_per_minute: float,
        is_animal_specific: bool = False
    ):
        """
        Tüketim hızı ayarla.
        
        Args:
            species_or_animal: Tür veya hayvan ID
            rate_kg_per_minute: Dakika başına kg
            is_animal_specific: Hayvan bazında mı?
        """
        if is_animal_specific:
            self._animal_rates[species_or_animal] = rate_kg_per_minute
        else:
            self._consumption_rates[species_or_animal] = rate_kg_per_minute
    
    def get_consumption_rate(
        self,
        animal_id: str,
        species: Optional[str] = None
    ) -> float:
        """Tüketim hızını al."""
        # Önce hayvan bazında kontrol
        if animal_id in self._animal_rates:
            return self._animal_rates[animal_id]
        
        # Sonra tür bazında
        if species and species.lower() in self._consumption_rates:
            return self._consumption_rates[species.lower()]
        
        # Varsayılan
        return self._consumption_rates.get("default", 0.1)
    
    def add_calibration(
        self,
        animal_id: str,
        feeding_duration_seconds: float,
        actual_consumption_kg: float,
        feed_type: str = "general"
    ):
        """
        Kalibrasyon verisi ekle.
        
        Gerçek yem miktarı bilindiğinde kullanılır.
        """
        data = CalibrationData(
            animal_id=animal_id,
            feed_type=feed_type,
            feeding_duration_seconds=feeding_duration_seconds,
            actual_consumption_kg=actual_consumption_kg
        )
        self._calibration_data.append(data)
        
        # Hayvan için özel rate hesapla
        if feeding_duration_seconds > 0:
            rate = actual_consumption_kg / (feeding_duration_seconds / 60)
            self._animal_rates[animal_id] = rate
            logger.info(
                f"Calibrated rate for {animal_id}: {rate:.4f} kg/min"
            )
    
    def estimate_consumption(
        self,
        animal_id: str,
        sessions: List[FeedingSession],
        species: Optional[str] = None
    ) -> FeedConsumptionEstimate:
        """
        Seanslardan yem tüketimini tahmin et.
        
        Args:
            animal_id: Hayvan ID
            sessions: Beslenme seansları
            species: Hayvan türü (opsiyonel)
            
        Returns:
            Tüketim tahmini
        """
        if not sessions:
            return FeedConsumptionEstimate(
                animal_id=animal_id,
                period_start=datetime.now(),
                period_end=datetime.now()
            )
        
        # Süreleri topla
        total_duration_seconds = sum(s.duration for s in sessions)
        total_duration_minutes = total_duration_seconds / 60
        
        # Tüketim hızını al
        rate = self.get_consumption_rate(animal_id, species)
        
        # Tahmini hesapla
        estimated_kg = total_duration_minutes * rate
        
        # Güven skoru (kalibrasyon varsa yüksek)
        confidence = 0.8 if animal_id in self._animal_rates else 0.5
        
        # Periyodu belirle
        start_times = [s.start_time for s in sessions]
        end_times = [s.end_time or datetime.now() for s in sessions]
        
        return FeedConsumptionEstimate(
            animal_id=animal_id,
            period_start=min(start_times),
            period_end=max(end_times),
            estimated_kg=estimated_kg,
            confidence=confidence,
            total_feeding_time_minutes=total_duration_minutes,
            session_count=len(sessions)
        )
    
    def estimate_daily_consumption(
        self,
        feed_tracker: FeedTracker,
        animal_id: str,
        date: Optional[datetime] = None,
        species: Optional[str] = None
    ) -> FeedConsumptionEstimate:
        """
        Günlük yem tüketimini tahmin et.
        
        Args:
            feed_tracker: FeedTracker instance
            animal_id: Hayvan ID
            date: Tarih (varsayılan: bugün)
            species: Hayvan türü
        """
        date = date or datetime.now()
        day_start = datetime(date.year, date.month, date.day)
        day_end = day_start + timedelta(days=1)
        
        # O günün seanslarını al
        sessions = feed_tracker.get_completed_sessions(
            animal_id=animal_id,
            since=day_start
        )
        
        # Gün sonu önceki seansları filtrele
        sessions = [s for s in sessions if s.start_time < day_end]
        
        estimate = self.estimate_consumption(animal_id, sessions, species)
        estimate.period_start = day_start
        estimate.period_end = day_end
        
        return estimate
    
    def estimate_weekly_consumption(
        self,
        feed_tracker: FeedTracker,
        animal_id: str,
        species: Optional[str] = None
    ) -> FeedConsumptionEstimate:
        """Haftalık yem tüketimini tahmin et."""
        now = datetime.now()
        week_start = now - timedelta(days=7)
        
        sessions = feed_tracker.get_completed_sessions(
            animal_id=animal_id,
            since=week_start
        )
        
        estimate = self.estimate_consumption(animal_id, sessions, species)
        estimate.period_start = week_start
        estimate.period_end = now
        
        return estimate
    
    def get_consumption_report(
        self,
        feed_tracker: FeedTracker,
        animal_ids: List[str],
        period_days: int = 7,
        species_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Çoklu hayvan için tüketim raporu.
        
        Args:
            feed_tracker: FeedTracker instance
            animal_ids: Hayvan ID listesi
            period_days: Rapor periyodu
            species_map: animal_id -> species eşlemesi
        """
        species_map = species_map or {}
        since = datetime.now() - timedelta(days=period_days)
        
        estimates = []
        total_kg = 0.0
        total_sessions = 0
        total_minutes = 0.0
        
        for animal_id in animal_ids:
            sessions = feed_tracker.get_completed_sessions(
                animal_id=animal_id,
                since=since
            )
            
            species = species_map.get(animal_id)
            estimate = self.estimate_consumption(animal_id, sessions, species)
            estimates.append(estimate)
            
            total_kg += estimate.estimated_kg
            total_sessions += estimate.session_count
            total_minutes += estimate.total_feeding_time_minutes
        
        return {
            "period_days": period_days,
            "period_start": since.isoformat(),
            "period_end": datetime.now().isoformat(),
            "animal_count": len(animal_ids),
            "total_estimated_kg": round(total_kg, 2),
            "total_sessions": total_sessions,
            "total_feeding_time_hours": round(total_minutes / 60, 2),
            "avg_kg_per_animal": round(total_kg / len(animal_ids), 2) if animal_ids else 0,
            "estimates": [e.to_dict() for e in estimates]
        }
    
    def detect_feeding_anomalies(
        self,
        feed_tracker: FeedTracker,
        animal_id: str,
        threshold_std: float = 2.0
    ) -> List[dict]:
        """
        Beslenme anomalilerini tespit et.
        
        Normal dışı yeme davranışlarını bulur:
        - Çok uzun/kısa seanslar
        - Normalden az/çok yeme
        
        Args:
            feed_tracker: FeedTracker instance
            animal_id: Hayvan ID
            threshold_std: Standart sapma eşiği
        """
        # Son 30 günlük veriyi al
        sessions = feed_tracker.get_completed_sessions(
            animal_id=animal_id,
            since=datetime.now() - timedelta(days=30)
        )
        
        if len(sessions) < 7:
            return []  # Yeterli veri yok
        
        anomalies = []
        durations = [s.duration for s in sessions]
        
        mean_duration = np.mean(durations)
        std_duration = np.std(durations)
        
        for session in sessions:
            z_score = (session.duration - mean_duration) / std_duration if std_duration > 0 else 0
            
            if abs(z_score) > threshold_std:
                anomaly_type = "long_session" if z_score > 0 else "short_session"
                anomalies.append({
                    "session_id": session.session_id,
                    "animal_id": animal_id,
                    "anomaly_type": anomaly_type,
                    "z_score": round(z_score, 2),
                    "duration_seconds": session.duration,
                    "expected_duration": round(mean_duration, 1),
                    "timestamp": session.start_time.isoformat()
                })
        
        return anomalies
