"""
AI Animal Tracking System - Health Monitor
===========================================

Hayvan sağlık izleme modülü.
BCS (Body Condition Score), topalllık tespiti, anormallik algılama.
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import numpy as np

from src.tracking.object_tracker import Track
from src.behavior.behavior_analyzer import BehaviorType, BehaviorAnalysisResult


logger = logging.getLogger("animal_tracking.health")


# ===========================================
# Health Enums
# ===========================================

class HealthStatus(Enum):
    """Genel sağlık durumu"""
    HEALTHY = "healthy"
    ATTENTION = "attention"     # Dikkat gerektiriyor
    WARNING = "warning"         # Uyarı
    CRITICAL = "critical"       # Kritik


class LamenessScore(Enum):
    """Topallık skoru (1-5)"""
    NORMAL = 1          # Normal yürüyüş
    MILD = 2            # Hafif topallık
    MODERATE = 3        # Orta topallık
    SEVERE = 4          # Ciddi topallık
    NON_WEIGHT = 5      # Ağırlık vermiyor


class BodyConditionScore(Enum):
    """Vücut kondisyon skoru (1-5)"""
    EMACIATED = 1       # Aşırı zayıf
    THIN = 2            # Zayıf
    IDEAL = 3           # İdeal
    OVERWEIGHT = 4      # Kilolu
    OBESE = 5           # Obez


# Türkçe isimler
HEALTH_STATUS_TR = {
    HealthStatus.HEALTHY: "Sağlıklı",
    HealthStatus.ATTENTION: "Dikkat",
    HealthStatus.WARNING: "Uyarı",
    HealthStatus.CRITICAL: "Kritik",
}

LAMENESS_TR = {
    LamenessScore.NORMAL: "Normal",
    LamenessScore.MILD: "Hafif Topallık",
    LamenessScore.MODERATE: "Orta Topallık",
    LamenessScore.SEVERE: "Ciddi Topallık",
    LamenessScore.NON_WEIGHT: "Ağırlık Vermiyor",
}

BCS_TR = {
    BodyConditionScore.EMACIATED: "Aşırı Zayıf",
    BodyConditionScore.THIN: "Zayıf",
    BodyConditionScore.IDEAL: "İdeal",
    BodyConditionScore.OVERWEIGHT: "Kilolu",
    BodyConditionScore.OBESE: "Obez",
}


# ===========================================
# Data Classes
# ===========================================

@dataclass
class HealthConfig:
    """Sağlık izleme konfigürasyonu"""
    # Hareket analizi
    min_walking_speed: float = 2.0        # Minimum yürüme hızı (px/frame)
    normal_speed_range: Tuple[float, float] = (3.0, 15.0)
    
    # Davranış analizi
    abnormal_stationary_threshold: int = 300   # Anormal durağanlık (frame)
    isolation_distance: float = 200.0     # İzolasyon mesafesi (px)
    
    # Zaman pencereleri
    analysis_window: int = 300            # Analiz penceresi (frame)
    alert_cooldown: int = 100             # Uyarı bekleme süresi (frame)
    
    # FPS
    fps: float = 30.0


@dataclass
class HealthAlert:
    """Sağlık uyarısı"""
    alert_type: str
    severity: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    
    # İlişkili hayvan
    animal_id: Optional[str] = None
    track_id: Optional[int] = None
    
    # Detaylar
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "severity_tr": HEALTH_STATUS_TR.get(self.severity, self.severity.value),
            "message": self.message,
            "timestamp": self.timestamp,
            "animal_id": self.animal_id,
            "track_id": self.track_id,
            "details": self.details,
        }


@dataclass
class HealthMetrics:
    """Hayvan sağlık metrikleri"""
    track_id: int
    animal_id: Optional[str] = None
    
    # Genel durum
    overall_status: HealthStatus = HealthStatus.HEALTHY
    
    # BCS (şimdilik placeholder - görüntü analizi gerekli)
    bcs: Optional[BodyConditionScore] = None
    bcs_confidence: float = 0.0
    
    # Topallık
    lameness_score: LamenessScore = LamenessScore.NORMAL
    lameness_confidence: float = 0.0
    
    # Hareket metrikleri
    avg_speed: float = 0.0
    speed_variance: float = 0.0
    total_distance: float = 0.0
    
    # Davranış metrikleri
    stationary_ratio: float = 0.0
    eating_ratio: float = 0.0
    activity_score: float = 0.0
    
    # Anomali skorları
    anomaly_score: float = 0.0
    is_isolated: bool = False
    
    # Uyarılar
    alerts: List[HealthAlert] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "animal_id": self.animal_id,
            "overall_status": self.overall_status.value,
            "overall_status_tr": HEALTH_STATUS_TR.get(self.overall_status),
            "bcs": self.bcs.value if self.bcs else None,
            "bcs_tr": BCS_TR.get(self.bcs) if self.bcs else None,
            "lameness_score": self.lameness_score.value,
            "lameness_tr": LAMENESS_TR.get(self.lameness_score),
            "avg_speed": round(self.avg_speed, 2),
            "speed_variance": round(self.speed_variance, 4),
            "total_distance": round(self.total_distance, 2),
            "stationary_ratio": round(self.stationary_ratio, 4),
            "eating_ratio": round(self.eating_ratio, 4),
            "activity_score": round(self.activity_score, 4),
            "anomaly_score": round(self.anomaly_score, 4),
            "is_isolated": self.is_isolated,
            "alert_count": len(self.alerts),
        }


@dataclass
class AnimalHealthState:
    """Hayvan sağlık durumu state"""
    track_id: int
    
    # Geçmiş veriler
    speed_history: deque = field(default_factory=lambda: deque(maxlen=300))
    behavior_history: deque = field(default_factory=lambda: deque(maxlen=300))
    position_history: deque = field(default_factory=lambda: deque(maxlen=300))
    
    # Sayaçlar
    stationary_frames: int = 0
    eating_frames: int = 0
    walking_frames: int = 0
    
    # Son uyarı zamanı
    last_alert_frame: int = 0
    
    # Kümülatif metrikler
    total_distance: float = 0.0


# ===========================================
# Health Monitor
# ===========================================

class HealthMonitor:
    """
    Hayvan sağlık izleme ana sınıfı.
    
    Hareket ve davranış verilerinden sağlık durumu analiz eder.
    
    Kullanım:
        monitor = HealthMonitor()
        
        # Her frame'de
        for track in tracks:
            metrics = monitor.update(track, behavior_result)
            if metrics.alerts:
                for alert in metrics.alerts:
                    print(f"ALERT: {alert.message}")
    """
    
    def __init__(self, config: Optional[HealthConfig] = None):
        self.config = config or HealthConfig()
        
        # State yönetimi
        self._states: Dict[int, AnimalHealthState] = {}
        
        # Frame sayacı
        self._frame_id: int = 0
        
        # Tüm uyarılar
        self._all_alerts: List[HealthAlert] = []
        
        # İstatistikler
        self._total_updates: int = 0
        self._alert_counts: Dict[str, int] = defaultdict(int)
    
    @property
    def statistics(self) -> dict:
        return {
            "total_updates": self._total_updates,
            "active_animals": len(self._states),
            "total_alerts": len(self._all_alerts),
            "alert_counts": dict(self._alert_counts),
        }
    
    def update(
        self,
        track: Track,
        behavior_result: Optional[BehaviorAnalysisResult] = None,
        animal_id: Optional[str] = None,
    ) -> HealthMetrics:
        """
        Hayvan sağlık durumunu güncelle.
        
        Args:
            track: Track nesnesi
            behavior_result: Davranış analiz sonucu
            animal_id: Hayvan ID
            
        Returns:
            HealthMetrics
        """
        self._frame_id += 1
        self._total_updates += 1
        
        # State al veya oluştur
        if track.track_id not in self._states:
            self._states[track.track_id] = AnimalHealthState(track_id=track.track_id)
        
        state = self._states[track.track_id]
        
        # Hız hesapla ve kaydet
        speed = self._calculate_speed(track)
        state.speed_history.append(speed)
        
        # Pozisyon kaydet
        state.position_history.append(track.center)
        
        # Mesafe güncelle
        if len(state.position_history) >= 2:
            prev = state.position_history[-2]
            curr = state.position_history[-1]
            dist = np.sqrt((curr[0]-prev[0])**2 + (curr[1]-prev[1])**2)
            state.total_distance += dist
        
        # Davranış kaydet
        if behavior_result:
            state.behavior_history.append(behavior_result.behavior)
            
            # Sayaçlar
            if behavior_result.behavior == BehaviorType.STATIONARY:
                state.stationary_frames += 1
            if behavior_result.behavior == BehaviorType.EATING:
                state.eating_frames += 1
            if behavior_result.behavior == BehaviorType.WALKING:
                state.walking_frames += 1
        
        # Metrikler hesapla
        metrics = self._calculate_metrics(track, state, animal_id)
        
        # Anomali tespiti
        self._detect_anomalies(track, state, metrics)
        
        # Topallık analizi
        self._analyze_lameness(track, state, metrics)
        
        # Genel durum değerlendir
        self._evaluate_overall_status(metrics)
        
        return metrics
    
    def _calculate_speed(self, track: Track) -> float:
        """Track hızını hesapla"""
        if track.velocity is None:
            return 0.0
        vx, vy = track.velocity
        return np.sqrt(vx**2 + vy**2)
    
    def _calculate_metrics(
        self,
        track: Track,
        state: AnimalHealthState,
        animal_id: Optional[str],
    ) -> HealthMetrics:
        """Sağlık metriklerini hesapla"""
        metrics = HealthMetrics(
            track_id=track.track_id,
            animal_id=animal_id,
        )
        
        # Hız metrikleri
        if state.speed_history:
            speeds = list(state.speed_history)
            metrics.avg_speed = np.mean(speeds)
            metrics.speed_variance = np.var(speeds)
        
        metrics.total_distance = state.total_distance
        
        # Davranış oranları
        total_frames = len(state.behavior_history)
        if total_frames > 0:
            metrics.stationary_ratio = state.stationary_frames / total_frames
            metrics.eating_ratio = state.eating_frames / total_frames
        
        # Aktivite skoru (yüksek = aktif, düşük = pasif)
        if state.speed_history:
            metrics.activity_score = min(1.0, metrics.avg_speed / 10.0)
        
        return metrics
    
    def _detect_anomalies(
        self,
        track: Track,
        state: AnimalHealthState,
        metrics: HealthMetrics,
    ):
        """Anomali tespiti"""
        alerts = []
        
        # Uzun süreli durağanlık
        recent_behaviors = list(state.behavior_history)[-self.config.abnormal_stationary_threshold:]
        stationary_count = sum(
            1 for b in recent_behaviors
            if b in [BehaviorType.STATIONARY, BehaviorType.LYING]
        )
        
        if stationary_count >= self.config.abnormal_stationary_threshold * 0.9:
            if self._can_alert(state, "prolonged_stationary"):
                alert = HealthAlert(
                    alert_type="prolonged_stationary",
                    severity=HealthStatus.ATTENTION,
                    message=f"Track {track.track_id}: Uzun süredir hareketsiz",
                    track_id=track.track_id,
                    details={"stationary_frames": stationary_count},
                )
                alerts.append(alert)
                self._record_alert(state, alert)
        
        # Düşük aktivite
        if metrics.activity_score < 0.1 and len(state.speed_history) >= 100:
            metrics.anomaly_score += 0.3
        
        # Hız varyansı anormalliği
        if metrics.speed_variance > 100:
            metrics.anomaly_score += 0.2
        
        # Anomali skoru yüksekse uyar
        if metrics.anomaly_score > 0.5:
            if self._can_alert(state, "high_anomaly"):
                alert = HealthAlert(
                    alert_type="high_anomaly",
                    severity=HealthStatus.WARNING,
                    message=f"Track {track.track_id}: Anormal davranış tespit edildi",
                    track_id=track.track_id,
                    details={"anomaly_score": metrics.anomaly_score},
                )
                alerts.append(alert)
                self._record_alert(state, alert)
        
        metrics.alerts.extend(alerts)
    
    def _analyze_lameness(
        self,
        track: Track,
        state: AnimalHealthState,
        metrics: HealthMetrics,
    ):
        """
        Topallık analizi.
        
        Basit kural tabanlı - gerçek sistemde:
        - Yürüyüş simetrisi analizi
        - Adım uzunluğu karşılaştırması
        - Baş hareketi analizi
        - Pose estimation
        """
        # Basit hız tabanlı analiz
        if metrics.avg_speed < self.config.min_walking_speed and state.walking_frames > 30:
            # Çok yavaş yürüyüş
            metrics.lameness_score = LamenessScore.MILD
            metrics.lameness_confidence = 0.6
        
        # Yüksek hız varyansı (düzensiz yürüyüş)
        if metrics.speed_variance > 50 and state.walking_frames > 50:
            metrics.lameness_score = LamenessScore.MODERATE
            metrics.lameness_confidence = 0.5
    
    def _evaluate_overall_status(self, metrics: HealthMetrics):
        """Genel sağlık durumunu değerlendir"""
        # Varsayılan sağlıklı
        status = HealthStatus.HEALTHY
        
        # Topallık kontrolü
        if metrics.lameness_score.value >= 3:
            status = HealthStatus.WARNING
        elif metrics.lameness_score.value >= 2:
            status = max(status, HealthStatus.ATTENTION, key=lambda x: x.value)
        
        # Anomali kontrolü
        if metrics.anomaly_score > 0.7:
            status = max(status, HealthStatus.WARNING, key=lambda x: x.value)
        elif metrics.anomaly_score > 0.4:
            status = max(status, HealthStatus.ATTENTION, key=lambda x: x.value)
        
        # Çok sayıda uyarı
        if len(metrics.alerts) >= 3:
            status = HealthStatus.WARNING
        
        metrics.overall_status = status
    
    def _can_alert(self, state: AnimalHealthState, alert_type: str) -> bool:
        """Uyarı verebilir mi kontrol et (cooldown)"""
        return self._frame_id - state.last_alert_frame > self.config.alert_cooldown
    
    def _record_alert(self, state: AnimalHealthState, alert: HealthAlert):
        """Uyarı kaydet"""
        state.last_alert_frame = self._frame_id
        self._all_alerts.append(alert)
        self._alert_counts[alert.alert_type] += 1
        logger.warning(f"Health Alert: {alert.message}")
    
    def check_isolation(
        self,
        track: Track,
        all_tracks: List[Track],
        metrics: HealthMetrics,
    ):
        """
        İzolasyon kontrolü - hayvan sürüden ayrılmış mı?
        
        Args:
            track: Kontrol edilecek track
            all_tracks: Tüm track'ler
            metrics: Güncellenecek metrikler
        """
        if len(all_tracks) < 2:
            return
        
        # Diğer hayvanlara olan minimum mesafe
        min_distance = float('inf')
        
        for other in all_tracks:
            if other.track_id == track.track_id:
                continue
            
            dist = np.sqrt(
                (track.center[0] - other.center[0])**2 +
                (track.center[1] - other.center[1])**2
            )
            min_distance = min(min_distance, dist)
        
        if min_distance > self.config.isolation_distance:
            metrics.is_isolated = True
            metrics.anomaly_score += 0.2
    
    def get_alerts(
        self,
        track_id: Optional[int] = None,
        severity: Optional[HealthStatus] = None,
        limit: int = 100,
    ) -> List[HealthAlert]:
        """
        Uyarıları al.
        
        Args:
            track_id: Track ID filtresi
            severity: Önem derecesi filtresi
            limit: Maksimum sonuç
            
        Returns:
            HealthAlert listesi
        """
        alerts = self._all_alerts.copy()
        
        if track_id is not None:
            alerts = [a for a in alerts if a.track_id == track_id]
        
        if severity is not None:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Son N uyarı
        return alerts[-limit:]
    
    def get_state(self, track_id: int) -> Optional[AnimalHealthState]:
        """Track state al"""
        return self._states.get(track_id)
    
    def reset(self):
        """Monitor'ü sıfırla"""
        self._states.clear()
        self._all_alerts.clear()
        self._frame_id = 0
        self._total_updates = 0
        self._alert_counts.clear()
        logger.info("Health monitor reset")


