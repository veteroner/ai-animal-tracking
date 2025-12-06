"""
Hareket Analizi Modülü
Hayvan hareketlerini detaylı analiz eder
"""
from typing import Dict, List, Optional, Tuple, Deque
from dataclasses import dataclass
from collections import deque
import numpy as np
import math


@dataclass
class MotionMetrics:
    """Hareket metrikleri"""
    velocity: float  # m/s
    acceleration: float  # m/s²
    direction: float  # derece (0-360)
    angular_velocity: float  # derece/s
    distance_traveled: float  # m
    avg_speed: float  # m/s
    max_speed: float  # m/s


class MotionAnalyzer:
    """
    Hayvan hareketlerini analiz eder
    
    Özellikler:
    - Hız ve ivme hesaplama
    - Yön analizi
    - Hareket paternleri
    - Anomali tespiti
    """
    
    def __init__(
        self,
        history_size: int = 30,
        fps: float = 30.0,
        pixels_per_meter: float = 100.0
    ):
        """
        Args:
            history_size: Geçmiş pozisyon sayısı
            fps: Video FPS
            pixels_per_meter: Piksel/metre oranı (kalibrasyon)
        """
        self.history_size = history_size
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        
        # Her hayvan için pozisyon geçmişi
        self.position_history: Dict[str, Deque] = {}
        self.velocity_history: Dict[str, Deque] = {}
        
        # Toplam hareket istatistikleri
        self.total_distance: Dict[str, float] = {}
        self.motion_events: Dict[str, List] = {}
    
    def update(
        self,
        animal_id: str,
        position: Tuple[float, float],
        timestamp: float
    ) -> MotionMetrics:
        """
        Pozisyon güncellemesi ve hareket analizi
        
        Args:
            animal_id: Hayvan kimliği
            position: (x, y) pozisyon (piksel)
            timestamp: Zaman damgası
        
        Returns:
            MotionMetrics: Hesaplanan hareket metrikleri
        """
        # İlk kez görülüyorsa initialize et
        if animal_id not in self.position_history:
            self.position_history[animal_id] = deque(maxlen=self.history_size)
            self.velocity_history[animal_id] = deque(maxlen=self.history_size)
            self.total_distance[animal_id] = 0.0
            self.motion_events[animal_id] = []
        
        # Pozisyonu kaydet
        self.position_history[animal_id].append((position, timestamp))
        
        # Metrikleri hesapla
        metrics = self._calculate_metrics(animal_id)
        
        # Velocity'yi kaydet
        self.velocity_history[animal_id].append(metrics.velocity)
        
        # Toplam mesafeyi güncelle
        if len(self.position_history[animal_id]) >= 2:
            prev_pos, _ = self.position_history[animal_id][-2]
            distance = self._euclidean_distance(prev_pos, position)
            distance_meters = distance / self.pixels_per_meter
            self.total_distance[animal_id] += distance_meters
        
        return metrics
    
    def _calculate_metrics(self, animal_id: str) -> MotionMetrics:
        """Hareket metriklerini hesapla"""
        history = self.position_history[animal_id]
        
        if len(history) < 2:
            return MotionMetrics(
                velocity=0.0,
                acceleration=0.0,
                direction=0.0,
                angular_velocity=0.0,
                distance_traveled=0.0,
                avg_speed=0.0,
                max_speed=0.0
            )
        
        # Son iki pozisyon
        (pos1, t1), (pos2, t2) = history[-2], history[-1]
        
        # Hız hesaplama (m/s)
        displacement = self._euclidean_distance(pos1, pos2)
        time_diff = max(t2 - t1, 1/self.fps)  # Minimum 1 frame
        velocity_pixels = displacement / time_diff
        velocity = velocity_pixels / self.pixels_per_meter
        
        # İvme hesaplama
        if len(self.velocity_history[animal_id]) >= 2:
            prev_velocity = self.velocity_history[animal_id][-1]
            acceleration = (velocity - prev_velocity) / time_diff
        else:
            acceleration = 0.0
        
        # Yön hesaplama (0-360 derece)
        direction = self._calculate_direction(pos1, pos2)
        
        # Açısal hız
        if len(history) >= 3:
            (pos0, _), _, _ = history[-3], history[-2], history[-1]
            prev_direction = self._calculate_direction(pos0, pos1)
            angular_velocity = (direction - prev_direction) / time_diff
            
            # Normalize et (-180, 180)
            if angular_velocity > 180:
                angular_velocity -= 360
            elif angular_velocity < -180:
                angular_velocity += 360
        else:
            angular_velocity = 0.0
        
        # İstatistikler
        velocities = list(self.velocity_history[animal_id])
        avg_speed = np.mean(velocities) if velocities else 0.0
        max_speed = np.max(velocities) if velocities else 0.0
        
        return MotionMetrics(
            velocity=velocity,
            acceleration=acceleration,
            direction=direction,
            angular_velocity=angular_velocity,
            distance_traveled=self.total_distance[animal_id],
            avg_speed=avg_speed,
            max_speed=max_speed
        )
    
    def _euclidean_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """İki nokta arası Euclidean mesafe"""
        return math.sqrt(
            (pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2
        )
    
    def _calculate_direction(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Hareket yönü (0-360 derece)"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        
        # atan2 radyan cinsinden -π ile π arası döner
        angle_rad = math.atan2(dy, dx)
        
        # Dereceye çevir ve 0-360 aralığına normalize et
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    def detect_motion_patterns(
        self,
        animal_id: str
    ) -> Dict[str, any]:
        """
        Hareket paternlerini tespit et
        
        Returns:
            Dict: {
                'is_circling': bool,
                'is_pacing': bool,
                'is_zigzagging': bool,
                'movement_consistency': float,
                'preferred_direction': float
            }
        """
        if animal_id not in self.position_history:
            return {}
        
        history = list(self.position_history[animal_id])
        
        if len(history) < 10:
            return {
                'is_circling': False,
                'is_pacing': False,
                'is_zigzagging': False,
                'movement_consistency': 0.0,
                'preferred_direction': 0.0
            }
        
        # Yönleri hesapla
        directions = []
        for i in range(len(history) - 1):
            (pos1, _), (pos2, _) = history[i], history[i+1]
            direction = self._calculate_direction(pos1, pos2)
            directions.append(direction)
        
        # Dairesel hareket tespiti
        is_circling = self._detect_circling(directions)
        
        # Gidip gelme (pacing) tespiti
        is_pacing = self._detect_pacing(directions)
        
        # Zikzak hareket
        is_zigzagging = self._detect_zigzagging(directions)
        
        # Hareket tutarlılığı (0-1)
        direction_std = np.std(directions)
        consistency = max(0, 1 - (direction_std / 180))
        
        # Tercih edilen yön
        preferred_direction = np.mean(directions)
        
        return {
            'is_circling': is_circling,
            'is_pacing': is_pacing,
            'is_zigzagging': is_zigzagging,
            'movement_consistency': consistency,
            'preferred_direction': preferred_direction,
            'direction_std': direction_std
        }
    
    def _detect_circling(self, directions: List[float]) -> bool:
        """Dairesel hareket tespiti"""
        if len(directions) < 20:
            return False
        
        # Son 20 yönü kontrol et
        recent_directions = directions[-20:]
        
        # Toplam açı değişimi
        total_rotation = sum(
            self._angle_difference(recent_directions[i], recent_directions[i+1])
            for i in range(len(recent_directions) - 1)
        )
        
        # 360 dereceye yakınsa dairesel hareket
        return abs(total_rotation) > 270
    
    def _detect_pacing(self, directions: List[float]) -> bool:
        """Gidip gelme hareketi tespiti"""
        if len(directions) < 10:
            return False
        
        # Zıt yönlerde sürekli hareket
        reversals = 0
        threshold = 150  # derece
        
        for i in range(len(directions) - 1):
            angle_diff = abs(self._angle_difference(directions[i], directions[i+1]))
            if angle_diff > threshold:
                reversals += 1
        
        # Sık yön değiştirme
        return reversals > len(directions) * 0.3
    
    def _detect_zigzagging(self, directions: List[float]) -> bool:
        """Zikzak hareket tespiti"""
        if len(directions) < 6:
            return False
        
        # Sürekli sağa-sola dönüş
        direction_changes = []
        for i in range(len(directions) - 1):
            diff = self._angle_difference(directions[i], directions[i+1])
            if abs(diff) > 30:  # Önemli yön değişimi
                direction_changes.append(diff > 0)
        
        if len(direction_changes) < 4:
            return False
        
        # Alternatif dönüşler
        alternations = sum(
            1 for i in range(len(direction_changes) - 1)
            if direction_changes[i] != direction_changes[i+1]
        )
        
        return alternations > len(direction_changes) * 0.6
    
    def _angle_difference(self, angle1: float, angle2: float) -> float:
        """İki açı arasındaki en kısa fark"""
        diff = angle2 - angle1
        
        # -180 ile 180 arası normalize et
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        return diff
    
    def get_movement_summary(
        self,
        animal_id: str,
        time_window: int = 3600
    ) -> Dict:
        """
        Hareket özeti
        
        Returns:
            Dict: {
                'total_distance': float,
                'avg_velocity': float,
                'max_velocity': float,
                'active_time': float,
                'stationary_time': float
            }
        """
        if animal_id not in self.position_history:
            return {}
        
        velocities = list(self.velocity_history.get(animal_id, []))
        
        if not velocities:
            return {
                'total_distance': 0.0,
                'avg_velocity': 0.0,
                'max_velocity': 0.0,
                'active_time': 0.0,
                'stationary_time': 0.0
            }
        
        # Aktif/hareketsiz süre (velocity > 0.1 m/s)
        active_count = sum(1 for v in velocities if v > 0.1)
        stationary_count = len(velocities) - active_count
        
        frame_duration = 1 / self.fps
        active_time = active_count * frame_duration
        stationary_time = stationary_count * frame_duration
        
        return {
            'total_distance': self.total_distance.get(animal_id, 0.0),
            'avg_velocity': np.mean(velocities),
            'max_velocity': np.max(velocities),
            'active_time': active_time,
            'stationary_time': stationary_time,
            'movement_ratio': active_time / (active_time + stationary_time) if (active_time + stationary_time) > 0 else 0
        }
