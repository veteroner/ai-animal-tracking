"""
Veterinary System Integration - Veteriner Sistemi Entegrasyonu
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


logger = logging.getLogger(__name__)


class AlertPriority(str, Enum):
    """Uyarı önceliği"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class VetConfig:
    """Veteriner sistemi konfigürasyonu"""
    base_url: str
    api_key: str = ""
    clinic_id: str = ""
    timeout: int = 30
    auto_alert: bool = True  # Otomatik uyarı gönder


@dataclass
class HealthAlert:
    """Sağlık uyarısı"""
    animal_id: str
    alert_type: str
    priority: AlertPriority
    description: str
    observations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TreatmentRecommendation:
    """Tedavi önerisi"""
    condition: str
    recommended_action: str
    urgency: str
    notes: str = ""


class VeterinarySystemIntegration:
    """Veteriner sistemi entegrasyonu"""
    
    def __init__(self, config: VetConfig):
        self.config = config
        self._pending_alerts: List[HealthAlert] = []
        
    def _get_headers(self) -> Dict[str, str]:
        """İstek header'ları"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Clinic-ID": self.config.clinic_id
        }
        
    async def send_health_alert(self, alert: HealthAlert) -> bool:
        """Sağlık uyarısı gönder"""
        if not HTTPX_AVAILABLE:
            logger.warning("httpx yüklü değil, uyarı kaydedildi")
            self._pending_alerts.append(alert)
            return False
            
        data = {
            "animal_id": alert.animal_id,
            "alert_type": alert.alert_type,
            "priority": alert.priority.value,
            "description": alert.description,
            "observations": alert.observations,
            "metrics": alert.metrics,
            "timestamp": alert.timestamp.isoformat(),
            "source": "ai_tracking_system"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/alerts",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                logger.info(f"Sağlık uyarısı gönderildi: {alert.animal_id}")
                return True
                
        except Exception as e:
            logger.error(f"Uyarı gönderilemedi: {e}")
            self._pending_alerts.append(alert)
            return False
            
    async def get_animal_history(self, animal_id: str) -> List[Dict]:
        """Hayvan sağlık geçmişi al"""
        if not HTTPX_AVAILABLE:
            return []
            
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.base_url}/animals/{animal_id}/history",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Sağlık geçmişi alınamadı: {e}")
            return []
            
    async def get_treatment_recommendations(
        self,
        symptoms: List[str],
        species: str
    ) -> List[TreatmentRecommendation]:
        """Tedavi önerisi al"""
        if not HTTPX_AVAILABLE:
            return []
            
        data = {
            "symptoms": symptoms,
            "species": species
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/recommendations",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                
                recommendations = []
                for item in response.json():
                    recommendations.append(TreatmentRecommendation(
                        condition=item.get('condition', ''),
                        recommended_action=item.get('recommended_action', ''),
                        urgency=item.get('urgency', 'normal'),
                        notes=item.get('notes', '')
                    ))
                    
                return recommendations
                
        except Exception as e:
            logger.error(f"Tedavi önerisi alınamadı: {e}")
            return []
            
    async def schedule_checkup(
        self,
        animal_id: str,
        reason: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        preferred_date: datetime = None
    ) -> Optional[str]:
        """Muayene randevusu oluştur"""
        if not HTTPX_AVAILABLE:
            return None
            
        data = {
            "animal_id": animal_id,
            "reason": reason,
            "priority": priority.value,
            "preferred_date": preferred_date.isoformat() if preferred_date else None,
            "source": "ai_tracking_system"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/appointments",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get('appointment_id')
                
        except Exception as e:
            logger.error(f"Randevu oluşturulamadı: {e}")
            return None
            
    async def report_abnormal_behavior(
        self,
        animal_id: str,
        behavior_type: str,
        description: str,
        severity: int = 1
    ) -> bool:
        """Anormal davranış rapor et"""
        alert = HealthAlert(
            animal_id=animal_id,
            alert_type="abnormal_behavior",
            priority=self._severity_to_priority(severity),
            description=description,
            observations=[f"Davranış tipi: {behavior_type}"],
            metrics={"severity": severity, "behavior_type": behavior_type}
        )
        
        return await self.send_health_alert(alert)
        
    def _severity_to_priority(self, severity: int) -> AlertPriority:
        """Şiddet değerini önceliğe çevir"""
        if severity >= 4:
            return AlertPriority.CRITICAL
        elif severity >= 3:
            return AlertPriority.HIGH
        elif severity >= 2:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
            
    async def send_pending_alerts(self) -> int:
        """Bekleyen uyarıları gönder"""
        sent = 0
        remaining = []
        
        for alert in self._pending_alerts:
            if await self.send_health_alert(alert):
                sent += 1
            else:
                remaining.append(alert)
                
        self._pending_alerts = remaining
        return sent
        
    def get_pending_alerts_count(self) -> int:
        """Bekleyen uyarı sayısı"""
        return len(self._pending_alerts)
        
    async def health_check(self) -> bool:
        """Servis sağlık kontrolü"""
        if not HTTPX_AVAILABLE:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.config.base_url}/health",
                    headers=self._get_headers()
                )
                return response.status_code == 200
                
        except Exception:
            return False
            
    # Yaygın sağlık durumları için yardımcı metodlar
    
    async def alert_lameness(self, animal_id: str, score: float):
        """Topallık uyarısı"""
        alert = HealthAlert(
            animal_id=animal_id,
            alert_type="lameness",
            priority=AlertPriority.HIGH if score >= 3 else AlertPriority.MEDIUM,
            description=f"Topallık tespit edildi. Skor: {score}",
            metrics={"lameness_score": score}
        )
        return await self.send_health_alert(alert)
        
    async def alert_reduced_activity(
        self,
        animal_id: str,
        current_activity: float,
        normal_activity: float
    ):
        """Azalan aktivite uyarısı"""
        reduction = ((normal_activity - current_activity) / normal_activity) * 100
        
        alert = HealthAlert(
            animal_id=animal_id,
            alert_type="reduced_activity",
            priority=AlertPriority.MEDIUM,
            description=f"Aktivite %{reduction:.1f} azalmış",
            metrics={
                "current_activity": current_activity,
                "normal_activity": normal_activity,
                "reduction_percent": reduction
            }
        )
        return await self.send_health_alert(alert)
        
    async def alert_abnormal_eating(
        self,
        animal_id: str,
        eating_duration: float,
        normal_duration: float
    ):
        """Anormal yeme davranışı uyarısı"""
        deviation = abs(eating_duration - normal_duration) / normal_duration * 100
        
        alert = HealthAlert(
            animal_id=animal_id,
            alert_type="abnormal_eating",
            priority=AlertPriority.MEDIUM,
            description=f"Yeme süresi normalden %{deviation:.1f} farklı",
            metrics={
                "eating_duration": eating_duration,
                "normal_duration": normal_duration,
                "deviation_percent": deviation
            }
        )
        return await self.send_health_alert(alert)
