"""
Push Notification Servisi

iOS, Android ve Web için push bildirim gönderimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import json
from abc import ABC, abstractmethod
import hashlib
from collections import defaultdict


class NotificationPriority(Enum):
    """Bildirim önceliği"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(Enum):
    """Bildirim tipi"""
    ALERT = "alert"             # Uyarı
    REMINDER = "reminder"       # Hatırlatma
    UPDATE = "update"           # Güncelleme
    INFO = "info"               # Bilgi
    EMERGENCY = "emergency"     # Acil


class NotificationChannel(Enum):
    """Bildirim kanalı"""
    PUSH = "push"               # Push notification
    EMAIL = "email"             # E-posta
    SMS = "sms"                 # SMS
    IN_APP = "in_app"           # Uygulama içi
    WEBHOOK = "webhook"         # Webhook


class DeliveryStatus(Enum):
    """Teslimat durumu"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CLICKED = "clicked"


@dataclass
class NotificationPayload:
    """Bildirim içeriği"""
    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    sound: str = "default"
    badge: Optional[int] = None
    category: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "image_url": self.image_url,
            "action_url": self.action_url,
            "sound": self.sound,
            "badge": self.badge,
            "category": self.category
        }
    
    def to_apns(self) -> Dict:
        """Apple Push Notification formatı"""
        aps = {
            "alert": {
                "title": self.title,
                "body": self.body
            },
            "sound": self.sound
        }
        if self.badge is not None:
            aps["badge"] = self.badge
        if self.category:
            aps["category"] = self.category
        
        payload = {"aps": aps}
        payload.update(self.data)
        return payload
    
    def to_fcm(self) -> Dict:
        """Firebase Cloud Messaging formatı"""
        return {
            "notification": {
                "title": self.title,
                "body": self.body,
                "image": self.image_url
            },
            "data": self.data
        }


@dataclass
class DeviceToken:
    """Cihaz token'ı"""
    token_id: str
    device_id: str
    user_id: str
    platform: str               # ios, android, web
    token: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "token_id": self.token_id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "platform": self.platform,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class NotificationRecord:
    """Bildirim kaydı"""
    notification_id: str
    user_id: str
    payload: NotificationPayload
    type: NotificationType
    priority: NotificationPriority
    channel: NotificationChannel
    status: DeliveryStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "payload": self.payload.to_dict(),
            "type": self.type.value,
            "priority": self.priority.value,
            "channel": self.channel.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
        }


@dataclass
class UserPreferences:
    """Kullanıcı bildirim tercihleri"""
    user_id: str
    enabled: bool = True
    channels: List[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.PUSH, NotificationChannel.IN_APP]
    )
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None
    alert_types: Dict[str, bool] = field(default_factory=dict)
    min_priority: NotificationPriority = NotificationPriority.LOW
    
    def is_quiet_time(self) -> bool:
        """Sessiz saat mı kontrol et"""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        
        current_hour = datetime.now().hour
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
        else:
            # Gece yarısını geçen sessiz saatler (ör: 22-07)
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
    
    def should_receive(self, notification_type: NotificationType,
                      priority: NotificationPriority) -> bool:
        """Bu bildirimi almalı mı?"""
        if not self.enabled:
            return False
        
        # Kritik bildirimler her zaman
        if priority == NotificationPriority.CRITICAL:
            return True
        
        # Sessiz saatlerde yalnızca yüksek öncelik
        if self.is_quiet_time() and priority.value < NotificationPriority.HIGH.value:
            return False
        
        # Minimum öncelik kontrolü
        priority_order = {
            NotificationPriority.LOW: 0,
            NotificationPriority.NORMAL: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.CRITICAL: 3
        }
        
        if priority_order[priority] < priority_order[self.min_priority]:
            return False
        
        # Tip bazlı kontrol
        type_key = notification_type.value
        if type_key in self.alert_types:
            return self.alert_types[type_key]
        
        return True


class PushProvider(ABC):
    """Push sağlayıcı temel sınıfı"""
    
    @abstractmethod
    async def send(self, token: str, payload: NotificationPayload) -> bool:
        """Bildirim gönder"""
        pass
    
    @abstractmethod
    async def send_batch(self, tokens: List[str], 
                        payload: NotificationPayload) -> Dict[str, bool]:
        """Toplu bildirim gönder"""
        pass


