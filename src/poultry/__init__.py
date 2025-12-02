# src/poultry/__init__.py
"""
AI Animal Tracking System - Kanatlı Hayvan Modülü
=================================================

Tavuk, hindi, kaz, ördek gibi kanatlı hayvanların
tespiti, takibi ve davranış analizi.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


# ===========================================
# Kanatlı Hayvan Sınıfları
# ===========================================

class PoultryType(str, Enum):
    """Kanatlı hayvan türleri."""
    CHICKEN = "chicken"          # Tavuk
    ROOSTER = "rooster"          # Horoz
    CHICK = "chick"              # Civciv
    TURKEY = "turkey"            # Hindi
    GOOSE = "goose"              # Kaz
    DUCK = "duck"                # Ördek
    QUAIL = "quail"              # Bıldırcın
    GUINEA_FOWL = "guinea_fowl"  # Beç tavuğu
    PHEASANT = "pheasant"        # Sülün
    UNKNOWN_BIRD = "unknown_bird"


# Türkçe karşılıklar
POULTRY_NAMES_TR = {
    PoultryType.CHICKEN: "Tavuk",
    PoultryType.ROOSTER: "Horoz",
    PoultryType.CHICK: "Civciv",
    PoultryType.TURKEY: "Hindi",
    PoultryType.GOOSE: "Kaz",
    PoultryType.DUCK: "Ördek",
    PoultryType.QUAIL: "Bıldırcın",
    PoultryType.GUINEA_FOWL: "Beç Tavuğu",
    PoultryType.PHEASANT: "Sülün",
    PoultryType.UNKNOWN_BIRD: "Bilinmeyen Kuş",
}


class PoultryBehavior(str, Enum):
    """Kanatlı davranış tipleri."""
    # Normal davranışlar
    FEEDING = "feeding"              # Yem yeme
    DRINKING = "drinking"            # Su içme
    ROOSTING = "roosting"            # Tüneme
    NESTING = "nesting"              # Yumurtlama
    DUST_BATHING = "dust_bathing"    # Toz banyosu
    PREENING = "preening"            # Tüy temizleme
    WALKING = "walking"              # Yürüme
    RUNNING = "running"              # Koşma
    RESTING = "resting"              # Dinlenme
    FORAGING = "foraging"            # Yiyecek arama
    
    # Sosyal davranışlar
    FLOCKING = "flocking"            # Sürü halinde hareket
    PECKING_ORDER = "pecking_order"  # Gagalama sıralaması
    MATING = "mating"                # Çiftleşme
    BROODING = "brooding"            # Kuluçkaya yatma
    
    # Stres/Anormal davranışlar
    FEATHER_PECKING = "feather_pecking"  # Tüy gagalama (stres)
    CANNIBALISM = "cannibalism"          # Yamyamlık
    PILING = "piling"                    # Üst üste yığılma
    PANIC = "panic"                      # Panik
    LETHARGY = "lethargy"                # Durgunluk
    ISOLATION = "isolation"              # Sürüden ayrılma


BEHAVIOR_NAMES_TR = {
    PoultryBehavior.FEEDING: "Yem Yeme",
    PoultryBehavior.DRINKING: "Su İçme",
    PoultryBehavior.ROOSTING: "Tüneme",
    PoultryBehavior.NESTING: "Yumurtlama",
    PoultryBehavior.DUST_BATHING: "Toz Banyosu",
    PoultryBehavior.PREENING: "Tüy Temizleme",
    PoultryBehavior.WALKING: "Yürüme",
    PoultryBehavior.RUNNING: "Koşma",
    PoultryBehavior.RESTING: "Dinlenme",
    PoultryBehavior.FORAGING: "Yiyecek Arama",
    PoultryBehavior.FLOCKING: "Sürü Hareketi",
    PoultryBehavior.PECKING_ORDER: "Gagalama Sıralaması",
    PoultryBehavior.MATING: "Çiftleşme",
    PoultryBehavior.BROODING: "Kuluçka",
    PoultryBehavior.FEATHER_PECKING: "Tüy Gagalama (Stres)",
    PoultryBehavior.CANNIBALISM: "Yamyamlık",
    PoultryBehavior.PILING: "Yığılma",
    PoultryBehavior.PANIC: "Panik",
    PoultryBehavior.LETHARGY: "Durgunluk",
    PoultryBehavior.ISOLATION: "İzolasyon",
}


class PoultryHealthStatus(str, Enum):
    """Kanatlı sağlık durumu."""
    HEALTHY = "healthy"
    SICK = "sick"
    INJURED = "injured"
    MOLTING = "molting"      # Tüy dökümü
    BROODY = "broody"        # Kuluçka
    STRESSED = "stressed"
    DEAD = "dead"


class CoopZoneType(str, Enum):
    """Kümes bölge tipleri."""
    FEEDER = "feeder"              # Yemlik
    WATERER = "waterer"            # Suluk
    ROOST = "roost"                # Tünek
    NEST_BOX = "nest_box"          # Yumurtlama kutusu
    DUST_BATH = "dust_bath"        # Toz banyosu alanı
    FREE_RANGE = "free_range"      # Serbest dolaşım
    BROODER = "brooder"            # Civciv büyütme
    QUARANTINE = "quarantine"      # Karantina


ZONE_NAMES_TR = {
    CoopZoneType.FEEDER: "Yemlik",
    CoopZoneType.WATERER: "Suluk",
    CoopZoneType.ROOST: "Tünek",
    CoopZoneType.NEST_BOX: "Yumurtlama Kutusu",
    CoopZoneType.DUST_BATH: "Toz Banyosu",
    CoopZoneType.FREE_RANGE: "Serbest Alan",
    CoopZoneType.BROODER: "Civciv Bölümü",
    CoopZoneType.QUARANTINE: "Karantina",
}


# ===========================================
# Data Classes
# ===========================================

@dataclass
class PoultryDetection:
    """Tek bir kanatlı tespit sonucu."""
    poultry_id: str
    poultry_type: PoultryType
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Ek özellikler
    estimated_age: Optional[str] = None  # "chick", "pullet", "adult"
    color: Optional[str] = None
    health_status: PoultryHealthStatus = PoultryHealthStatus.HEALTHY
    current_zone: Optional[CoopZoneType] = None
    behavior: Optional[PoultryBehavior] = None
    
    def to_dict(self) -> Dict:
        return {
            "poultry_id": self.poultry_id,
            "poultry_type": self.poultry_type.value,
            "poultry_type_tr": POULTRY_NAMES_TR.get(self.poultry_type, ""),
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox,
            "center": self.center,
            "timestamp": self.timestamp.isoformat(),
            "estimated_age": self.estimated_age,
            "health_status": self.health_status.value,
            "current_zone": self.current_zone.value if self.current_zone else None,
            "behavior": self.behavior.value if self.behavior else None,
        }


@dataclass
class EggProduction:
    """Yumurta üretim kaydı."""
    record_id: str
    nest_box_id: str
    timestamp: datetime
    egg_count: int = 1
    poultry_id: Optional[str] = None  # Hangi tavuk yumurtladı
    egg_quality: str = "normal"  # normal, soft_shell, double_yolk, blood_spot
    
    def to_dict(self) -> Dict:
        return {
            "record_id": self.record_id,
            "nest_box_id": self.nest_box_id,
            "timestamp": self.timestamp.isoformat(),
            "egg_count": self.egg_count,
            "poultry_id": self.poultry_id,
            "egg_quality": self.egg_quality,
        }


@dataclass
class CoopZone:
    """Kümes bölgesi."""
    zone_id: str
    zone_type: CoopZoneType
    name: str
    bbox: Tuple[int, int, int, int]
    capacity: int = 0
    current_count: int = 0
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Nokta bu bölge içinde mi?"""
        x, y = point
        x1, y1, x2, y2 = self.bbox
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def to_dict(self) -> Dict:
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type.value,
            "zone_type_tr": ZONE_NAMES_TR.get(self.zone_type, ""),
            "name": self.name,
            "bbox": self.bbox,
            "capacity": self.capacity,
            "current_count": self.current_count,
        }


