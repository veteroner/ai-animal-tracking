"""
Aktivite Tespit Modülü
Hayvan aktivitelerini tespit ve ölçümler
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np


@dataclass
class Activity:
    """Aktivite kaydı"""
    activity_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    intensity: float = 0.0
    location: Optional[Tuple[int, int]] = None
    metadata: Optional[Dict] = None


class ActivityDetector:
    """
    Hayvan aktivitelerini tespit eder
    
    Tespit edilen aktiviteler:
    - Yeme (feeding)
    - İçme (drinking)
    - Yürüme (walking)
    - Koşma (running)
    - Dinlenme (resting)
    - Geviş getirme (ruminating)
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Activity]] = {}
        self.completed_activities: Dict[str, List[Activity]] = {}
        
        # Aktivite parametreleri
        self.min_eating_duration = 5.0  # saniye
        self.min_drinking_duration = 2.0
        self.min_resting_duration = 60.0
        
        # Hız eşikleri (m/s cinsinden, piksel/frame'e dönüştürülmeli)
        self.walking_speed_range = (0.3, 2.0)
        self.running_speed_threshold = 2.0
    
    def update(
        self,
        animal_id: str,
        position: Tuple[int, int],
        velocity: float,
        zones: Dict[str, any],
        timestamp: datetime
    ):
        """
        Aktivite durumunu güncelle
        
        Args:
            animal_id: Hayvan kimliği
            position: Mevcut pozisyon
            velocity: Anlık hız
            zones: Tanımlı bölgeler
            timestamp: Zaman damgası
        """
        if animal_id not in self.active_sessions:
            self.active_sessions[animal_id] = {}
        
        if animal_id not in self.completed_activities:
            self.completed_activities[animal_id] = []
        
        # Mevcut aktiviteleri kontrol et
        current_activities = self._detect_current_activities(
            position, velocity, zones
        )
        
        # Aktif oturumları güncelle
        active = self.active_sessions[animal_id]
        
        for activity_type in current_activities:
            if activity_type not in active:
                # Yeni aktivite başlat
                active[activity_type] = Activity(
                    activity_type=activity_type,
                    start_time=timestamp,
                    location=position
                )
        
        # Bitmiş aktiviteleri tespit et
        for activity_type in list(active.keys()):
            if activity_type not in current_activities:
                # Aktivite sona erdi
                activity = active[activity_type]
                activity.end_time = timestamp
                activity.duration = (
                    activity.end_time - activity.start_time
                ).total_seconds()
                
                # Minimum süre kontrolü
                if self._is_valid_activity(activity):
                    self.completed_activities[animal_id].append(activity)
                
                del active[activity_type]
    
    def _detect_current_activities(
        self,
        position: Tuple[int, int],
        velocity: float,
        zones: Dict[str, any]
    ) -> List[str]:
        """Mevcut aktiviteleri tespit et"""
        activities = []
        
        # Yeme aktivitesi
        if 'feeder' in zones and self._is_in_zone(position, zones['feeder']):
            if velocity < 0.2:
                activities.append('eating')
        
        # İçme aktivitesi
        if 'water' in zones and self._is_in_zone(position, zones['water']):
            if velocity < 0.1:
                activities.append('drinking')
        
        # Hareket aktiviteleri
        if velocity >= self.running_speed_threshold:
            activities.append('running')
        elif velocity >= self.walking_speed_range[0]:
            activities.append('walking')
        elif velocity < 0.1:
            activities.append('resting')
        
        return activities
    
    def _is_in_zone(
        self,
        position: Tuple[int, int],
        zone: Dict
    ) -> bool:
        """Pozisyonun bölge içinde olup olmadığını kontrol et"""
        x, y = position
        x1, y1, x2, y2 = zone['bbox']
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _is_valid_activity(self, activity: Activity) -> bool:
        """Aktivitenin geçerli olup olmadığını kontrol et"""
        if activity.activity_type == 'eating':
            return activity.duration >= self.min_eating_duration
        elif activity.activity_type == 'drinking':
            return activity.duration >= self.min_drinking_duration
        elif activity.activity_type == 'resting':
            return activity.duration >= self.min_resting_duration
        
        return True  # Diğer aktiviteler her zaman geçerli
    
    def get_daily_summary(
        self,
        animal_id: str,
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Günlük aktivite özeti
        
        Returns:
            Dict: {
                'eating': {'count': 10, 'total_duration': 300, 'avg_duration': 30},
                'drinking': {...},
                'walking': {...},
                ...
            }
        """
        if animal_id not in self.completed_activities:
            return {}
        
        if date is None:
            date = datetime.now()
        
        # Günün başlangıç ve bitişi
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Günün aktivitelerini filtrele
        daily_activities = [
            a for a in self.completed_activities[animal_id]
            if day_start <= a.start_time < day_end
        ]
        
        # Aktivite tipine göre grupla
        summary = {}
        
        for activity in daily_activities:
            activity_type = activity.activity_type
            
            if activity_type not in summary:
                summary[activity_type] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'durations': []
                }
            
            summary[activity_type]['count'] += 1
            summary[activity_type]['total_duration'] += activity.duration
            summary[activity_type]['durations'].append(activity.duration)
        
        # Ortalama hesapla
        for activity_type in summary:
            durations = summary[activity_type]['durations']
            summary[activity_type]['avg_duration'] = np.mean(durations)
            summary[activity_type]['std_duration'] = np.std(durations)
            del summary[activity_type]['durations']  # Ham veriyi kaldır
        
        return summary
    
    def get_hourly_pattern(
        self,
        animal_id: str,
        activity_type: str,
        days: int = 7
    ) -> Dict[int, float]:
        """
        Saatlik aktivite deseni
        
        Args:
            animal_id: Hayvan kimliği
            activity_type: Aktivite tipi
            days: Kaç günlük veri
        
        Returns:
            Dict[int, float]: {0: 120.0, 1: 90.0, ...} (saat: toplam süre)
        """
        if animal_id not in self.completed_activities:
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filtreleme
        relevant_activities = [
            a for a in self.completed_activities[animal_id]
            if a.activity_type == activity_type and a.start_time >= cutoff_date
        ]
        
        # Saatlere göre grupla
        hourly_data = {h: 0.0 for h in range(24)}
        
        for activity in relevant_activities:
            hour = activity.start_time.hour
            hourly_data[hour] += activity.duration
        
        return hourly_data
    
    def detect_activity_anomalies(
        self,
        animal_id: str,
        baseline: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Aktivite anormalliklerini tespit et
        
        Returns:
            List[Dict]: [
                {
                    'type': 'low_eating_frequency',
                    'severity': 'medium',
                    'message': '...'
                },
                ...
            ]
        """
        anomalies = []
        summary = self.get_daily_summary(animal_id)
        
        # Yeme sıklığı kontrolü
        if 'eating' in summary:
            eating_count = summary['eating']['count']
            if eating_count < 5:  # Günde 5'ten az yeme seansı
                anomalies.append({
                    'type': 'low_eating_frequency',
                    'severity': 'medium',
                    'current_value': eating_count,
                    'expected_range': (5, 15),
                    'message': f'Düşük yeme sıklığı: günde {eating_count} kez'
                })
        else:
            anomalies.append({
                'type': 'no_eating_detected',
                'severity': 'high',
                'message': 'Bugün yeme aktivitesi tespit edilmedi'
            })
        
        # İçme sıklığı
        if 'drinking' not in summary:
            anomalies.append({
                'type': 'no_drinking_detected',
                'severity': 'high',
                'message': 'Bugün içme aktivitesi tespit edilmedi'
            })
        
        # Aşırı hareketsizlik
        if 'resting' in summary:
            resting_duration = summary['resting']['total_duration']
            if resting_duration > 18 * 3600:  # 18 saatten fazla dinlenme
                anomalies.append({
                    'type': 'excessive_resting',
                    'severity': 'medium',
                    'current_value': resting_duration / 3600,
                    'message': f'Aşırı dinlenme: {resting_duration/3600:.1f} saat'
                })
        
        # Hareket eksikliği
        total_movement = (
            summary.get('walking', {}).get('total_duration', 0) +
            summary.get('running', {}).get('total_duration', 0)
        )
        
        if total_movement < 1800:  # 30 dk'dan az hareket
            anomalies.append({
                'type': 'low_movement',
                'severity': 'low',
                'current_value': total_movement / 60,
                'expected_range': (30, 180),
                'message': f'Düşük hareket: {total_movement/60:.1f} dakika'
            })
        
        return anomalies
    
    def get_activity_timeline(
        self,
        animal_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Activity]:
        """Belirli zaman aralığındaki aktiviteleri getir"""
        if animal_id not in self.completed_activities:
            return []
        
        return [
            a for a in self.completed_activities[animal_id]
            if start_time <= a.start_time <= end_time
        ]
