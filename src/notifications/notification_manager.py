"""
Bildirim Yöneticisi
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import uuid


logger = logging.getLogger(__name__)


class NotificationSeverity(Enum):
    """Bildirim önem seviyesi"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Bildirim kanalları"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


@dataclass
class Notification:
    """Bildirim veri yapısı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    severity: NotificationSeverity = NotificationSeverity.INFO
    channels: List[NotificationChannel] = field(default_factory=list)
    animal_id: Optional[int] = None
    camera_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    is_read: bool = False
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'channels': [c.value for c in self.channels],
            'animal_id': self.animal_id,
            'camera_id': self.camera_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'is_read': self.is_read,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class NotificationManager:
    """Bildirim yönetim sistemi"""
    
    def __init__(self):
        self._notifiers: Dict[NotificationChannel, Any] = {}
        self._notification_history: List[Notification] = []
        self._max_history = 1000
        self._queue: asyncio.Queue = None
        self._running = False
        self._callbacks: Dict[str, List[Callable]] = {}
        
    def register_notifier(self, channel: NotificationChannel, notifier: Any):
        """Bildirim servisini kaydet"""
        self._notifiers[channel] = notifier
        logger.info(f"Bildirim servisi kaydedildi: {channel.value}")
        
    def add_callback(self, event: str, callback: Callable):
        """Olay callback'i ekle"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        
    async def _trigger_callbacks(self, event: str, data: Any):
        """Callback'leri tetikle"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Callback hatası: {e}")
                
    async def send_notification(self, notification: Notification) -> bool:
        """Bildirim gönder"""
        success = True
        
        for channel in notification.channels:
            notifier = self._notifiers.get(channel)
            
            if notifier is None:
                logger.warning(f"Bildirim servisi bulunamadı: {channel.value}")
                continue
                
            try:
                if asyncio.iscoroutinefunction(notifier.send):
                    await notifier.send(notification)
                else:
                    notifier.send(notification)
                    
                logger.info(f"Bildirim gönderildi: {channel.value} - {notification.title}")
                
            except Exception as e:
                logger.error(f"Bildirim gönderme hatası ({channel.value}): {e}")
                success = False
                
        notification.sent_at = datetime.utcnow()
        self._add_to_history(notification)
        
        await self._trigger_callbacks('notification_sent', notification)
        
        return success
        
    def create_notification(
        self,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        channels: List[NotificationChannel] = None,
        animal_id: int = None,
        camera_id: str = None,
        metadata: Dict = None
    ) -> Notification:
        """Yeni bildirim oluştur"""
        if channels is None:
            channels = [NotificationChannel.IN_APP]
            
        return Notification(
            title=title,
            message=message,
            severity=severity,
            channels=channels,
            animal_id=animal_id,
            camera_id=camera_id,
            metadata=metadata or {}
        )
        
    async def notify(
        self,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        channels: List[NotificationChannel] = None,
        **kwargs
    ) -> bool:
        """Hızlı bildirim gönder"""
        notification = self.create_notification(
            title=title,
            message=message,
            severity=severity,
            channels=channels,
            **kwargs
        )
        return await self.send_notification(notification)
        
    def _add_to_history(self, notification: Notification):
        """Geçmişe ekle"""
        self._notification_history.append(notification)
        
        # Maksimum boyutu aş
        if len(self._notification_history) > self._max_history:
            self._notification_history = self._notification_history[-self._max_history:]
            
    def get_history(
        self,
        limit: int = 50,
        severity: NotificationSeverity = None,
        unread_only: bool = False
    ) -> List[Notification]:
        """Bildirim geçmişini getir"""
        history = self._notification_history.copy()
        
        if severity:
            history = [n for n in history if n.severity == severity]
            
        if unread_only:
            history = [n for n in history if not n.is_read]
            
        return sorted(history, key=lambda x: x.created_at, reverse=True)[:limit]
        
    def mark_as_read(self, notification_id: str) -> bool:
        """Bildirimi okundu olarak işaretle"""
        for notification in self._notification_history:
            if notification.id == notification_id:
                notification.is_read = True
                return True
        return False
        
    def acknowledge(self, notification_id: str) -> bool:
        """Bildirimi onayla"""
        for notification in self._notification_history:
            if notification.id == notification_id:
                notification.acknowledged_at = datetime.utcnow()
                notification.is_read = True
                return True
        return False
        
    def get_unread_count(self) -> int:
        """Okunmamış bildirim sayısı"""
        return sum(1 for n in self._notification_history if not n.is_read)
        
    def clear_history(self, before: datetime = None):
        """Geçmişi temizle"""
        if before:
            self._notification_history = [
                n for n in self._notification_history
                if n.created_at >= before
            ]
        else:
            self._notification_history.clear()
            
    async def start_queue_processor(self):
        """Kuyruk işleyiciyi başlat"""
        self._queue = asyncio.Queue()
        self._running = True
        
        while self._running:
            try:
                notification = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                await self.send_notification(notification)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Kuyruk işleme hatası: {e}")
                
    def stop_queue_processor(self):
        """Kuyruk işleyiciyi durdur"""
        self._running = False
        
    async def queue_notification(self, notification: Notification):
        """Bildirimi kuyruğa ekle"""
        if self._queue:
            await self._queue.put(notification)
        else:
            await self.send_notification(notification)


# Singleton instance
notification_manager = NotificationManager()


# Yardımcı fonksiyonlar
async def send_alert(
    title: str,
    message: str,
    severity: str = "info",
    animal_id: int = None,
    camera_id: str = None
):
    """Hızlı uyarı gönder"""
    severity_map = {
        "info": NotificationSeverity.INFO,
        "warning": NotificationSeverity.WARNING,
        "error": NotificationSeverity.ERROR,
        "critical": NotificationSeverity.CRITICAL
    }
    
    await notification_manager.notify(
        title=title,
        message=message,
        severity=severity_map.get(severity, NotificationSeverity.INFO),
        channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
        animal_id=animal_id,
        camera_id=camera_id
    )


async def send_health_alert(animal_id: int, health_score: float, issue: str):
    """Sağlık uyarısı gönder"""
    severity = NotificationSeverity.WARNING
    if health_score < 50:
        severity = NotificationSeverity.ERROR
    if health_score < 30:
        severity = NotificationSeverity.CRITICAL
        
    await notification_manager.notify(
        title=f"Sağlık Uyarısı - Hayvan #{animal_id}",
        message=f"Sağlık skoru: {health_score:.1f}%. Tespit edilen sorun: {issue}",
        severity=severity,
        channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.EMAIL],
        animal_id=animal_id,
        metadata={"health_score": health_score, "issue": issue}
    )


async def send_behavior_alert(animal_id: int, behavior: str, details: str):
    """Davranış uyarısı gönder"""
    await notification_manager.notify(
        title=f"Anormal Davranış - Hayvan #{animal_id}",
        message=f"Davranış: {behavior}. {details}",
        severity=NotificationSeverity.WARNING,
        channels=[NotificationChannel.IN_APP],
        animal_id=animal_id,
        metadata={"behavior": behavior, "details": details}
    )