# ===========================================
# Kanatlı Davranış Analizi
# ===========================================

class PoultryBehaviorAnalyzer:
    """
    Kanatlı hayvan davranış analizörü.
    
    Hareket paternleri, konum ve süre bazlı davranış tespiti.
    """
    
    def __init__(self):
        self.position_history: Dict[str, List[Tuple[datetime, Tuple[int, int]]]] = {}
        self.behavior_history: Dict[str, List[Tuple[datetime, PoultryBehavior]]] = {}
        self.zones: List[CoopZone] = []
        
        # Davranış parametreleri
        self.feeding_duration_threshold = 30  # saniye
        self.resting_speed_threshold = 5  # pixel/saniye
        self.panic_speed_threshold = 100  # pixel/saniye
        
    def add_zone(self, zone: CoopZone):
        """Bölge ekle."""
        self.zones.append(zone)
        logger.info(f"Added zone: {zone.name} ({zone.zone_type.value})")
    
    def analyze(
        self,
        poultry_id: str,
        position: Tuple[int, int],
        timestamp: datetime
    ) -> Optional[PoultryBehavior]:
        """
        Kanatlı davranışını analiz et.
        
        Args:
            poultry_id: Kanatlı ID
            position: Mevcut konum (x, y)
            timestamp: Zaman damgası
            
        Returns:
            Tespit edilen davranış
        """
        # Konum geçmişini güncelle
        if poultry_id not in self.position_history:
            self.position_history[poultry_id] = []
        
        self.position_history[poultry_id].append((timestamp, position))
        
        # Eski kayıtları temizle (son 5 dakika)
        cutoff = timestamp - timedelta(minutes=5)
        self.position_history[poultry_id] = [
            (t, p) for t, p in self.position_history[poultry_id] if t > cutoff
        ]
        
        # Hangi bölgede?
        current_zone = self._get_zone(position)
        
        # Hız hesapla
        speed = self._calculate_speed(poultry_id)
        
        # Davranış belirle
        behavior = self._determine_behavior(
            poultry_id, current_zone, speed, timestamp
        )
        
        return behavior
    
    def _get_zone(self, position: Tuple[int, int]) -> Optional[CoopZone]:
        """Konumun hangi bölgede olduğunu bul."""
        for zone in self.zones:
            if zone.contains_point(position):
                return zone
        return None
    
    def _calculate_speed(self, poultry_id: str) -> float:
        """Ortalama hız hesapla (pixel/saniye)."""
        history = self.position_history.get(poultry_id, [])
        
        if len(history) < 2:
            return 0.0
        
        # Son 2 saniyedeki hareketler
        recent = history[-10:]  # Son 10 kayıt
        
        if len(recent) < 2:
            return 0.0
        
        total_distance = 0
        for i in range(1, len(recent)):
            t1, p1 = recent[i-1]
            t2, p2 = recent[i]
            
            dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_distance += dist
        
        time_diff = (recent[-1][0] - recent[0][0]).total_seconds()
        
        if time_diff > 0:
            return total_distance / time_diff
        return 0.0
    
    def _determine_behavior(
        self,
        poultry_id: str,
        zone: Optional[CoopZone],
        speed: float,
        timestamp: datetime
    ) -> PoultryBehavior:
        """Davranış belirle."""
        
        # Panik kontrolü (çok hızlı hareket)
        if speed > self.panic_speed_threshold:
            return PoultryBehavior.PANIC
        
        # Koşma
        if speed > 50:
            return PoultryBehavior.RUNNING
        
        # Bölgeye göre davranış
        if zone:
            if zone.zone_type == CoopZoneType.FEEDER:
                return PoultryBehavior.FEEDING
            elif zone.zone_type == CoopZoneType.WATERER:
                return PoultryBehavior.DRINKING
            elif zone.zone_type == CoopZoneType.ROOST:
                return PoultryBehavior.ROOSTING
            elif zone.zone_type == CoopZoneType.NEST_BOX:
                return PoultryBehavior.NESTING
            elif zone.zone_type == CoopZoneType.DUST_BATH:
                return PoultryBehavior.DUST_BATHING
        
        # Hız bazlı davranış
        if speed < self.resting_speed_threshold:
            return PoultryBehavior.RESTING
        elif speed < 20:
            return PoultryBehavior.WALKING
        else:
            return PoultryBehavior.FORAGING
    
    def get_behavior_stats(self, poultry_id: str) -> Dict[str, float]:
        """Davranış istatistikleri."""
        history = self.behavior_history.get(poultry_id, [])
        
        if not history:
            return {}
        
        stats = {}
        total = len(history)
        
        for behavior in PoultryBehavior:
            count = sum(1 for _, b in history if b == behavior)
            if count > 0:
                stats[behavior.value] = round(count / total * 100, 1)
        
        return stats


