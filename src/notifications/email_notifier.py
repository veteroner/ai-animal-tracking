"""
E-posta Bildirim Servisi
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import os


logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """E-posta konfigürasyonu"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    sender_email: str = ""
    sender_name: str = "Hayvan Takip Sistemi"
    use_tls: bool = True
    
    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender_email=os.getenv("SMTP_SENDER_EMAIL", ""),
            sender_name=os.getenv("SMTP_SENDER_NAME", "Hayvan Takip Sistemi"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        )


class EmailNotifier:
    """E-posta bildirim servisi"""
    
    def __init__(self, config: EmailConfig = None):
        self.config = config or EmailConfig.from_env()
        self._recipients: List[str] = []
        
    def add_recipient(self, email: str):
        """Alıcı ekle"""
        if email not in self._recipients:
            self._recipients.append(email)
            
    def remove_recipient(self, email: str):
        """Alıcı çıkar"""
        if email in self._recipients:
            self._recipients.remove(email)
            
    def set_recipients(self, emails: List[str]):
        """Alıcı listesini ayarla"""
        self._recipients = emails.copy()
        
    def send(self, notification) -> bool:
        """Bildirim gönder"""
        if not self._recipients:
            logger.warning("E-posta alıcısı tanımlanmamış")
            return False
            
        return self.send_email(
            subject=notification.title,
            body=self._format_notification(notification),
            recipients=self._recipients
        )
        
    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str] = None,
        html_body: str = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """E-posta gönder"""
        recipients = recipients or self._recipients
        
        if not recipients:
            logger.warning("E-posta alıcısı yok")
            return False
            
        if not self.config.username or not self.config.password:
            logger.warning("SMTP kimlik bilgileri eksik")
            return False
            
        try:
            # Mesaj oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>"
            msg['To'] = ", ".join(recipients)
            
            # Düz metin
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # HTML (varsa)
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
            # Ekler (varsa)
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
                    
            # Gönder
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
                server.send_message(msg)
                
            logger.info(f"E-posta gönderildi: {subject} -> {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"E-posta gönderme hatası: {e}")
            return False
            
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Ek dosya ekle"""
        try:
            file_path = attachment.get('path')
            file_name = attachment.get('name') or os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{file_name}"'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error(f"Ek dosya ekleme hatası: {e}")
            
    def _format_notification(self, notification) -> str:
        """Bildirimi e-posta formatına çevir"""
        lines = [
            f"📢 {notification.title}",
            "",
            notification.message,
            "",
            f"Önem Seviyesi: {notification.severity.value.upper()}",
            f"Tarih: {notification.created_at.strftime('%d.%m.%Y %H:%M:%S')}",
        ]
        
        if notification.animal_id:
            lines.append(f"Hayvan ID: {notification.animal_id}")
            
        if notification.camera_id:
            lines.append(f"Kamera ID: {notification.camera_id}")
            
        if notification.metadata:
            lines.append("")
            lines.append("Ek Bilgiler:")
            for key, value in notification.metadata.items():
                lines.append(f"  - {key}: {value}")
                
        lines.append("")
        lines.append("---")
        lines.append("Bu mesaj Hayvan Takip Sistemi tarafından otomatik olarak gönderilmiştir.")
        
        return "\n".join(lines)
        
    def _format_html_notification(self, notification) -> str:
        """Bildirimi HTML formatına çevir"""
        severity_colors = {
            "info": "#3498db",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "critical": "#c0392b"
        }
        
        color = severity_colors.get(notification.severity.value, "#3498db")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: {color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .footer {{ background: #ecf0f1; padding: 15px; font-size: 12px; color: #7f8c8d; text-align: center; }}
                .badge {{ display: inline-block; padding: 4px 8px; background: {color}; color: white; border-radius: 4px; font-size: 12px; }}
                .meta {{ color: #7f8c8d; font-size: 14px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin:0;">📢 {notification.title}</h2>
                </div>
                <div class="content">
                    <p>{notification.message}</p>
                    <p><span class="badge">{notification.severity.value.upper()}</span></p>
                    <div class="meta">
                        <p>📅 Tarih: {notification.created_at.strftime('%d.%m.%Y %H:%M:%S')}</p>
        """
        
        if notification.animal_id:
            html += f"<p>🐄 Hayvan ID: {notification.animal_id}</p>"
            
        if notification.camera_id:
            html += f"<p>📹 Kamera ID: {notification.camera_id}</p>"
            
        html += """
                    </div>
                </div>
                <div class="footer">
                    Bu mesaj Hayvan Takip Sistemi tarafından otomatik olarak gönderilmiştir.
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def test_connection(self) -> bool:
        """SMTP bağlantısını test et"""
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
                logger.info("SMTP bağlantısı başarılı")
                return True
        except Exception as e:
            logger.error(f"SMTP bağlantı hatası: {e}")
            return False
