"""
Uyarı Kuralları Yönetimi
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid


logger = logging.getLogger(__name__)


class RuleCondition(Enum):
    """Kural koşulları"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CHANGED = "changed"


class RuleAction(Enum):
    """Kural aksiyonları"""
    SEND_NOTIFICATION = "send_notification"
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    TRIGGER_WEBHOOK = "trigger_webhook"
    LOG_EVENT = "log_event"
    CUSTOM = "custom"


@dataclass
class AlertCondition:
    """Uyarı koşulu"""
    field: str
    condition: RuleCondition
    value: Any
    value2: Any = None  # BETWEEN için ikinci değer
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Koşulu değerlendir"""
        actual_value = self._get_nested_value(data, self.field)
        
        if actual_value is None:
            return False
            
        if self.condition == RuleCondition.EQUALS:
            return actual_value == self.value
        elif self.condition == RuleCondition.NOT_EQUALS:
            return actual_value != self.value
        elif self.condition == RuleCondition.GREATER_THAN:
            return actual_value > self.value
        elif self.condition == RuleCondition.LESS_THAN:
            return actual_value < self.value
        elif self.condition == RuleCondition.GREATER_EQUAL:
            return actual_value >= self.value
        elif self.condition == RuleCondition.LESS_EQUAL:
            return actual_value <= self.value
        elif self.condition == RuleCondition.CONTAINS:
            return self.value in actual_value
        elif self.condition == RuleCondition.NOT_CONTAINS:
            return self.value not in actual_value
        elif self.condition == RuleCondition.IN:
            return actual_value in self.value
        elif self.condition == RuleCondition.NOT_IN:
            return actual_value not in self.value
        elif self.condition == RuleCondition.BETWEEN:
            return self.value <= actual_value <= self.value2
            
        return False
        
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """İç içe değer al (path: 'a.b.c')"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


@dataclass
class AlertRule:
    """Uyarı kuralı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    conditions: List[AlertCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    severity: str = "info"
    enabled: bool = True
    cooldown_minutes: int = 5  # Aynı kural için minimum bekleme süresi
    max_triggers_per_hour: int = 10
    notification_template: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Çalışma zamanı bilgileri
    _last_triggered: datetime = None
    _trigger_count_hour: int = 0
    _hour_start: datetime = None
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Kuralı değerlendir"""
        if not self.enabled:
            return False
            
        # Rate limit kontrolü
        if not self._check_rate_limit():
            return False
            
        # Tüm koşulları kontrol et (AND)
        return all(cond.evaluate(data) for cond in self.conditions)
        
    def _check_rate_limit(self) -> bool:
        """Rate limit kontrolü"""
        now = datetime.utcnow()
        
        # Cooldown kontrolü
        if self._last_triggered:
            elapsed = (now - self._last_triggered).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                return False
                
        # Saatlik limit kontrolü
        if self._hour_start and (now - self._hour_start).total_seconds() < 3600:
            if self._trigger_count_hour >= self.max_triggers_per_hour:
                return False
        else:
            self._hour_start = now
            self._trigger_count_hour = 0
            
        return True
        
    def trigger(self):
        """Kuralı tetikle"""
        self._last_triggered = datetime.utcnow()
        self._trigger_count_hour += 1
        
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'conditions': [
                {
                    'field': c.field,
                    'condition': c.condition.value,
                    'value': c.value,
                    'value2': c.value2
                }
                for c in self.conditions
            ],
            'actions': [a.value for a in self.actions],
            'severity': self.severity,
            'enabled': self.enabled,
            'cooldown_minutes': self.cooldown_minutes,
            'max_triggers_per_hour': self.max_triggers_per_hour,
            'notification_template': self.notification_template,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class AlertRulesEngine:
    """Uyarı kuralları motoru"""
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._action_handlers: Dict[RuleAction, Callable] = {}
        self._triggered_events: List[Dict] = []
        
    def add_rule(self, rule: AlertRule) -> str:
        """Kural ekle"""
        self._rules[rule.id] = rule
        logger.info(f"Kural eklendi: {rule.name} ({rule.id})")
        return rule.id
        
    def remove_rule(self, rule_id: str) -> bool:
        """Kural sil"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"Kural silindi: {rule_id}")
            return True
        return False
        
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Kural getir"""
        return self._rules.get(rule_id)
        
    def get_all_rules(self) -> List[AlertRule]:
        """Tüm kuralları getir"""
        return list(self._rules.values())
        
    def enable_rule(self, rule_id: str) -> bool:
        """Kuralı aktifleştir"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False
        
    def disable_rule(self, rule_id: str) -> bool:
        """Kuralı devre dışı bırak"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False
        
    def register_action_handler(self, action: RuleAction, handler: Callable):
        """Aksiyon işleyici kaydet"""
        self._action_handlers[action] = handler
        
    def evaluate(self, data: Dict[str, Any]) -> List[AlertRule]:
        """Veriyi tüm kurallara göre değerlendir"""
        triggered_rules = []
        
        for rule in self._rules.values():
            if rule.evaluate(data):
                triggered_rules.append(rule)
                rule.trigger()
                
                # Olayı kaydet
                self._triggered_events.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_sample': {k: v for k, v in list(data.items())[:5]}
                })
                
                # Aksiyonları çalıştır
                self._execute_actions(rule, data)
                
        return triggered_rules
        
    def _execute_actions(self, rule: AlertRule, data: Dict[str, Any]):
        """Aksiyonları çalıştır"""
        for action in rule.actions:
            handler = self._action_handlers.get(action)
            if handler:
                try:
                    handler(rule, data)
                except Exception as e:
                    logger.error(f"Aksiyon hatası ({action.value}): {e}")
            else:
                logger.warning(f"Aksiyon işleyici bulunamadı: {action.value}")
                
    def get_triggered_events(self, limit: int = 100) -> List[Dict]:
        """Tetiklenen olayları getir"""
        return self._triggered_events[-limit:]
        
    def clear_events(self):
        """Olayları temizle"""
        self._triggered_events.clear()