class APNSProvider(PushProvider):
    """Apple Push Notification Service"""
    
    def __init__(self, config: Dict):
        self.key_id = config.get("key_id")
        self.team_id = config.get("team_id")
        self.bundle_id = config.get("bundle_id")
        self.key_file = config.get("key_file")
        self.sandbox = config.get("sandbox", False)
    
    async def send(self, token: str, payload: NotificationPayload) -> bool:
        """iOS cihaza bildirim gönder"""
        # Gerçek implementasyonda APNs HTTP/2 API kullanılır
        # import aioapns veya httpx ile
        
        try:
            apns_payload = payload.to_apns()
            
            # Simülasyon
            await asyncio.sleep(0.1)
            
            # Gerçek gönderim kodu buraya
            # response = await self.client.send(token, apns_payload)
            
            return True
        except Exception as e:
            print(f"APNS gönderim hatası: {e}")
            return False
    
    async def send_batch(self, tokens: List[str],
                        payload: NotificationPayload) -> Dict[str, bool]:
        """Toplu iOS bildirimi"""
        results = {}
        
        tasks = [self.send(token, payload) for token in tokens]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for token, response in zip(tokens, responses):
            if isinstance(response, Exception):
                results[token] = False
            else:
                results[token] = response
        
        return results


class FCMProvider(PushProvider):
    """Firebase Cloud Messaging"""
    
    def __init__(self, config: Dict):
        self.project_id = config.get("project_id")
        self.service_account = config.get("service_account")
    
    async def send(self, token: str, payload: NotificationPayload) -> bool:
        """Android/Web cihaza bildirim gönder"""
        try:
            fcm_payload = payload.to_fcm()
            fcm_payload["token"] = token
            
            # Simülasyon
            await asyncio.sleep(0.1)
            
            # Gerçek gönderim kodu
            # response = await self.client.send(fcm_payload)
            
            return True
        except Exception as e:
            print(f"FCM gönderim hatası: {e}")
            return False
    
    async def send_batch(self, tokens: List[str],
                        payload: NotificationPayload) -> Dict[str, bool]:
        """Toplu Android/Web bildirimi"""
        results = {}
        
        # FCM multicast kullanılabilir (500 token limiti)
        batch_size = 500
        
        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i+batch_size]
            
            tasks = [self.send(token, payload) for token in batch]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for token, response in zip(batch, responses):
                results[token] = not isinstance(response, Exception) and response
        
        return results


