"""
API Exporter - Harici API'lere veri aktarma
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import json
import os

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API konfigürasyonu"""
    base_url: str
    api_key: str = ""
    auth_type: str = "bearer"  # bearer, api_key, basic
    headers: Dict[str, str] = None
    timeout: int = 30
    retry_count: int = 3
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class ExportResult:
    """Export sonucu"""
    success: bool
    records_sent: int
    errors: List[str]
    response_data: Dict = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class APIExporter:
    """API veri aktarıcı"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self._client = None
        
    def _get_headers(self) -> Dict[str, str]:
        """İstek header'larını oluştur"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        headers.update(self.config.headers)
        
        if self.config.auth_type == "bearer" and self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.auth_type == "api_key" and self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
            
        return headers
        
    async def export_data(
        self,
        endpoint: str,
        data: List[Dict[str, Any]],
        method: str = "POST",
        batch_size: int = 100
    ) -> ExportResult:
        """Veriyi API'ye aktar"""
        if not HTTPX_AVAILABLE and not AIOHTTP_AVAILABLE:
            return ExportResult(
                success=False,
                records_sent=0,
                errors=["HTTP kütüphanesi yüklü değil (httpx veya aiohttp)"]
            )
            
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        total_sent = 0
        errors = []
        
        # Batch işleme
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            try:
                if HTTPX_AVAILABLE:
                    response = await self._send_httpx(url, method, batch, headers)
                else:
                    response = await self._send_aiohttp(url, method, batch, headers)
                    
                if response.get('success', True):
                    total_sent += len(batch)
                else:
                    errors.append(f"Batch {i//batch_size}: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                errors.append(f"Batch {i//batch_size}: {str(e)}")
                
        return ExportResult(
            success=len(errors) == 0,
            records_sent=total_sent,
            errors=errors
        )
        
    async def _send_httpx(
        self,
        url: str,
        method: str,
        data: Any,
        headers: Dict
    ) -> Dict:
        """httpx ile istek gönder"""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            for attempt in range(self.config.retry_count):
                try:
                    if method.upper() == "POST":
                        response = await client.post(url, json=data, headers=headers)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=data, headers=headers)
                    else:
                        response = await client.patch(url, json=data, headers=headers)
                        
                    response.raise_for_status()
                    return response.json() if response.text else {'success': True}
                    
                except Exception as e:
                    if attempt == self.config.retry_count - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                    
    async def _send_aiohttp(
        self,
        url: str,
        method: str,
        data: Any,
        headers: Dict
    ) -> Dict:
        """aiohttp ile istek gönder"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as session:
            for attempt in range(self.config.retry_count):
                try:
                    async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        headers=headers
                    ) as response:
                        response.raise_for_status()
                        text = await response.text()
                        return json.loads(text) if text else {'success': True}
                        
                except Exception as e:
                    if attempt == self.config.retry_count - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                    
    def export_sync(
        self,
        endpoint: str,
        data: List[Dict[str, Any]],
        method: str = "POST"
    ) -> ExportResult:
        """Senkron export (asyncio.run wrapper)"""
        return asyncio.run(self.export_data(endpoint, data, method))
        
    async def health_check(self) -> bool:
        """API sağlık kontrolü"""
        try:
            url = f"{self.config.base_url}/health"
            headers = self._get_headers()
            
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(url, headers=headers)
                    return response.status_code == 200
            elif AIOHTTP_AVAILABLE:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as session:
                    async with session.get(url, headers=headers) as response:
                        return response.status == 200
                        
        except Exception:
            return False
            
        return False


class FarmSoftwareExporter(APIExporter):
    """Çiftlik yazılımı entegrasyonu"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        self._field_mapping: Dict[str, str] = {}
        
    def set_field_mapping(self, mapping: Dict[str, str]):
        """Alan eşleştirmesi ayarla"""
        self._field_mapping = mapping
        
    def _transform_data(self, data: List[Dict]) -> List[Dict]:
        """Veriyi hedef formata dönüştür"""
        if not self._field_mapping:
            return data
            
        transformed = []
        for item in data:
            new_item = {}
            for source_field, target_field in self._field_mapping.items():
                if source_field in item:
                    new_item[target_field] = item[source_field]
            transformed.append(new_item)
            
        return transformed
        
    async def export_animals(self, animals: List[Dict]) -> ExportResult:
        """Hayvan verilerini aktar"""
        transformed = self._transform_data(animals)
        return await self.export_data("/animals", transformed)
        
    async def export_health_data(self, health_records: List[Dict]) -> ExportResult:
        """Sağlık verilerini aktar"""
        transformed = self._transform_data(health_records)
        return await self.export_data("/health", transformed)
        
    async def sync_animals(self) -> List[Dict]:
        """Hayvanları senkronize et (çek)"""
        if not HTTPX_AVAILABLE and not AIOHTTP_AVAILABLE:
            return []
            
        url = f"{self.config.base_url}/animals"
        headers = self._get_headers()
        
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.get(url, headers=headers)
                    return response.json()
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        return await response.json()
        except Exception as e:
            logger.error(f"Senkronizasyon hatası: {e}")
            return []