# Önceden tanımlı kurallar
def create_default_rules() -> List[AlertRule]:
    """Varsayılan kuralları oluştur"""
    rules = []
    
    # Düşük sağlık skoru uyarısı
    rules.append(AlertRule(
        name="Düşük Sağlık Skoru",
        description="Hayvan sağlık skoru 50'nin altına düştüğünde uyarı ver",
        conditions=[
            AlertCondition(
                field="health_score",
                condition=RuleCondition.LESS_THAN,
                value=50
            )
        ],
        actions=[RuleAction.SEND_NOTIFICATION, RuleAction.SEND_EMAIL],
        severity="warning",
        cooldown_minutes=60
    ))
    
    # Kritik sağlık durumu
    rules.append(AlertRule(
        name="Kritik Sağlık Durumu",
        description="Hayvan sağlık skoru 30'un altına düştüğünde acil uyarı",
        conditions=[
            AlertCondition(
                field="health_score",
                condition=RuleCondition.LESS_THAN,
                value=30
            )
        ],
        actions=[RuleAction.SEND_NOTIFICATION, RuleAction.SEND_EMAIL, RuleAction.SEND_SMS],
        severity="critical",
        cooldown_minutes=30
    ))
    
    # Uzun süreli hareketsizlik
    rules.append(AlertRule(
        name="Uzun Süreli Hareketsizlik",
        description="Hayvan 2 saatten fazla hareketsiz kaldığında uyarı",
        conditions=[
            AlertCondition(
                field="inactive_minutes",
                condition=RuleCondition.GREATER_THAN,
                value=120
            )
        ],
        actions=[RuleAction.SEND_NOTIFICATION],
        severity="warning",
        cooldown_minutes=120
    ))
    
    # Anormal davranış
    rules.append(AlertRule(
        name="Anormal Davranış",
        description="Anormal davranış tespit edildiğinde uyarı",
        conditions=[
            AlertCondition(
                field="behavior.is_abnormal",
                condition=RuleCondition.EQUALS,
                value=True
            )
        ],
        actions=[RuleAction.SEND_NOTIFICATION, RuleAction.LOG_EVENT],
        severity="warning",
        cooldown_minutes=15
    ))
    
    # Topallama tespiti
    rules.append(AlertRule(
        name="Topallama Tespiti",
        description="Topallama skoru yüksek olduğunda uyarı",
        conditions=[
            AlertCondition(
                field="lameness_score",
                condition=RuleCondition.GREATER_THAN,
                value=2
            )
        ],
        actions=[RuleAction.SEND_NOTIFICATION, RuleAction.SEND_EMAIL],
        severity="warning",
        cooldown_minutes=180
    ))
    
    return rules


# Singleton instance
alert_rules_engine = AlertRulesEngine()


# Varsayılan kuralları yükle
def initialize_default_rules():
    """Varsayılan kuralları yükle"""
    for rule in create_default_rules():
        alert_rules_engine.add_rule(rule)
    logger.info(f"Varsayılan kurallar yüklendi: {len(alert_rules_engine.get_all_rules())} kural")