class PushNotificationService:
    """Ana push bildirim servisi"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Sağlayıcılar
        self.providers: Dict[str, PushProvider] = {}
        
        # Token deposu
        self.device_tokens: Dict[str, DeviceToken] = {}
        self.user_tokens: Dict[str, List[str]] = defaultdict(list)  # user_id -> token_ids
        
        # Bildirim geçmişi
        self.notifications: Dict[str, NotificationRecord] = {}
        
        # Kullanıcı tercihleri
        self.user_preferences: Dict[str, UserPreferences] = {}
        
        # İstatistikler
        self.stats = {
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "by_platform": defaultdict(int),
            "by_type": defaultdict(int)
        }
        
        # Sayaç
        self._notification_counter = 0
        self._token_counter = 0
        
        # Sağlayıcıları başlat
        self._init_providers()
    
    def _init_providers(self):
        """Push sağlayıcılarını başlat"""
        if "apns" in self.config:
            self.providers["ios"] = APNSProvider(self.config["apns"])
        
        if "fcm" in self.config:
            self.providers["android"] = FCMProvider(self.config["fcm"])
            self.providers["web"] = FCMProvider(self.config["fcm"])
    
    def _generate_notification_id(self) -> str:
        """Benzersiz bildirim ID'si"""
        self._notification_counter += 1
        return f"NOTIF_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._notification_counter}"
    
    def _generate_token_id(self) -> str:
        """Benzersiz token ID'si"""
        self._token_counter += 1
        return f"TOKEN_{self._token_counter}"
    
    def register_device(self, user_id: str, device_id: str,
                       platform: str, token: str) -> DeviceToken:
        """Cihaz token'ı kaydet"""
        token_id = self._generate_token_id()
        
        device_token = DeviceToken(
            token_id=token_id,
            device_id=device_id,
            user_id=user_id,
            platform=platform.lower(),
            token=token,
            created_at=datetime.now()
        )
        
        self.device_tokens[token_id] = device_token
        self.user_tokens[user_id].append(token_id)
        
        return device_token
    
    def unregister_device(self, token_id: str) -> bool:
        """Cihaz token'ını kaldır"""
        if token_id not in self.device_tokens:
            return False
        
        token = self.device_tokens[token_id]
        token.is_active = False
        
        return True
    
    def update_user_preferences(self, user_id: str, 
                               preferences: Dict) -> UserPreferences:
        """Kullanıcı tercihlerini güncelle"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id=user_id)
        
        prefs = self.user_preferences[user_id]
        
        if "enabled" in preferences:
            prefs.enabled = preferences["enabled"]
        if "channels" in preferences:
            prefs.channels = [NotificationChannel(c) for c in preferences["channels"]]
        if "quiet_hours_start" in preferences:
            prefs.quiet_hours_start = preferences["quiet_hours_start"]
        if "quiet_hours_end" in preferences:
            prefs.quiet_hours_end = preferences["quiet_hours_end"]
        if "min_priority" in preferences:
            prefs.min_priority = NotificationPriority(preferences["min_priority"])
        if "alert_types" in preferences:
            prefs.alert_types.update(preferences["alert_types"])
        
        return prefs
    
    def get_user_tokens(self, user_id: str, 
                       platform: Optional[str] = None) -> List[DeviceToken]:
        """Kullanıcının aktif token'larını al"""
        token_ids = self.user_tokens.get(user_id, [])
        tokens = []
        
        for token_id in token_ids:
            token = self.device_tokens.get(token_id)
            if token and token.is_active:
                if platform is None or token.platform == platform.lower():
                    tokens.append(token)
        
        return tokens
    
    async def send_notification(self, user_id: str,
                               payload: NotificationPayload,
                               notification_type: NotificationType = NotificationType.INFO,
                               priority: NotificationPriority = NotificationPriority.NORMAL) -> NotificationRecord:
        """Kullanıcıya bildirim gönder"""
        # Tercih kontrolü
        prefs = self.user_preferences.get(user_id, UserPreferences(user_id=user_id))
        
        if not prefs.should_receive(notification_type, priority):
            record = NotificationRecord(
                notification_id=self._generate_notification_id(),
                user_id=user_id,
                payload=payload,
                type=notification_type,
                priority=priority,
                channel=NotificationChannel.PUSH,
                status=DeliveryStatus.FAILED,
                created_at=datetime.now(),
                error_message="Kullanıcı tercihleri nedeniyle gönderilmedi"
            )
            self.notifications[record.notification_id] = record
            return record
        
        # Kullanıcının token'larını al
        tokens = self.get_user_tokens(user_id)
        
        if not tokens:
            record = NotificationRecord(
                notification_id=self._generate_notification_id(),
                user_id=user_id,
                payload=payload,
                type=notification_type,
                priority=priority,
                channel=NotificationChannel.PUSH,
                status=DeliveryStatus.FAILED,
                created_at=datetime.now(),
                error_message="Kayıtlı cihaz bulunamadı"
            )
            self.notifications[record.notification_id] = record
            return record
        
        # Platform bazında gönder
        success = False
        for token in tokens:
            provider = self.providers.get(token.platform)
            if provider:
                result = await provider.send(token.token, payload)
                if result:
                    success = True
                    token.last_used = datetime.now()
                    self.stats["by_platform"][token.platform] += 1
        
        status = DeliveryStatus.SENT if success else DeliveryStatus.FAILED
        
        record = NotificationRecord(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            payload=payload,
            type=notification_type,
            priority=priority,
            channel=NotificationChannel.PUSH,
            status=status,
            created_at=datetime.now(),
            sent_at=datetime.now() if success else None
        )
        
        self.notifications[record.notification_id] = record
        
        # İstatistik güncelle
        if success:
            self.stats["total_sent"] += 1
        else:
            self.stats["total_failed"] += 1
        self.stats["by_type"][notification_type.value] += 1
        
        return record
    
    async def send_to_topic(self, topic: str,
                           payload: NotificationPayload,
                           notification_type: NotificationType = NotificationType.INFO,
                           priority: NotificationPriority = NotificationPriority.NORMAL) -> int:
        """Konuya abone olan tüm cihazlara gönder"""
        # Gerçek implementasyonda FCM topic messaging kullanılır
        # Bu örnek için simülasyon
        
        sent_count = 0
        
        # Tüm kullanıcılara gönder (gerçekte topic subscription olur)
        for user_id in self.user_tokens.keys():
            record = await self.send_notification(user_id, payload, notification_type, priority)
            if record.status == DeliveryStatus.SENT:
                sent_count += 1
        
        return sent_count
    
    async def send_batch(self, user_ids: List[str],
                        payload: NotificationPayload,
                        notification_type: NotificationType = NotificationType.INFO,
                        priority: NotificationPriority = NotificationPriority.NORMAL) -> Dict[str, bool]:
        """Çoklu kullanıcıya gönder"""
        results = {}
        
        tasks = [
            self.send_notification(uid, payload, notification_type, priority)
            for uid in user_ids
        ]
        records = await asyncio.gather(*tasks)
        
        for uid, record in zip(user_ids, records):
            results[uid] = record.status == DeliveryStatus.SENT
        
        return results
    
    def mark_delivered(self, notification_id: str) -> bool:
        """Bildirimi teslim edildi olarak işaretle"""
        if notification_id not in self.notifications:
            return False
        
        record = self.notifications[notification_id]
        record.status = DeliveryStatus.DELIVERED
        record.delivered_at = datetime.now()
        
        self.stats["total_delivered"] += 1
        
        return True
    
    def mark_clicked(self, notification_id: str) -> bool:
        """Bildirimi tıklandı olarak işaretle"""
        if notification_id not in self.notifications:
            return False
        
        record = self.notifications[notification_id]
        record.clicked_at = datetime.now()
        record.status = DeliveryStatus.CLICKED
        
        return True
    
    def get_notification_history(self, user_id: str,
                                limit: int = 50) -> List[NotificationRecord]:
        """Kullanıcı bildirim geçmişi"""
        user_notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id
        ]
        
        return sorted(user_notifications, 
                     key=lambda x: x.created_at, 
                     reverse=True)[:limit]
    
    def get_stats(self) -> Dict:
        """İstatistikleri al"""
        return {
            "total_sent": self.stats["total_sent"],
            "total_delivered": self.stats["total_delivered"],
            "total_failed": self.stats["total_failed"],
            "delivery_rate": round(
                self.stats["total_delivered"] / max(1, self.stats["total_sent"]) * 100, 1
            ),
            "by_platform": dict(self.stats["by_platform"]),
            "by_type": dict(self.stats["by_type"]),
            "registered_devices": len([t for t in self.device_tokens.values() if t.is_active]),
            "active_users": len(self.user_tokens)
        }
    
    def cleanup_inactive_tokens(self, days: int = 30) -> int:
        """Eski/kullanılmayan token'ları temizle"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for token_id, token in list(self.device_tokens.items()):
            if token.last_used and token.last_used < cutoff:
                token.is_active = False
                removed += 1
        
        return removed


# Yardımcı fonksiyonlar
def create_alert_notification(title: str, body: str,
                             animal_id: Optional[str] = None,
                             alert_type: str = "general") -> NotificationPayload:
    """Uyarı bildirimi oluştur"""
    data = {"type": "alert", "alert_type": alert_type}
    if animal_id:
        data["animal_id"] = animal_id
    
    return NotificationPayload(
        title=title,
        body=body,
        data=data,
        sound="alert.wav",
        category="ALERT"
    )


def create_health_notification(animal_id: str, condition: str,
                              severity: str = "normal") -> NotificationPayload:
    """Sağlık bildirimi oluştur"""
    return NotificationPayload(
        title=f"Sağlık Uyarısı - Hayvan #{animal_id}",
        body=f"Tespit edilen durum: {condition}",
        data={
            "type": "health",
            "animal_id": animal_id,
            "condition": condition,
            "severity": severity
        },
        sound="health_alert.wav" if severity in ["high", "critical"] else "default",
        category="HEALTH_ALERT"
    )


def create_activity_notification(animal_id: str, activity: str,
                                location: Optional[str] = None) -> NotificationPayload:
    """Aktivite bildirimi oluştur"""
    body = f"Hayvan #{animal_id}: {activity}"
    if location:
        body += f" - Konum: {location}"
    
    return NotificationPayload(
        title="Aktivite Bildirimi",
        body=body,
        data={
            "type": "activity",
            "animal_id": animal_id,
            "activity": activity,
            "location": location
        },
        sound="default",
        category="ACTIVITY"
    )
