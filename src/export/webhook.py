# src/export/webhook.py
"""
Webhook Sender - Webhook Entegrasyonu
=====================================

Event'leri harici sistemlere webhook ile gönderir.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

try:
    import aiohttp  # type: ignore
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook event tipleri."""
    DETECTION = "detection"
    TRACKING = "tracking"
    FEEDING = "feeding"
    HEALTH_ALERT = "health_alert"
    BEHAVIOR_ALERT = "behavior_alert"
    SYSTEM_STATUS = "system_status"
    CUSTOM = "custom"


@dataclass
class WebhookEvent:
    """Webhook event."""
    event_type: WebhookEventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default="")
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = hashlib.sha256(
                f"{self.event_type}_{self.timestamp.isoformat()}".encode()
            ).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


@dataclass
class WebhookConfig:
    """Webhook konfigürasyonu."""
    url: str
    name: str = ""
    secret: Optional[str] = None
    enabled: bool = True
    
    # Event filtresi
    event_types: List[WebhookEventType] = field(default_factory=list)
    
    # Retry ayarları
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 10.0
    
    # Headers
    headers: Dict[str, str] = field(default_factory=dict)
    
    def accepts_event(self, event_type: WebhookEventType) -> bool:
        """Bu webhook bu event tipini kabul ediyor mu?"""
        if not self.event_types:
            return True  # Filtre yoksa hepsini kabul et
        return event_type in self.event_types


