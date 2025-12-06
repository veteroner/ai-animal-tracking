"""
Erken Uyarı Sistemi

Sağlık sorunları için erken uyarı ve risk değerlendirmesi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import numpy as np
from collections import defaultdict


class AlertPriority(Enum):
    """Uyarı önceliği"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AlertCategory(Enum):
    """Uyarı kategorisi"""
    HEALTH = "health"
    BEHAVIOR = "behavior"
    FEEDING = "feeding"
    ENVIRONMENT = "environment"
    REPRODUCTION = "reproduction"


class AlertStatus(Enum):
    """Uyarı durumu"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class RiskScore:
    """Risk skoru"""
    animal_id: str
    timestamp: datetime
    overall_score: float          # 0-100
    health_score: float           # 0-100
    behavior_score: float         # 0-100
    feeding_score: float          # 0-100
    factors: Dict[str, float] = field(default_factory=dict)
    
    @property
    def risk_level(self) -> str:
        if self.overall_score < 25:
            return "low"
        elif self.overall_score < 50:
            return "moderate"
        elif self.overall_score < 75:
            return "high"
        else:
            return "critical"
    
    def to_dict(self) -> Dict:
        return {
            "animal_id": self.animal_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": round(self.overall_score, 1),
            "health_score": round(self.health_score, 1),
            "behavior_score": round(self.behavior_score, 1),
            "feeding_score": round(self.feeding_score, 1),
            "risk_level": self.risk_level,
            "factors": {k: round(v, 2) for k, v in self.factors.items()}
        }


@dataclass
class Alert:
    """Uyarı"""
    alert_id: str
    animal_id: str
    timestamp: datetime
    priority: AlertPriority
    category: AlertCategory
    title: str
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    risk_score: Optional[float] = None
    data: Dict = field(default_factory=dict)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "animal_id": self.animal_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "priority_label": self.priority.name.lower(),
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "status": self.status.value,
            "risk_score": round(self.risk_score, 1) if self.risk_score else None,
            "data": self.data
        }


@dataclass
class AlertRule:
    """Uyarı kuralı"""
    rule_id: str
    name: str
    category: AlertCategory
    condition: Callable[[Dict], bool]
    priority: AlertPriority
    title_template: str
    message_template: str
    cooldown_minutes: int = 60
    enabled: bool = True


class EarlyWarningSystem:
    """Erken uyarı sistemi"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Uyarılar
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Risk skorları
        self.risk_scores: Dict[str, RiskScore] = {}
        
        # Kurallar
        self.rules: Dict[str, AlertRule] = {}
        self._setup_default_rules()
        
        # Son uyarı zamanları (cooldown için)
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Sayaç
        self._alert_counter = 0
    
    def _generate_alert_id(self) -> str:
        self._alert_counter += 1
        return f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._alert_counter}"
    
    def _setup_default_rules(self):
        """Varsayılan kuralları oluştur"""
        # Düşük aktivite uyarısı
        self.add_rule(AlertRule(
            rule_id="low_activity",
            name="Düşük Aktivite",
            category=AlertCategory.BEHAVIOR,
            condition=lambda d: d.get("activity_level", 100) < 30,
            priority=AlertPriority.MEDIUM,
            title_template="Düşük Aktivite Tespit Edildi",
            message_template="Hayvan {animal_id} son 24 saatte normalin %{activity_level} altında aktivite gösterdi."
        ))
        
        # Yeme azalması uyarısı
        self.add_rule(AlertRule(
            rule_id="reduced_feeding",
            name="Yeme Azalması",
            category=AlertCategory.FEEDING,
            condition=lambda d: d.get("feeding_reduction", 0) > 40,
            priority=AlertPriority.HIGH,
            title_template="Yeme Miktarında Azalma",
            message_template="Hayvan {animal_id} yem tüketiminde %{feeding_reduction} azalma tespit edildi."
        ))
        
        # İzolasyon uyarısı
        self.add_rule(AlertRule(
            rule_id="isolation",
            name="İzolasyon Davranışı",
            category=AlertCategory.BEHAVIOR,
            condition=lambda d: d.get("isolation_score", 0) > 70,
            priority=AlertPriority.HIGH,
            title_template="İzolasyon Davranışı",
            message_template="Hayvan {animal_id} sürüden izole davranış sergiliyor."
        ))
        
        # Yüksek sıcaklık stresi
        self.add_rule(AlertRule(
            rule_id="heat_stress",
            name="Isı Stresi",
            category=AlertCategory.ENVIRONMENT,
            condition=lambda d: d.get("heat_stress_level", 0) >= 3,
            priority=AlertPriority.CRITICAL,
            title_template="Şiddetli Isı Stresi",
            message_template="Hayvan {animal_id} şiddetli ısı stresi altında. THI: {thi}"
        ))
        
        # Topallama uyarısı
        self.add_rule(AlertRule(
            rule_id="lameness",
            name="Topallama",
            category=AlertCategory.HEALTH,
            condition=lambda d: d.get("lameness_score", 1) >= 3,
            priority=AlertPriority.HIGH,
            title_template="Topallama Tespit Edildi",
            message_template="Hayvan {animal_id} topallama belirtileri gösteriyor. Skor: {lameness_score}/5"
        ))
        
        # BCS düşüşü
        self.add_rule(AlertRule(
            rule_id="bcs_decline",
            name="BCS Düşüşü",
            category=AlertCategory.HEALTH,
            condition=lambda d: d.get("bcs_change", 0) < -0.5,
            priority=AlertPriority.MEDIUM,
            title_template="Vücut Kondisyonu Düşüşü",
            message_template="Hayvan {animal_id} BCS'de {bcs_change} puan düşüş tespit edildi."
        ))
    
    def add_rule(self, rule: AlertRule):
        """Kural ekle"""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str):
        """Kural kaldır"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def calculate_risk_score(self, animal_id: str, data: Dict) -> RiskScore:
        """Risk skoru hesapla"""
        # Sağlık faktörleri
        health_factors = {
            "lameness": data.get("lameness_score", 1) / 5 * 100,
            "bcs_deviation": abs(data.get("bcs", 3) - 3) / 2 * 100,
            "respiratory_rate": max(0, (data.get("respiratory_rate", 20) - 30) / 20 * 100),
            "anomaly_score": data.get("anomaly_score", 0)
        }
        health_score = np.mean(list(health_factors.values()))
        
        # Davranış faktörleri
        behavior_factors = {
            "activity_reduction": 100 - data.get("activity_level", 100),
            "isolation": data.get("isolation_score", 0),
            "restlessness": data.get("restlessness_score", 0)
        }
        behavior_score = np.mean(list(behavior_factors.values()))
        
        # Beslenme faktörleri
        feeding_factors = {
            "feeding_reduction": data.get("feeding_reduction", 0),
            "water_reduction": data.get("water_reduction", 0),
            "feeding_time_change": abs(data.get("feeding_time_change", 0))
        }
        feeding_score = np.mean(list(feeding_factors.values()))
        
        # Genel skor (ağırlıklı ortalama)
        overall_score = (
            health_score * 0.4 +
            behavior_score * 0.35 +
            feeding_score * 0.25
        )
        
        # Tüm faktörleri birleştir
        all_factors = {}
        all_factors.update({f"health_{k}": v for k, v in health_factors.items()})
        all_factors.update({f"behavior_{k}": v for k, v in behavior_factors.items()})
        all_factors.update({f"feeding_{k}": v for k, v in feeding_factors.items()})
        
        risk_score = RiskScore(
            animal_id=animal_id,
            timestamp=datetime.now(),
            overall_score=overall_score,
            health_score=health_score,
            behavior_score=behavior_score,
            feeding_score=feeding_score,
            factors=all_factors
        )
        
        self.risk_scores[animal_id] = risk_score
        return risk_score
    
    def evaluate_rules(self, animal_id: str, data: Dict) -> List[Alert]:
        """Kuralları değerlendir ve uyarı oluştur"""
        alerts = []
        data["animal_id"] = animal_id
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Cooldown kontrolü
            cooldown_key = f"{animal_id}_{rule_id}"
            if cooldown_key in self.last_alert_times:
                elapsed = (datetime.now() - self.last_alert_times[cooldown_key]).total_seconds() / 60
                if elapsed < rule.cooldown_minutes:
                    continue
            
            # Kural koşulunu kontrol et
            try:
                if rule.condition(data):
                    alert = self._create_alert_from_rule(rule, animal_id, data)
                    alerts.append(alert)
                    self.last_alert_times[cooldown_key] = datetime.now()
            except Exception:
                pass
        
        return alerts
    
    def _create_alert_from_rule(self, rule: AlertRule, animal_id: str, data: Dict) -> Alert:
        """Kuraldan uyarı oluştur"""
        title = rule.title_template.format(**data)
        message = rule.message_template.format(**data)
        
        alert = Alert(
            alert_id=self._generate_alert_id(),
            animal_id=animal_id,
            timestamp=datetime.now(),
            priority=rule.priority,
            category=rule.category,
            title=title,
            message=message,
            risk_score=self.risk_scores.get(animal_id, RiskScore(animal_id, datetime.now(), 0, 0, 0, 0)).overall_score,
            data=data.copy()
        )
        
        self.alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        return alert
    
    def create_alert(self, animal_id: str, priority: AlertPriority,
                    category: AlertCategory, title: str, message: str,
                    data: Optional[Dict] = None) -> Alert:
        """Manuel uyarı oluştur"""
        alert = Alert(
            alert_id=self._generate_alert_id(),
            animal_id=animal_id,
            timestamp=datetime.now(),
            priority=priority,
            category=category,
            title=title,
            message=message,
            data=data or {}
        )
        
        self.alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Uyarıyı onayla"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            self.alerts[alert_id].acknowledged_at = datetime.now()
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Uyarıyı çöz"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.RESOLVED
            self.alerts[alert_id].resolved_at = datetime.now()
            return True
        return False
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Uyarıyı reddet"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.DISMISSED
            return True
        return False
    
    def get_active_alerts(self, animal_id: Optional[str] = None,
                         priority: Optional[AlertPriority] = None,
                         category: Optional[AlertCategory] = None) -> List[Alert]:
        """Aktif uyarıları al"""
        alerts = [a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]
        
        if animal_id:
            alerts = [a for a in alerts if a.animal_id == animal_id]
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        return sorted(alerts, key=lambda x: (x.priority.value, x.timestamp), reverse=True)
    
    def get_high_risk_animals(self, threshold: float = 50) -> List[Dict]:
        """Yüksek riskli hayvanları al"""
        high_risk = []
        
        for animal_id, risk in self.risk_scores.items():
            if risk.overall_score >= threshold:
                active_alerts = len([a for a in self.alerts.values() 
                                   if a.animal_id == animal_id and a.status == AlertStatus.ACTIVE])
                high_risk.append({
                    "animal_id": animal_id,
                    "risk_score": round(risk.overall_score, 1),
                    "risk_level": risk.risk_level,
                    "active_alerts": active_alerts,
                    "top_factors": dict(sorted(risk.factors.items(), key=lambda x: x[1], reverse=True)[:3])
                })
        
        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)
    
    def get_alert_summary(self) -> Dict:
        """Uyarı özeti"""
        active = [a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]
        
        priority_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for alert in active:
            priority_counts[alert.priority.name] += 1
            category_counts[alert.category.value] += 1
        
        return {
            "total_active": len(active),
            "by_priority": dict(priority_counts),
            "by_category": dict(category_counts),
            "critical_count": priority_counts.get("CRITICAL", 0),
            "high_count": priority_counts.get("HIGH", 0),
            "animals_with_alerts": len(set(a.animal_id for a in active)),
            "oldest_alert": min((a.timestamp for a in active), default=None)
        }