# ===========================================
# Kanatlı Sağlık İzleme
# ===========================================

class PoultryHealthMonitor:
    """
    Kanatlı sağlık izleme sistemi.
    
    Hastalık belirtileri, stres ve anormal davranış tespiti.
    """
    
    # Hastalık belirtileri
    DISEASE_SYMPTOMS = {
        "respiratory": ["wheezing", "coughing", "nasal_discharge"],
        "digestive": ["diarrhea", "loss_of_appetite", "weight_loss"],
        "neurological": ["tremors", "paralysis", "twisted_neck"],
        "skin": ["lesions", "scabs", "feather_loss"],
    }
    
    def __init__(self):
        self.health_records: Dict[str, List[Dict]] = {}
        self.alerts: List[Dict] = []
        
        # Eşik değerler
        self.isolation_threshold = 60  # saniye (sürüden ayrı kalma)
        self.lethargy_threshold = 120  # saniye (hareketsizlik)
        self.feeding_min_threshold = 300  # saniye (minimum yem yeme)
    
    def check_health(
        self,
        poultry_id: str,
        behavior: PoultryBehavior,
        position: Tuple[int, int],
        flock_center: Optional[Tuple[int, int]] = None
    ) -> PoultryHealthStatus:
        """
        Sağlık durumunu kontrol et.
        
        Args:
            poultry_id: Kanatlı ID
            behavior: Mevcut davranış
            position: Mevcut konum
            flock_center: Sürü merkezi
            
        Returns:
            Sağlık durumu
        """
        alerts = []
        status = PoultryHealthStatus.HEALTHY
        
        # Stres davranışları kontrolü
        if behavior in [
            PoultryBehavior.FEATHER_PECKING,
            PoultryBehavior.CANNIBALISM,
            PoultryBehavior.PILING,
            PoultryBehavior.PANIC
        ]:
            status = PoultryHealthStatus.STRESSED
            alerts.append({
                "type": "stress_behavior",
                "behavior": behavior.value,
                "severity": "warning",
            })
        
        # Durgunluk kontrolü
        if behavior == PoultryBehavior.LETHARGY:
            status = PoultryHealthStatus.SICK
            alerts.append({
                "type": "lethargy",
                "severity": "critical",
            })
        
        # Sürüden izolasyon kontrolü
        if flock_center and behavior == PoultryBehavior.ISOLATION:
            distance = np.sqrt(
                (position[0] - flock_center[0])**2 +
                (position[1] - flock_center[1])**2
            )
            if distance > 200:  # pixel
                status = PoultryHealthStatus.SICK
                alerts.append({
                    "type": "isolation",
                    "distance": distance,
                    "severity": "warning",
                })
        
        # Uyarıları kaydet
        for alert in alerts:
            alert["poultry_id"] = poultry_id
            alert["timestamp"] = datetime.now().isoformat()
            self.alerts.append(alert)
        
        return status
    
    def get_health_report(self, poultry_id: str) -> Dict:
        """Sağlık raporu oluştur."""
        records = self.health_records.get(poultry_id, [])
        
        # Son uyarılar
        recent_alerts = [
            a for a in self.alerts
            if a.get("poultry_id") == poultry_id
        ][-10:]
        
        return {
            "poultry_id": poultry_id,
            "total_records": len(records),
            "recent_alerts": recent_alerts,
            "alert_count": len([a for a in self.alerts if a.get("poultry_id") == poultry_id]),
        }
    
    def get_flock_health_summary(self) -> Dict:
        """Sürü sağlık özeti."""
        total_alerts = len(self.alerts)
        
        # Uyarı tipleri
        alert_types = {}
        for alert in self.alerts:
            alert_type = alert.get("type", "unknown")
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        # Kritik uyarılar
        critical = [a for a in self.alerts if a.get("severity") == "critical"]
        
        return {
            "total_alerts": total_alerts,
            "critical_alerts": len(critical),
            "alert_types": alert_types,
            "last_check": datetime.now().isoformat(),
        }