# ===========================================
# Health Report Generator
# ===========================================

class HealthReportGenerator:
    """
    Sağlık raporu oluşturucu.
    
    Belirli bir hayvan veya tüm sürü için rapor oluşturur.
    """
    
    def __init__(self, monitor: HealthMonitor):
        self.monitor = monitor
    
    def generate_individual_report(
        self,
        track_id: int,
        animal_id: Optional[str] = None,
    ) -> dict:
        """Bireysel hayvan raporu"""
        state = self.monitor.get_state(track_id)
        if state is None:
            return {"error": "Track not found"}
        
        # Metrikler
        speeds = list(state.speed_history) if state.speed_history else []
        behaviors = list(state.behavior_history) if state.behavior_history else []
        
        # Davranış dağılımı
        behavior_dist = defaultdict(int)
        for b in behaviors:
            behavior_dist[b.value] += 1
        
        return {
            "track_id": track_id,
            "animal_id": animal_id,
            "total_frames": len(speeds),
            "total_distance": round(state.total_distance, 2),
            "avg_speed": round(np.mean(speeds), 2) if speeds else 0,
            "max_speed": round(np.max(speeds), 2) if speeds else 0,
            "min_speed": round(np.min(speeds), 2) if speeds else 0,
            "behavior_distribution": dict(behavior_dist),
            "stationary_frames": state.stationary_frames,
            "eating_frames": state.eating_frames,
            "walking_frames": state.walking_frames,
            "alert_count": len(self.monitor.get_alerts(track_id=track_id)),
        }
    
    def generate_herd_summary(self) -> dict:
        """Sürü özet raporu"""
        stats = self.monitor.statistics
        
        # Durum dağılımı (örnek)
        status_dist = {
            "healthy": 0,
            "attention": 0,
            "warning": 0,
            "critical": 0,
        }
        
        return {
            "total_animals": stats["active_animals"],
            "total_alerts": stats["total_alerts"],
            "alert_breakdown": stats["alert_counts"],
            "status_distribution": status_dist,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    monitor = HealthMonitor()
    
    # Fake track
    class FakeTrack:
        def __init__(self, track_id, center, velocity):
            self.track_id = track_id
            self.center = center
            self.velocity = velocity
    
    # Fake behavior result
    @dataclass
    class FakeBehaviorResult:
        behavior: BehaviorType
    
    print("=== Health Monitor Test ===\n")
    
    # Simülasyon
    track = FakeTrack(1, (100, 100), (5.0, 3.0))
    
    for i in range(50):
        # Pozisyon güncelle
        track.center = (100 + i*2, 100 + i)
        track.velocity = (2.0 + np.random.randn(), 1.0 + np.random.randn())
        
        behavior = FakeBehaviorResult(behavior=BehaviorType.WALKING)
        
        metrics = monitor.update(track, behavior)
    
    # Son metrikler
    print(f"Track ID: {metrics.track_id}")
    print(f"Overall Status: {metrics.overall_status.value}")
    print(f"Avg Speed: {metrics.avg_speed:.2f}")
    print(f"Total Distance: {metrics.total_distance:.2f}")
    print(f"Activity Score: {metrics.activity_score:.2f}")
    print(f"Lameness: {metrics.lameness_score.value} - {LAMENESS_TR[metrics.lameness_score]}")
    print(f"Alert Count: {len(metrics.alerts)}")
    
    # Rapor
    print("\n=== Statistics ===")
    for k, v in monitor.statistics.items():
        print(f"{k}: {v}")
