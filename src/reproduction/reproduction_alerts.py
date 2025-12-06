"""
Üreme Uyarı Yönetim Modülü
==========================
Üreme ile ilgili tüm uyarıları yönetir.

Uyarı Tipleri:
- 🔴 Kritik: Doğum başladı, güç doğum riski
- 🟠 Yüksek: Doğum 24 saat içinde
- 🟡 Orta: Kızgınlık tespit edildi
- 🟢 Normal: Optimal tohumlama zamanı
- 🔵 Bilgi: Gebelik kontrol hatırlatması
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class AlertSeverity(Enum):
    """Uyarı önceliği"""
    INFO = "bilgi"
    LOW = "düşük"
    MEDIUM = "orta"
    HIGH = "yüksek"
    CRITICAL = "kritik"


class AlertType(Enum):
    """Uyarı tipi"""
    ESTRUS_DETECTED = "kızgınlık_tespiti"
    OPTIMAL_BREEDING = "optimal_tohumlama"
    PREGNANCY_CHECK = "gebelik_kontrolü"
    BIRTH_SOON = "doğum_yakın"
    BIRTH_IMMINENT = "doğum_başlıyor"
    BIRTH_STARTED = "doğum_başladı"
    DYSTOCIA_RISK = "güç_doğum_riski"
    BIRTH_COMPLETED = "doğum_tamamlandı"
    REPEAT_HEAT = "tekrar_kızgınlık"
    OVERDUE = "gecikmeli_doğum"


class NotificationChannel(Enum):
    """Bildirim kanalı"""
    APP = "uygulama"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    ALARM = "alarm"


@dataclass
class ReproductionAlert:
    """Üreme uyarısı veri yapısı"""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    animal_id: str
    title: str
    message: str
    data: Dict = field(default_factory=dict)
    channels: List[NotificationChannel] = field(default_factory=list)
    is_read: bool = False
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# Uyarı konfigürasyonu
ALERT_CONFIG = {
    AlertType.BIRTH_STARTED: {
        'severity': AlertSeverity.CRITICAL,
        'channels': [NotificationChannel.SMS, NotificationChannel.APP, NotificationChannel.ALARM],
        'title_template': '🔴 DOĞUM BAŞLADI: {animal_id}',
        'message_template': '{animal_name} doğum sürecine girdi. Hemen kontrol edin!',
        'expiry_hours': 6
    },
    AlertType.DYSTOCIA_RISK: {
        'severity': AlertSeverity.CRITICAL,
        'channels': [NotificationChannel.SMS, NotificationChannel.APP, NotificationChannel.ALARM],
        'title_template': '⚠️ GÜÇ DOĞUM RİSKİ: {animal_id}',
        'message_template': '{animal_name} için güç doğum riski tespit edildi. Veteriner müdahalesi gerekebilir!',
        'expiry_hours': 2
    },
    AlertType.BIRTH_IMMINENT: {
        'severity': AlertSeverity.HIGH,
        'channels': [NotificationChannel.SMS, NotificationChannel.APP],
        'title_template': '🟠 DOĞUM 6 SAAT İÇİNDE: {animal_id}',
        'message_template': '{animal_name} için doğum belirtileri güçlendi. Tahmini 6 saat içinde.',
        'expiry_hours': 8
    },
    AlertType.BIRTH_SOON: {
        'severity': AlertSeverity.HIGH,
        'channels': [NotificationChannel.APP, NotificationChannel.PUSH],
        'title_template': '🟠 DOĞUM 24 SAAT İÇİNDE: {animal_id}',
        'message_template': '{animal_name} için doğum öncesi davranışlar tespit edildi.',
        'expiry_hours': 30
    },
    AlertType.ESTRUS_DETECTED: {
        'severity': AlertSeverity.MEDIUM,
        'channels': [NotificationChannel.APP, NotificationChannel.PUSH],
        'title_template': '🟡 KIZGINLIK TESPİTİ: {animal_id}',
        'message_template': '{animal_name} kızgınlık belirtileri gösteriyor. Güven: {confidence}%',
        'expiry_hours': 24
    },
    AlertType.OPTIMAL_BREEDING: {
        'severity': AlertSeverity.MEDIUM,
        'channels': [NotificationChannel.APP],
        'title_template': '🟢 OPTİMAL TOHUMLAMA: {animal_id}',
        'message_template': '{animal_name} için optimal tohumlama penceresi: {start_time} - {end_time}',
        'expiry_hours': 12
    },
    AlertType.PREGNANCY_CHECK: {
        'severity': AlertSeverity.INFO,
        'channels': [NotificationChannel.APP],
        'title_template': '🔵 GEBELİK KONTROLÜ: {animal_id}',
        'message_template': '{animal_name} için gebelik kontrolü zamanı. Çiftleşme: {breeding_date}',
        'expiry_hours': 72
    },
    AlertType.REPEAT_HEAT: {
        'severity': AlertSeverity.INFO,
        'channels': [NotificationChannel.APP],
        'title_template': '🔵 TEKRAR KIZGINLIK BEKLENİYOR: {animal_id}',
        'message_template': '{animal_name} için tekrar kızgınlık bekleniyor. Tarih: {expected_date}',
        'expiry_hours': 48
    },
    AlertType.OVERDUE: {
        'severity': AlertSeverity.HIGH,
        'channels': [NotificationChannel.APP, NotificationChannel.SMS],
        'title_template': '🟠 GECİKMELİ DOĞUM: {animal_id}',
        'message_template': '{animal_name} beklenen doğum tarihini {days} gün geçti.',
        'expiry_hours': 48
    },
    AlertType.BIRTH_COMPLETED: {
        'severity': AlertSeverity.INFO,
        'channels': [NotificationChannel.APP],
        'title_template': '✅ DOĞUM TAMAMLANDI: {animal_id}',
        'message_template': '{animal_name} başarıyla doğum yaptı. Yavru sayısı: {offspring_count}',
        'expiry_hours': 24
    }
}


class ReproductionAlertManager:
    """
    Üreme Uyarı Yönetim Sınıfı
    
    Tüm üreme uyarılarını oluşturur, yönetir ve bildirir.
    """
    
    def __init__(self):
        self.alerts: Dict[str, ReproductionAlert] = {}
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        self.animal_names: Dict[str, str] = {}  # ID -> İsim mapping
        
    def register_notification_handler(
        self,
        channel: NotificationChannel,
        handler: Callable
    ):
        """
        Bildirim kanalı için handler kaydeder.
        
        Handler imzası: async def handler(alert: ReproductionAlert) -> bool
        """
        self.notification_handlers[channel] = handler
    
    def set_animal_name(self, animal_id: str, name: str):
        """Hayvan ismi kaydeder (mesajlarda kullanılır)."""
        self.animal_names[animal_id] = name
    
    def create_alert(
        self,
        alert_type: AlertType,
        animal_id: str,
        data: Optional[Dict] = None,
        custom_message: Optional[str] = None
    ) -> ReproductionAlert:
        """
        Yeni uyarı oluşturur.
        
        Args:
            alert_type: Uyarı tipi
            animal_id: Hayvan kimliği
            data: Ek veri (şablon değişkenleri için)
            custom_message: Özel mesaj (şablon yerine)
            
        Returns:
            Oluşturulan uyarı
        """
        config = ALERT_CONFIG.get(alert_type, {})
        
        # Şablon değişkenlerini hazırla
        template_vars = {
            'animal_id': animal_id,
            'animal_name': self.animal_names.get(animal_id, animal_id),
            **(data or {})
        }
        
        # Başlık ve mesajı oluştur
        title = config.get('title_template', '{alert_type}').format(**template_vars)
        message = custom_message or config.get('message_template', '').format(**template_vars)
        
        # Expiry hesapla
        expiry_hours = config.get('expiry_hours', 24)
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        alert = ReproductionAlert(
            id=f"alert-{alert_type.value}-{uuid.uuid4().hex[:8]}",
            alert_type=alert_type,
            severity=config.get('severity', AlertSeverity.INFO),
            animal_id=animal_id,
            title=title,
            message=message,
            data=data or {},
            channels=config.get('channels', [NotificationChannel.APP]),
            expires_at=expires_at
        )
        
        self.alerts[alert.id] = alert
        return alert
    
    async def send_alert(self, alert: ReproductionAlert) -> Dict[str, bool]:
        """
        Uyarıyı tüm kanallara gönderir.
        
        Returns:
            Kanal bazında gönderim sonuçları
        """
        results = {}
        
        for channel in alert.channels:
            handler = self.notification_handlers.get(channel)
            
            if handler:
                try:
                    success = await handler(alert)
                    results[channel.value] = success
                except Exception as e:
                    print(f"Bildirim hatası ({channel.value}): {e}")
                    results[channel.value] = False
            else:
                # Handler yoksa sadece logla
                print(f"[{channel.value}] {alert.title}: {alert.message}")
                results[channel.value] = True
        
        return results
    
    def create_and_send_alert(
        self,
        alert_type: AlertType,
        animal_id: str,
        data: Optional[Dict] = None
    ) -> ReproductionAlert:
        """
        Uyarı oluşturur ve gönderir (senkron wrapper).
        """
        alert = self.create_alert(alert_type, animal_id, data)
        
        # Async gönderim için event loop kullan
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_alert(alert))
            else:
                loop.run_until_complete(self.send_alert(alert))
        except RuntimeError:
            # Event loop yoksa direkt çalıştır
            asyncio.run(self.send_alert(alert))
        
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: str,
        user: str = "system"
    ) -> bool:
        """
        Uyarıyı onaylar (acknowledged).
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.is_acknowledged = True
        alert.acknowledged_by = user
        alert.acknowledged_at = datetime.now()
        
        return True
    
    def mark_as_read(self, alert_id: str) -> bool:
        """Uyarıyı okundu olarak işaretler."""
        if alert_id not in self.alerts:
            return False
        
        self.alerts[alert_id].is_read = True
        return True
    
    def get_unread_alerts(self, animal_id: Optional[str] = None) -> List[ReproductionAlert]:
        """
        Okunmamış uyarıları döndürür.
        """
        now = datetime.now()
        alerts = [
            a for a in self.alerts.values()
            if not a.is_read
            and (a.expires_at is None or a.expires_at > now)
            and (animal_id is None or a.animal_id == animal_id)
        ]
        
        # Önceliğe göre sırala
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        
        alerts.sort(key=lambda a: (severity_order[a.severity], a.created_at))
        return alerts
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None
    ) -> List[ReproductionAlert]:
        """
        Aktif (süresi dolmamış) uyarıları döndürür.
        """
        now = datetime.now()
        
        alerts = [
            a for a in self.alerts.values()
            if (a.expires_at is None or a.expires_at > now)
            and (severity is None or a.severity == severity)
            and (alert_type is None or a.alert_type == alert_type)
        ]
        
        return alerts
    
    def get_critical_alerts(self) -> List[ReproductionAlert]:
        """
        Kritik uyarıları döndürür.
        """
        return self.get_active_alerts(severity=AlertSeverity.CRITICAL)
    
    def cleanup_expired(self) -> int:
        """
        Süresi dolmuş uyarıları temizler.
        
        Returns:
            Silinen uyarı sayısı
        """
        now = datetime.now()
        expired_ids = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.expires_at and alert.expires_at < now
        ]
        
        for alert_id in expired_ids:
            del self.alerts[alert_id]
        
        return len(expired_ids)
    
    def get_alert_statistics(self) -> Dict:
        """
        Uyarı istatistiklerini döndürür.
        """
        all_alerts = list(self.alerts.values())
        now = datetime.now()
        
        active = [a for a in all_alerts if a.expires_at is None or a.expires_at > now]
        
        by_severity = {}
        for severity in AlertSeverity:
            count = len([a for a in active if a.severity == severity])
            by_severity[severity.value] = count
        
        by_type = {}
        for alert_type in AlertType:
            count = len([a for a in active if a.alert_type == alert_type])
            if count > 0:
                by_type[alert_type.value] = count
        
        return {
            'total': len(all_alerts),
            'active': len(active),
            'unread': len([a for a in active if not a.is_read]),
            'acknowledged': len([a for a in active if a.is_acknowledged]),
            'by_severity': by_severity,
            'by_type': by_type,
            'critical_count': by_severity.get(AlertSeverity.CRITICAL.value, 0),
            'high_count': by_severity.get(AlertSeverity.HIGH.value, 0)
        }
    
    # === Convenience Methods ===
    
    def alert_estrus(
        self,
        animal_id: str,
        confidence: float,
        optimal_start: datetime,
        optimal_end: datetime
    ) -> ReproductionAlert:
        """Kızgınlık uyarısı oluşturur."""
        return self.create_and_send_alert(
            AlertType.ESTRUS_DETECTED,
            animal_id,
            {
                'confidence': round(confidence * 100),
                'start_time': optimal_start.strftime('%H:%M'),
                'end_time': optimal_end.strftime('%H:%M')
            }
        )
    
    def alert_birth_soon(
        self,
        animal_id: str,
        expected_date: datetime,
        hours_remaining: int
    ) -> ReproductionAlert:
        """Yaklaşan doğum uyarısı oluşturur."""
        if hours_remaining <= 6:
            alert_type = AlertType.BIRTH_IMMINENT
        else:
            alert_type = AlertType.BIRTH_SOON
        
        return self.create_and_send_alert(
            alert_type,
            animal_id,
            {
                'expected_date': expected_date.strftime('%d.%m.%Y %H:%M'),
                'hours_remaining': hours_remaining
            }
        )
    
    def alert_birth_started(self, animal_id: str) -> ReproductionAlert:
        """Doğum başladı uyarısı oluşturur."""
        return self.create_and_send_alert(
            AlertType.BIRTH_STARTED,
            animal_id
        )
    
    def alert_dystocia(
        self,
        animal_id: str,
        reason: str
    ) -> ReproductionAlert:
        """Güç doğum riski uyarısı oluşturur."""
        return self.create_and_send_alert(
            AlertType.DYSTOCIA_RISK,
            animal_id,
            {'reason': reason}
        )
    
    def alert_birth_completed(
        self,
        animal_id: str,
        offspring_count: int
    ) -> ReproductionAlert:
        """Doğum tamamlandı uyarısı oluşturur."""
        return self.create_and_send_alert(
            AlertType.BIRTH_COMPLETED,
            animal_id,
            {'offspring_count': offspring_count}
        )


