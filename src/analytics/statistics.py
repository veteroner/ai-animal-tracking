"""
İstatistik modülü - Hayvan takip istatistikleri
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import defaultdict


@dataclass
class AnimalStatistics:
    """Tek bir hayvan için istatistikler"""
    animal_id: str
    total_detections: int = 0
    total_tracking_time: float = 0.0  # saniye
    average_speed: float = 0.0
    total_distance: float = 0.0
    behavior_counts: Dict[str, int] = None
    zone_visits: Dict[str, int] = None
    health_score: float = 100.0
    last_seen: Optional[datetime] = None
    
    def __post_init__(self):
        if self.behavior_counts is None:
            self.behavior_counts = {}
        if self.zone_visits is None:
            self.zone_visits = {}


@dataclass
class SystemStatistics:
    """Sistem geneli istatistikler"""
    total_animals: int = 0
    active_cameras: int = 0
    total_detections_today: int = 0
    average_fps: float = 0.0
    uptime_hours: float = 0.0
    alerts_today: int = 0
    storage_used_gb: float = 0.0


class StatisticsCalculator:
    """İstatistik hesaplama sınıfı"""
    
    def __init__(self):
        self.animal_stats: Dict[str, AnimalStatistics] = {}
        self.hourly_detections: Dict[int, int] = defaultdict(int)
        self.daily_detections: Dict[str, int] = defaultdict(int)
        self.behavior_distribution: Dict[str, int] = defaultdict(int)
        self._start_time = datetime.now()
        
    def update_detection(self, animal_id: str, detection_data: Dict[str, Any]) -> None:
        """Yeni tespit ile istatistikleri güncelle"""
        if animal_id not in self.animal_stats:
            self.animal_stats[animal_id] = AnimalStatistics(animal_id=animal_id)
            
        stats = self.animal_stats[animal_id]
        stats.total_detections += 1
        stats.last_seen = datetime.now()
        
        # Saatlik ve günlük tespitler
        current_hour = datetime.now().hour
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.hourly_detections[current_hour] += 1
        self.daily_detections[current_date] += 1
        
        # Davranış istatistikleri
        if 'behavior' in detection_data:
            behavior = detection_data['behavior']
            stats.behavior_counts[behavior] = stats.behavior_counts.get(behavior, 0) + 1
            self.behavior_distribution[behavior] += 1
            
        # Bölge ziyaretleri
        if 'zone' in detection_data:
            zone = detection_data['zone']
            stats.zone_visits[zone] = stats.zone_visits.get(zone, 0) + 1
            
    def update_tracking(self, animal_id: str, positions: List[tuple], time_delta: float) -> None:
        """Takip verisi ile istatistikleri güncelle"""
        if animal_id not in self.animal_stats:
            self.animal_stats[animal_id] = AnimalStatistics(animal_id=animal_id)
            
        stats = self.animal_stats[animal_id]
        stats.total_tracking_time += time_delta
        
        # Mesafe hesapla
        if len(positions) >= 2:
            total_distance = 0.0
            for i in range(1, len(positions)):
                p1, p2 = positions[i-1], positions[i]
                distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                total_distance += distance
                
            stats.total_distance += total_distance
            
            # Ortalama hız güncelle
            if stats.total_tracking_time > 0:
                stats.average_speed = stats.total_distance / stats.total_tracking_time
                
    def get_animal_statistics(self, animal_id: str) -> Optional[AnimalStatistics]:
        """Belirli bir hayvanın istatistiklerini getir"""
        return self.animal_stats.get(animal_id)
        
    def get_all_statistics(self) -> Dict[str, AnimalStatistics]:
        """Tüm hayvan istatistiklerini getir"""
        return self.animal_stats.copy()
        
    def get_system_statistics(self) -> SystemStatistics:
        """Sistem istatistiklerini hesapla"""
        today = datetime.now().strftime("%Y-%m-%d")
        uptime = (datetime.now() - self._start_time).total_seconds() / 3600
        
        return SystemStatistics(
            total_animals=len(self.animal_stats),
            total_detections_today=self.daily_detections.get(today, 0),
            uptime_hours=uptime
        )
        
    def get_hourly_distribution(self) -> Dict[int, int]:
        """Saatlik tespit dağılımı"""
        return dict(self.hourly_detections)
        
    def get_behavior_distribution(self) -> Dict[str, int]:
        """Davranış dağılımı"""
        return dict(self.behavior_distribution)
        
    def get_top_active_animals(self, limit: int = 10) -> List[AnimalStatistics]:
        """En aktif hayvanları getir"""
        sorted_stats = sorted(
            self.animal_stats.values(),
            key=lambda x: x.total_detections,
            reverse=True
        )
        return sorted_stats[:limit]
        
    def calculate_activity_score(self, animal_id: str) -> float:
        """Aktivite skoru hesapla (0-100)"""
        stats = self.animal_stats.get(animal_id)
        if not stats:
            return 0.0
            
        # Basit aktivite skoru hesaplama
        detection_score = min(stats.total_detections / 100, 1.0) * 30
        distance_score = min(stats.total_distance / 1000, 1.0) * 30
        behavior_variety = min(len(stats.behavior_counts) / 5, 1.0) * 20
        zone_variety = min(len(stats.zone_visits) / 5, 1.0) * 20
        
        return detection_score + distance_score + behavior_variety + zone_variety
        
    def reset_daily_statistics(self) -> None:
        """Günlük istatistikleri sıfırla"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # Eski günlük verileri temizle (son 30 gün hariç)
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.daily_detections = {
            k: v for k, v in self.daily_detections.items()
            if k >= cutoff_date
        }
        
    def export_statistics(self) -> Dict[str, Any]:
        """İstatistikleri dışa aktar"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'total_animals': len(self.animal_stats),
                'uptime_hours': (datetime.now() - self._start_time).total_seconds() / 3600
            },
            'animals': {
                animal_id: {
                    'total_detections': stats.total_detections,
                    'total_tracking_time': stats.total_tracking_time,
                    'average_speed': stats.average_speed,
                    'total_distance': stats.total_distance,
                    'health_score': stats.health_score,
                    'last_seen': stats.last_seen.isoformat() if stats.last_seen else None
                }
                for animal_id, stats in self.animal_stats.items()
            },
            'hourly_distribution': dict(self.hourly_detections),
            'behavior_distribution': dict(self.behavior_distribution)
        }
