"""
SMS Bildirim Servisi
"""

import logging
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


@dataclass
class SMSConfig:
    """SMS konfigürasyonu"""
    provider: str = "twilio"  # twilio, netgsm, vonage
    account_sid: str = ""
    auth_token: str = ""
    from_number: str = ""
    # NetGSM specific
    username: str = ""
    password: str = ""
    header: str = ""
    
    @classmethod
    def from_env(cls) -> "SMSConfig":
        return cls(
            provider=os.getenv("SMS_PROVIDER", "twilio"),
            account_sid=os.getenv("SMS_ACCOUNT_SID", ""),
            auth_token=os.getenv("SMS_AUTH_TOKEN", ""),
            from_number=os.getenv("SMS_FROM_NUMBER", ""),
            username=os.getenv("SMS_USERNAME", ""),
            password=os.getenv("SMS_PASSWORD", ""),
            header=os.getenv("SMS_HEADER", "")
        )


class SMSProvider(ABC):
    """SMS sağlayıcı temel sınıfı"""
    
    @abstractmethod
    def send(self, to: str, message: str) -> bool:
        pass
        
    @abstractmethod
    def send_bulk(self, recipients: List[str], message: str) -> Dict[str, bool]:
        pass


class TwilioProvider(SMSProvider):
    """Twilio SMS sağlayıcısı"""
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        """Twilio client oluştur"""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(
                    self.config.account_sid,
                    self.config.auth_token
                )
            except ImportError:
                logger.error("Twilio kütüphanesi yüklü değil: pip install twilio")
                raise
        return self._client
        
    def send(self, to: str, message: str) -> bool:
        """SMS gönder"""
        try:
            client = self._get_client()
            result = client.messages.create(
                body=message,
                from_=self.config.from_number,
                to=to
            )
            logger.info(f"SMS gönderildi: {to} - SID: {result.sid}")
            return True
        except Exception as e:
            logger.error(f"SMS gönderme hatası: {e}")
            return False
            
    def send_bulk(self, recipients: List[str], message: str) -> Dict[str, bool]:
        """Toplu SMS gönder"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send(recipient, message)
        return results


class NetGSMProvider(SMSProvider):
    """NetGSM SMS sağlayıcısı (Türkiye)"""
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self.api_url = "https://api.netgsm.com.tr/sms/send/get"
        
    def send(self, to: str, message: str) -> bool:
        """SMS gönder"""
        try:
            import requests
            
            params = {
                'usercode': self.config.username,
                'password': self.config.password,
                'gsmno': to,
                'message': message,
                'msgheader': self.config.header,
                'dil': 'TR'
            }
            
            response = requests.get(self.api_url, params=params, timeout=30)
            
            if response.text.startswith('00') or response.text.startswith('01'):
                logger.info(f"SMS gönderildi: {to}")
                return True
            else:
                logger.error(f"NetGSM hatası: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SMS gönderme hatası: {e}")
            return False
            
    def send_bulk(self, recipients: List[str], message: str) -> Dict[str, bool]:
        """Toplu SMS gönder"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send(recipient, message)
        return results


class MockSMSProvider(SMSProvider):
    """Test için mock SMS sağlayıcısı"""
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self.sent_messages: List[Dict] = []
        
    def send(self, to: str, message: str) -> bool:
        """SMS gönder (simüle)"""
        self.sent_messages.append({
            'to': to,
            'message': message
        })
        logger.info(f"[MOCK] SMS gönderildi: {to}")
        return True
        
    def send_bulk(self, recipients: List[str], message: str) -> Dict[str, bool]:
        """Toplu SMS gönder (simüle)"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send(recipient, message)
        return results


class SMSNotifier:
    """SMS bildirim servisi"""
    
    def __init__(self, config: SMSConfig = None):
        self.config = config or SMSConfig.from_env()
        self._provider = self._create_provider()
        self._recipients: List[str] = []
        
    def _create_provider(self) -> SMSProvider:
        """SMS sağlayıcı oluştur"""
        providers = {
            'twilio': TwilioProvider,
            'netgsm': NetGSMProvider,
            'mock': MockSMSProvider
        }
        
        provider_class = providers.get(self.config.provider, MockSMSProvider)
        return provider_class(self.config)
        
    def add_recipient(self, phone: str):
        """Alıcı ekle"""
        # Telefon numarasını normalize et
        phone = self._normalize_phone(phone)
        if phone not in self._recipients:
            self._recipients.append(phone)
            
    def remove_recipient(self, phone: str):
        """Alıcı çıkar"""
        phone = self._normalize_phone(phone)
        if phone in self._recipients:
            self._recipients.remove(phone)
            
    def set_recipients(self, phones: List[str]):
        """Alıcı listesini ayarla"""
        self._recipients = [self._normalize_phone(p) for p in phones]
        
    def _normalize_phone(self, phone: str) -> str:
        """Telefon numarasını normalize et"""
        # Boşluk ve tire temizle
        phone = phone.replace(" ", "").replace("-", "")
        
        # Türkiye numarası düzeltme
        if phone.startswith("0"):
            phone = "+90" + phone[1:]
        elif not phone.startswith("+"):
            phone = "+90" + phone
            
        return phone
        
    def send(self, notification) -> bool:
        """Bildirim gönder"""
        if not self._recipients:
            logger.warning("SMS alıcısı tanımlanmamış")
            return False
            
        message = self._format_notification(notification)
        results = self._provider.send_bulk(self._recipients, message)
        
        return all(results.values())
        
    def send_sms(self, message: str, recipients: List[str] = None) -> Dict[str, bool]:
        """SMS gönder"""
        recipients = recipients or self._recipients
        
        if not recipients:
            logger.warning("SMS alıcısı yok")
            return {}
            
        return self._provider.send_bulk(recipients, message)
        
    def _format_notification(self, notification) -> str:
        """Bildirimi SMS formatına çevir"""
        # SMS 160 karakter sınırı var, kısa tut
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🔴",
            "critical": "🚨"
        }
        
        icon = severity_icons.get(notification.severity.value, "📢")
        message = f"{icon} {notification.title}: {notification.message}"
        
        # Karakter sınırı
        if len(message) > 155:
            message = message[:152] + "..."
            
        return message
        
    def get_balance(self) -> Optional[float]:
        """Bakiye sorgula (destekleyen sağlayıcılar için)"""
        if hasattr(self._provider, 'get_balance'):
            return self._provider.get_balance()
        return None