# Test için örnek kullanım
if __name__ == "__main__":
    manager = ReproductionAlertManager()
    
    # Hayvan isimlerini kaydet
    manager.set_animal_name('inek-001', 'Sarıkız')
    manager.set_animal_name('inek-002', 'Benekli')
    
    # Kızgınlık uyarısı
    alert1 = manager.alert_estrus(
        animal_id='inek-001',
        confidence=0.85,
        optimal_start=datetime.now() + timedelta(hours=12),
        optimal_end=datetime.now() + timedelta(hours=18)
    )
    print(f"Kızgınlık uyarısı: {alert1.title}")
    
    # Doğum yaklaşıyor uyarısı
    alert2 = manager.alert_birth_soon(
        animal_id='inek-002',
        expected_date=datetime.now() + timedelta(hours=20),
        hours_remaining=20
    )
    print(f"Doğum uyarısı: {alert2.title}")
    
    # Kritik uyarı - doğum başladı
    alert3 = manager.alert_birth_started('inek-002')
    print(f"Kritik uyarı: {alert3.title}")
    
    # İstatistikler
    stats = manager.get_alert_statistics()
    print(f"\nUyarı istatistikleri:")
    print(f"  Toplam: {stats['total']}")
    print(f"  Aktif: {stats['active']}")
    print(f"  Kritik: {stats['critical_count']}")
    print(f"  Yüksek: {stats['high_count']}")
    
    # Okunmamış uyarılar
    unread = manager.get_unread_alerts()
    print(f"\nOkunmamış uyarılar: {len(unread)}")
    for alert in unread:
        print(f"  [{alert.severity.value}] {alert.title}")
