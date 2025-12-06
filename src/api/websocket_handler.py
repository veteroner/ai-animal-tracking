"""
WebSocket Handler - Gerçek zamanlı iletişim
"""

from typing import Dict, Set, Any, Optional, Callable
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict

from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket mesaj türleri"""
    DETECTION = "detection"
    ALERT = "alert"
    STATUS = "status"
    FRAME = "frame"
    BEHAVIOR = "behavior"
    HEALTH = "health"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class WebSocketMessage:
    """WebSocket mesaj yapısı"""
    type: str
    data: Dict[str, Any]
    timestamp: str = None
    channel: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
            
    def to_json(self) -> str:
        return json.dumps(asdict(self))


class ConnectionManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        # Aktif bağlantılar
        self.active_connections: Dict[str, WebSocket] = {}
        # Kanal abonelikleri
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        # Bağlantı metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # Mesaj kuyrukları
        self._message_queues: Dict[str, asyncio.Queue] = {}
        # İşleyiciler
        self._message_handlers: Dict[str, Callable] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, metadata: Dict = None) -> bool:
        """Yeni bağlantı kabul et"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = metadata or {}
            self._message_queues[client_id] = asyncio.Queue()
            
            logger.info(f"WebSocket bağlantısı kuruldu: {client_id}")
            
            # Hoşgeldin mesajı gönder
            await self.send_personal(client_id, WebSocketMessage(
                type=MessageType.STATUS.value,
                data={
                    "status": "connected",
                    "client_id": client_id,
                    "message": "Bağlantı başarılı"
                }
            ))
            
            return True
        except Exception as e:
            logger.error(f"WebSocket bağlantı hatası: {e}")
            return False
            
    def disconnect(self, client_id: str):
        """Bağlantıyı kapat"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
            
        if client_id in self._message_queues:
            del self._message_queues[client_id]
            
        # Kanal aboneliklerinden çıkar
        for channel in list(self.channel_subscriptions.keys()):
            if client_id in self.channel_subscriptions[channel]:
                self.channel_subscriptions[channel].discard(client_id)
                
        logger.info(f"WebSocket bağlantısı kapatıldı: {client_id}")
        
    async def send_personal(self, client_id: str, message: WebSocketMessage):
        """Belirli bir istemciye mesaj gönder"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message.to_json())
            except Exception as e:
                logger.error(f"Mesaj gönderme hatası ({client_id}): {e}")
                self.disconnect(client_id)
                
    async def broadcast(self, message: WebSocketMessage, exclude: Set[str] = None):
        """Tüm bağlantılara mesaj gönder"""
        exclude = exclude or set()
        for client_id, websocket in list(self.active_connections.items()):
            if client_id not in exclude:
                try:
                    await websocket.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Broadcast hatası ({client_id}): {e}")
                    self.disconnect(client_id)
                    
    async def send_to_channel(self, channel: str, message: WebSocketMessage):
        """Belirli bir kanala abone olanlara mesaj gönder"""
        message.channel = channel
        subscribers = self.channel_subscriptions.get(channel, set())
        
        for client_id in list(subscribers):
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Kanal mesaj hatası ({channel}/{client_id}): {e}")
                    self.disconnect(client_id)
                    
    def subscribe(self, client_id: str, channel: str):
        """Kanala abone ol"""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(client_id)
        logger.debug(f"Kanal aboneliği: {client_id} -> {channel}")
        
    def unsubscribe(self, client_id: str, channel: str):
        """Kanal aboneliğini iptal et"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(client_id)
            
    def register_handler(self, message_type: str, handler: Callable):
        """Mesaj işleyici kaydet"""
        self._message_handlers[message_type] = handler
        
    async def handle_message(self, client_id: str, raw_message: str) -> Optional[WebSocketMessage]:
        """Gelen mesajı işle"""
        try:
            data = json.loads(raw_message)
            message_type = data.get('type', '')
            
            # Ping/Pong
            if message_type == MessageType.PING.value:
                return WebSocketMessage(
                    type=MessageType.PONG.value,
                    data={"timestamp": datetime.utcnow().isoformat()}
                )
                
            # Abone ol
            if message_type == MessageType.SUBSCRIBE.value:
                channel = data.get('data', {}).get('channel')
                if channel:
                    self.subscribe(client_id, channel)
                    return WebSocketMessage(
                        type=MessageType.STATUS.value,
                        data={"subscribed": channel}
                    )
                    
            # Abonelik iptal
            if message_type == MessageType.UNSUBSCRIBE.value:
                channel = data.get('data', {}).get('channel')
                if channel:
                    self.unsubscribe(client_id, channel)
                    return WebSocketMessage(
                        type=MessageType.STATUS.value,
                        data={"unsubscribed": channel}
                    )
                    
            # Özel işleyici
            if message_type in self._message_handlers:
                result = await self._message_handlers[message_type](client_id, data)
                if result:
                    return result
                    
            return None
            
        except json.JSONDecodeError:
            logger.warning(f"Geçersiz JSON mesajı: {raw_message[:100]}")
            return WebSocketMessage(
                type=MessageType.ERROR.value,
                data={"error": "Invalid JSON"}
            )
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
            return WebSocketMessage(
                type=MessageType.ERROR.value,
                data={"error": str(e)}
            )
            
    def get_connection_count(self) -> int:
        """Aktif bağlantı sayısı"""
        return len(self.active_connections)
        
    def get_channel_subscribers(self, channel: str) -> int:
        """Kanal abone sayısı"""
        return len(self.channel_subscriptions.get(channel, set()))
        
    def is_connected(self, client_id: str) -> bool:
        """Bağlantı durumunu kontrol et"""
        return client_id in self.active_connections


# Singleton instance
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint handler"""
    await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            response = await connection_manager.handle_message(client_id, data)
            if response:
                await connection_manager.send_personal(client_id, response)
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket hatası ({client_id}): {e}")
        connection_manager.disconnect(client_id)


# Yardımcı fonksiyonlar
async def broadcast_detection(detection_data: Dict[str, Any]):
    """Tespit verisi yayınla"""
    message = WebSocketMessage(
        type=MessageType.DETECTION.value,
        data=detection_data
    )
    await connection_manager.send_to_channel("detections", message)


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Uyarı yayınla"""
    message = WebSocketMessage(
        type=MessageType.ALERT.value,
        data=alert_data
    )
    await connection_manager.broadcast(message)


async def broadcast_status(status_data: Dict[str, Any]):
    """Sistem durumu yayınla"""
    message = WebSocketMessage(
        type=MessageType.STATUS.value,
        data=status_data
    )
    await connection_manager.send_to_channel("status", message)


async def send_frame_to_viewers(camera_id: str, frame_data: Dict[str, Any]):
    """Frame verisi gönder (base64 encoded)"""
    message = WebSocketMessage(
        type=MessageType.FRAME.value,
        data=frame_data
    )
    await connection_manager.send_to_channel(f"camera:{camera_id}", message)