# ===========================================
# Yumurta Üretim Takibi
# ===========================================

class EggProductionTracker:
    """
    Yumurta üretim takip sistemi.
    
    Yumurtlama kutusu izleme ve üretim istatistikleri.
    """
    
    def __init__(self):
        self.records: List[EggProduction] = []
        self.daily_counts: Dict[str, int] = {}  # date -> count
        self.nest_box_visits: Dict[str, List[Dict]] = {}
        
    def record_egg(
        self,
        nest_box_id: str,
        poultry_id: Optional[str] = None,
        egg_quality: str = "normal"
    ) -> EggProduction:
        """Yumurta kaydı ekle."""
        record = EggProduction(
            record_id=f"egg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            nest_box_id=nest_box_id,
            timestamp=datetime.now(),
            poultry_id=poultry_id,
            egg_quality=egg_quality,
        )
        
        self.records.append(record)
        
        # Günlük sayacı güncelle
        date_key = datetime.now().strftime("%Y-%m-%d")
        self.daily_counts[date_key] = self.daily_counts.get(date_key, 0) + 1
        
        logger.info(f"Egg recorded: {record.record_id} from {nest_box_id}")
        return record
    
    def record_nest_visit(
        self,
        nest_box_id: str,
        poultry_id: str,
        duration_seconds: float
    ):
        """Yumurtlama kutusu ziyareti kaydet."""
        if nest_box_id not in self.nest_box_visits:
            self.nest_box_visits[nest_box_id] = []
        
        self.nest_box_visits[nest_box_id].append({
            "poultry_id": poultry_id,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
        })
    
    def get_daily_production(self, date: Optional[datetime] = None) -> int:
        """Günlük üretim."""
        if date is None:
            date = datetime.now()
        
        date_key = date.strftime("%Y-%m-%d")
        return self.daily_counts.get(date_key, 0)
    
    def get_weekly_production(self) -> Dict[str, int]:
        """Haftalık üretim."""
        result = {}
        today = datetime.now()
        
        for i in range(7):
            date = today - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            result[date_key] = self.daily_counts.get(date_key, 0)
        
        return result
    
    def get_production_stats(self) -> Dict:
        """Üretim istatistikleri."""
        total = len(self.records)
        
        # Kalite dağılımı
        quality_dist = {}
        for record in self.records:
            quality = record.egg_quality
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        # Günlük ortalama
        if self.daily_counts:
            avg_daily = sum(self.daily_counts.values()) / len(self.daily_counts)
        else:
            avg_daily = 0
        
        return {
            "total_eggs": total,
            "daily_average": round(avg_daily, 1),
            "quality_distribution": quality_dist,
            "today": self.get_daily_production(),
            "weekly": self.get_weekly_production(),
        }