class WebhookSender:
    """
    Webhook gönderici.
    
    Eventleri yapılandırılmış webhook URL'lerine gönderir.
    
    Kullanım:
        sender = WebhookSender()
        sender.add_webhook("https://example.com/webhook", "my-webhook")
        sender.send(WebhookEvent(
            event_type=WebhookEventType.DETECTION,
            data={"animal_id": "cow_001", "location": "barn"}
        ))
    """
    
    def __init__(
        self,
        async_mode: bool = False,
        queue_size: int = 1000,
        batch_size: int = 10,
        batch_interval: float = 1.0
    ):
        """
        Args:
            async_mode: Async gönderim kullan
            queue_size: Event kuyruğu boyutu
            batch_size: Batch gönderim sayısı
            batch_interval: Batch gönderim aralığı (saniye)
        """
        self.async_mode = async_mode and AIOHTTP_AVAILABLE
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        
        # Webhooklar
        self._webhooks: Dict[str, WebhookConfig] = {}
        
        # Event kuyruğu
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        
        # İstatistikler
        self._stats = {
            "events_sent": 0,
            "events_failed": 0,
            "events_dropped": 0,
            "webhooks_active": 0,
        }
        
        # Worker thread
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Callbacks
        self._on_success: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        logger.info(f"WebhookSender initialized (async={self.async_mode})")
    
    def add_webhook(
        self,
        url: str,
        name: str = "",
        secret: Optional[str] = None,
        event_types: Optional[List[WebhookEventType]] = None,
        **kwargs
    ) -> str:
        """
        Webhook ekle.
        
        Args:
            url: Webhook URL
            name: Webhook adı
            secret: HMAC secret
            event_types: Kabul edilen event tipleri
            
        Returns:
            Webhook ID
        """
        # URL doğrula
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Invalid webhook URL: {url}")
        
        # Config oluştur
        webhook_id = name or hashlib.sha256(url.encode()).hexdigest()[:8]
        
        config = WebhookConfig(
            url=url,
            name=name or webhook_id,
            secret=secret,
            event_types=event_types or [],
            **kwargs
        )
        
        self._webhooks[webhook_id] = config
        self._stats["webhooks_active"] = len(self._webhooks)
        
        logger.info(f"Added webhook: {webhook_id} -> {url}")
        return webhook_id
    
    def remove_webhook(self, webhook_id: str):
        """Webhook kaldır."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            self._stats["webhooks_active"] = len(self._webhooks)
            logger.info(f"Removed webhook: {webhook_id}")
    
    def enable_webhook(self, webhook_id: str, enabled: bool = True):
        """Webhook'u etkinleştir/devre dışı bırak."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].enabled = enabled
    
    def send(self, event: WebhookEvent) -> bool:
        """
        Event gönder.
        
        Async modda kuyruğa ekler, sync modda direkt gönderir.
        """
        if not self._webhooks:
            return False
        
        if self._running:
            # Background worker çalışıyor, kuyruğa ekle
            try:
                self._queue.put_nowait(event)
                return True
            except queue.Full:
                self._stats["events_dropped"] += 1
                logger.warning("Event queue full, dropping event")
                return False
        else:
            # Direkt gönder
            return self._send_sync(event)
    
    def send_detection(
        self,
        animal_id: str,
        class_name: str,
        confidence: float,
        bbox: tuple,
        **extra
    ):
        """Detection eventi gönder."""
        event = WebhookEvent(
            event_type=WebhookEventType.DETECTION,
            data={
                "animal_id": animal_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": bbox,
                **extra
            }
        )
        self.send(event)
    
    def send_health_alert(
        self,
        animal_id: str,
        alert_type: str,
        severity: str,
        description: str,
        **extra
    ):
        """Sağlık uyarısı gönder."""
        event = WebhookEvent(
            event_type=WebhookEventType.HEALTH_ALERT,
            data={
                "animal_id": animal_id,
                "alert_type": alert_type,
                "severity": severity,
                "description": description,
                **extra
            }
        )
        self.send(event)
    
    def send_feeding(
        self,
        animal_id: str,
        zone_id: str,
        duration_minutes: float,
        estimated_kg: float,
        **extra
    ):
        """Beslenme eventi gönder."""
        event = WebhookEvent(
            event_type=WebhookEventType.FEEDING,
            data={
                "animal_id": animal_id,
                "zone_id": zone_id,
                "duration_minutes": duration_minutes,
                "estimated_kg": estimated_kg,
                **extra
            }
        )
        self.send(event)
    
    def _send_sync(self, event: WebhookEvent) -> bool:
        """Sync gönderim."""
        if not REQUESTS_AVAILABLE:
            logger.error("requests library required for sync webhook")
            return False
        
        payload = event.to_dict()
        success = False
        
        for webhook_id, config in self._webhooks.items():
            if not config.enabled:
                continue
            
            if not config.accepts_event(event.event_type):
                continue
            
            try:
                result = self._send_to_webhook(config, payload)
                if result:
                    success = True
                    self._stats["events_sent"] += 1
            except Exception as e:
                logger.error(f"Webhook {webhook_id} failed: {e}")
                self._stats["events_failed"] += 1
        
        return success
    
    def _send_to_webhook(
        self,
        config: WebhookConfig,
        payload: Dict
    ) -> bool:
        """Tek webhook'a gönder (retry ile)."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Animal-Tracker/1.0",
            **config.headers
        }
        
        # HMAC signature
        if config.secret:
            body = json.dumps(payload)
            signature = hmac.new(
                config.secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        # Retry loop
        for attempt in range(config.max_retries):
            try:
                response = requests.post(
                    config.url,
                    json=payload,
                    headers=headers,
                    timeout=config.timeout
                )
                
                if response.status_code < 400:
                    return True
                else:
                    logger.warning(
                        f"Webhook returned {response.status_code}: {response.text[:100]}"
                    )
            except requests.Timeout:
                logger.warning(f"Webhook timeout (attempt {attempt + 1})")
            except requests.RequestException as e:
                logger.error(f"Webhook error: {e}")
            
            if attempt < config.max_retries - 1:
                time.sleep(config.retry_delay * (attempt + 1))
        
        return False
    
    def start_background_worker(self):
        """Background worker başlat."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="WebhookWorker"
        )
        self._worker_thread.start()
        logger.info("Webhook background worker started")
    
    def stop_background_worker(self, timeout: float = 5.0):
        """Background worker durdur."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
            self._worker_thread = None
        
        logger.info("Webhook background worker stopped")
    
    def _worker_loop(self):
        """Background worker döngüsü."""
        batch = []
        last_send = time.time()
        
        while self._running:
            try:
                # Event al (timeout ile)
                try:
                    event = self._queue.get(timeout=0.1)
                    batch.append(event)
                except queue.Empty:
                    pass
                
                # Batch gönder
                should_send = (
                    len(batch) >= self.batch_size or
                    (batch and time.time() - last_send >= self.batch_interval)
                )
                
                if should_send:
                    for event in batch:
                        self._send_sync(event)
                    batch = []
                    last_send = time.time()
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
        
        # Kalan eventleri gönder
        for event in batch:
            self._send_sync(event)
    
    @property
    def statistics(self) -> Dict[str, int]:
        """İstatistikleri al."""
        return dict(self._stats)
    
    def on_success(self, callback: Callable):
        """Başarılı gönderim callback'i."""
        self._on_success = callback
    
    def on_error(self, callback: Callable):
        """Hata callback'i."""
        self._on_error = callback
