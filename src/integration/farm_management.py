"""
Farm Management Integration - Çiftlik Yönetim Sistemi Entegrasyonu
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class FarmConfig:
    """Çiftlik yönetim sistemi konfigürasyonu"""
    base_url: str
    api_key: str = ""
    farm_id: str = ""
    timeout: int = 30
    sync_interval: int = 300  # 5 dakika


@dataclass
class AnimalData:
    """Çiftlik sisteminden alınan hayvan verisi"""
    external_id: str
    name: str
    species: str
    breed: str = ""
    birth_date: datetime = None
    gender: str = ""
    weight: float = 0.0
    group_id: str = ""
    location: str = ""
    metadata: Dict = None


class FarmManagementIntegration:
    """Çiftlik yönetim sistemi entegrasyonu"""
    
    def __init__(self, config: FarmConfig):
        self.config = config
        self._last_sync: datetime = None
        self._animals_cache: Dict[str, AnimalData] = {}
        
    def _get_headers(self) -> Dict[str, str]:
        """İstek header'ları"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Farm-ID": self.config.farm_id
        }
        
    async def get_all_animals(self) -> List[AnimalData]:
        """Tüm hayvanları çek"""
        if not HTTPX_AVAILABLE:
            logger.warning("httpx yüklü değil")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.base_url}/animals",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                animals = []
                for item in response.json():
                    animals.append(AnimalData(
                        external_id=item.get('id', ''),
                        name=item.get('name', ''),
                        species=item.get('species', ''),
                        breed=item.get('breed', ''),
                        birth_date=datetime.fromisoformat(item['birth_date']) if item.get('birth_date') else None,
                        gender=item.get('gender', ''),
                        weight=item.get('weight', 0.0),
                        group_id=item.get('group_id', ''),
                        location=item.get('location', ''),
                        metadata=item.get('metadata', {})
                    ))
                    
                return animals
                
        except Exception as e:
            logger.error(f"Hayvan listesi alınamadı: {e}")
            return []
            
    async def get_animal(self, external_id: str) -> Optional[AnimalData]:
        """Tek hayvan bilgisi al"""
        if not HTTPX_AVAILABLE:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.base_url}/animals/{external_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                item = response.json()
                return AnimalData(
                    external_id=item.get('id', ''),
                    name=item.get('name', ''),
                    species=item.get('species', ''),
                    breed=item.get('breed', ''),
                    birth_date=datetime.fromisoformat(item['birth_date']) if item.get('birth_date') else None,
                    gender=item.get('gender', ''),
                    weight=item.get('weight', 0.0),
                    group_id=item.get('group_id', ''),
                    location=item.get('location', ''),
                    metadata=item.get('metadata', {})
                )
                
        except Exception as e:
            logger.error(f"Hayvan bilgisi alınamadı: {e}")
            return None
            
    async def update_animal(self, external_id: str, data: Dict[str, Any]) -> bool:
        """Hayvan bilgisi güncelle"""
        if not HTTPX_AVAILABLE:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.patch(
                    f"{self.config.base_url}/animals/{external_id}",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Hayvan güncellenemedi: {e}")
            return False
            
    async def send_health_data(
        self,
        external_id: str,
        health_score: float,
        observations: List[str] = None
    ) -> bool:
        """Sağlık verisini gönder"""
        if not HTTPX_AVAILABLE:
            return False
            
        data = {
            "animal_id": external_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": health_score,
            "observations": observations or [],
            "source": "ai_tracking_system"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/health-records",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Sağlık verisi gönderilemedi: {e}")
            return False
            
    async def send_behavior_event(
        self,
        external_id: str,
        behavior_type: str,
        confidence: float,
        duration: float = None,
        metadata: Dict = None
    ) -> bool:
        """Davranış olayı gönder"""
        if not HTTPX_AVAILABLE:
            return False
            
        data = {
            "animal_id": external_id,
            "timestamp": datetime.utcnow().isoformat(),
            "behavior_type": behavior_type,
            "confidence": confidence,
            "duration_seconds": duration,
            "metadata": metadata or {},
            "source": "ai_tracking_system"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/behavior-events",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Davranış olayı gönderilemedi: {e}")
            return False
            
    async def sync_animals(self) -> int:
        """Hayvanları senkronize et"""
        animals = await self.get_all_animals()
        
        for animal in animals:
            self._animals_cache[animal.external_id] = animal
            
        self._last_sync = datetime.utcnow()
        logger.info(f"Senkronizasyon tamamlandı: {len(animals)} hayvan")
        
        return len(animals)
        
    def get_cached_animal(self, external_id: str) -> Optional[AnimalData]:
        """Önbellekten hayvan bilgisi al"""
        return self._animals_cache.get(external_id)
        
    def needs_sync(self) -> bool:
        """Senkronizasyon gerekli mi"""
        if self._last_sync is None:
            return True
            
        elapsed = (datetime.utcnow() - self._last_sync).total_seconds()
        return elapsed >= self.config.sync_interval
        
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