# ===========================================
# Ana Kümes Yönetici Sınıfı
# ===========================================

class PoultryCoopManager:
    """
    Kanatlı kümes yönetim sistemi.
    
    Tüm kanatlı takip, davranış analizi ve sağlık izleme
    işlemlerini koordine eder.
    
    Kullanım:
        manager = PoultryCoopManager()
        manager.add_zone(CoopZone(...))
        
        # Tespit işle
        result = manager.process_detection(detection)
    """
    
    def __init__(self, coop_name: str = "Kümes 1"):
        self.coop_name = coop_name
        self.behavior_analyzer = PoultryBehaviorAnalyzer()
        self.health_monitor = PoultryHealthMonitor()
        self.egg_tracker = EggProductionTracker()
        
        # Kanatlı kayıtları
        self.poultry_registry: Dict[str, Dict] = {}
        self.detection_history: List[PoultryDetection] = []
        
        # İstatistikler
        self.stats = {
            "total_detections": 0,
            "unique_poultry": 0,
            "active_count": 0,
        }
        
        logger.info(f"PoultryCoopManager initialized: {coop_name}")
    
    def add_zone(
        self,
        zone_id: str,
        zone_type: CoopZoneType,
        name: str,
        bbox: Tuple[int, int, int, int],
        capacity: int = 0
    ):
        """Bölge ekle."""
        zone = CoopZone(
            zone_id=zone_id,
            zone_type=zone_type,
            name=name,
            bbox=bbox,
            capacity=capacity,
        )
        self.behavior_analyzer.add_zone(zone)
    
    def register_poultry(
        self,
        poultry_id: str,
        poultry_type: PoultryType,
        **kwargs
    ):
        """Kanatlı kaydet."""
        self.poultry_registry[poultry_id] = {
            "poultry_id": poultry_id,
            "poultry_type": poultry_type.value,
            "registered_at": datetime.now().isoformat(),
            **kwargs
        }
        self.stats["unique_poultry"] = len(self.poultry_registry)
        logger.info(f"Registered poultry: {poultry_id} ({poultry_type.value})")
    
    def process_detection(
        self,
        poultry_id: str,
        poultry_type: PoultryType,
        confidence: float,
        bbox: Tuple[int, int, int, int],
        timestamp: Optional[datetime] = None
    ) -> PoultryDetection:
        """
        Tespit işle.
        
        Args:
            poultry_id: Kanatlı ID
            poultry_type: Tür
            confidence: Güven skoru
            bbox: Bounding box
            timestamp: Zaman damgası
            
        Returns:
            İşlenmiş tespit
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Merkez hesapla
        x1, y1, x2, y2 = bbox
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        
        # Davranış analizi
        behavior = self.behavior_analyzer.analyze(poultry_id, center, timestamp)
        
        # Bölge tespiti
        current_zone = None
        for zone in self.behavior_analyzer.zones:
            if zone.contains_point(center):
                current_zone = zone.zone_type
                break
        
        # Sağlık kontrolü
        flock_center = self._calculate_flock_center()
        health_status = self.health_monitor.check_health(
            poultry_id, behavior, center, flock_center
        )
        
        # Tespit oluştur
        detection = PoultryDetection(
            poultry_id=poultry_id,
            poultry_type=poultry_type,
            confidence=confidence,
            bbox=bbox,
            center=center,
            timestamp=timestamp,
            health_status=health_status,
            current_zone=current_zone,
            behavior=behavior,
        )
        
        # Kaydet
        self.detection_history.append(detection)
        self.stats["total_detections"] += 1
        
        # Yumurtlama kutusu ziyareti kontrolü
        if current_zone == CoopZoneType.NEST_BOX:
            self._check_nesting(poultry_id, timestamp)
        
        return detection
    
    def _calculate_flock_center(self) -> Optional[Tuple[int, int]]:
        """Sürü merkezini hesapla."""
        recent = self.detection_history[-50:]  # Son 50 tespit
        
        if not recent:
            return None
        
        avg_x = sum(d.center[0] for d in recent) / len(recent)
        avg_y = sum(d.center[1] for d in recent) / len(recent)
        
        return (int(avg_x), int(avg_y))
    
    def _check_nesting(self, poultry_id: str, timestamp: datetime):
        """Yumurtlama kontrolü."""
        # Basit mantık: Uzun süre nest box'ta kalma = yumurtlama
        # Gerçek uygulamada sensör veya görüntü analizi kullanılabilir
        pass
    
    def get_active_count(self) -> int:
        """Aktif kanatlı sayısı."""
        # Son 5 dakikadaki benzersiz ID'ler
        cutoff = datetime.now() - timedelta(minutes=5)
        recent = [d for d in self.detection_history if d.timestamp > cutoff]
        
        unique_ids = set(d.poultry_id for d in recent)
        self.stats["active_count"] = len(unique_ids)
        
        return len(unique_ids)
    
    def get_zone_occupancy(self) -> Dict[str, int]:
        """Bölge doluluk durumu."""
        # Son tespitlerden bölge sayıları
        cutoff = datetime.now() - timedelta(seconds=30)
        recent = [d for d in self.detection_history if d.timestamp > cutoff]
        
        occupancy = {}
        for zone in self.behavior_analyzer.zones:
            count = sum(
                1 for d in recent
                if d.current_zone == zone.zone_type
            )
            occupancy[zone.zone_id] = count
        
        return occupancy
    
    def get_summary(self) -> Dict:
        """Özet bilgiler."""
        return {
            "coop_name": self.coop_name,
            "total_registered": len(self.poultry_registry),
            "active_count": self.get_active_count(),
            "total_detections": self.stats["total_detections"],
            "zone_occupancy": self.get_zone_occupancy(),
            "egg_production": self.egg_tracker.get_production_stats(),
            "health_summary": self.health_monitor.get_flock_health_summary(),
            "zones": [z.to_dict() for z in self.behavior_analyzer.zones],
        }


# ===========================================
# Export
# ===========================================

__all__ = [
    # Enums
    "PoultryType",
    "PoultryBehavior",
    "PoultryHealthStatus",
    "CoopZoneType",
    
    # Data classes
    "PoultryDetection",
    "EggProduction",
    "CoopZone",
    
    # Managers
    "PoultryBehaviorAnalyzer",
    "PoultryHealthMonitor",
    "EggProductionTracker",
    "PoultryCoopManager",
    
    # Constants
    "POULTRY_NAMES_TR",
    "BEHAVIOR_NAMES_TR",
    "ZONE_NAMES_TR",
]
